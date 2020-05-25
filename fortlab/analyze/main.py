
import sys
import os

from collections import OrderedDict

from microapp import App
from fortlab.analyze import kgutils
from fortlab.analyze import kgparse
#from kgconfig import Config
from fortlab.analyze import statements



class FortranAnalyzer(App):

    _name_ = "analyze"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("callsitefile", metavar="path", help="callsite file path")
        self.add_argument("--import-source", metavar="srcpath", action="append",
                          help="load source file")
        self.add_argument("--compile-info", metavar="path", help="compiler flags")


        self.register_forward("data", help="ast object")

        # database
        self.config = {}

        # source file parameters
        self.config["source"] = OrderedDict()
        self.config['source'] = OrderedDict()
        self.config['source']['isfree'] = None
        self.config['source']['isstrict'] = None
        self.config['source']['alias'] = OrderedDict()
        self.config['source']['file'] = OrderedDict()
        self.config['source']['state'] = []

        # include parameters
        self.config['include'] = OrderedDict()
        self.config['include']['macro'] = OrderedDict()
        self.config['include']['path'] = []
        self.config['include']['type'] = OrderedDict()
        self.config['include']['compiler'] = OrderedDict()
        self.config['include']['import'] = OrderedDict()
        self.config['include']['file'] = OrderedDict()
        self.config['include']['opt'] = None

        # mpi parameters
        self.config['mpi'] = OrderedDict()
        self.config['mpi']['enabled'] = False
        self.config['mpi']['comm'] = None
        self.config['mpi']['logical'] = None
        self.config['mpi']['status_size'] = None
        self.config['mpi']['source'] = None
        self.config['mpi']['any_source'] = None
        self.config['mpi']['header'] = 'mpif.h'
        self.config['mpi']['use_stmts'] = []

        # external tool parameters
        self.config['bin'] = OrderedDict()
        self.config['bin']['pp'] = 'cpp'
        self.config['bin']['cpp_flags'] = '-w -traditional -P'

        self.config['modules'] = OrderedDict()
        self.config['srcfiles'] = OrderedDict()
        self.config['kernel'] = OrderedDict()
        self.config['kernel']['name'] = None
        self.config['callsite'] = OrderedDict()
        self.config['callsite']['stmts'] = []
        self.config['callsite']['filepath'] = ''
        self.config['callsite']['span'] = (-1, -1)
        self.config['callsite']['namepath'] = ''
#        self.config['callsite']['lineafter'] = -1
        self.config['parentblock'] = OrderedDict()
        self.config['parentblock']['stmt'] = None
        self.config['topblock'] = OrderedDict()
        self.config['topblock']['stmt'] = None
        self.config['topblock']['filepath'] = ''
        self.config['used_srcfiles'] = OrderedDict()
        self.config['kernel_driver'] = OrderedDict()
        self.config['kernel_driver']['name'] = 'kernel_driver'
        self.config['kernel_driver']['callsite_args'] = ['kgen_unit', 'kgen_measure', 'kgen_isverified', 'kgen_filepath']

        # search parameters
        self.config['search'] = OrderedDict()
        self.config['search']['skip_intrinsic'] = True
        self.config['search']['except'] = []
        self.config['search']['promote_exception'] = False

        # exclude parameters
        self.config['exclude'] = OrderedDict()


    def read_compile_info(self, cinfo, config):

        for key, value in cinfo.items():
            #if key in [ 'type', 'rename', 'state', 'extern' ]:
            if key in [ 'type', 'macro' ]:
                import pdb; pdb.set_trace()
                for option in Inc.options(section):
                    self.config["include"][key][option] = Inc.get(section, option).strip()
            elif key=='import':
                import pdb; pdb.set_trace()
                for option in Inc.options(section):
                    self.config["include"][key][option] = Inc.get(section, option).strip()
    #                subflags = OrderedDict()
    #                for subf in Inc.get(section, option).split(','):
    #                    subflags[subf.strip()] = None
    #                self.config["include"][key][option] = subflags
            elif key=='include':
                import pdb; pdb.set_trace()
                for option in Inc.options(section):
                    self.config["include"]['path'].append(option.strip())
            elif key=='compiler':
                import pdb; pdb.set_trace()
                for option in Inc.options(section):
                    self.config["include"][key][option] = Inc.get(section, option).strip()
            else:
                realpath = os.path.realpath(key)

                if not os.path.exists(realpath):
                    print("WARNING: '%s' does not exist. It may cause failure of KGen analysis." % realpath)

                if realpath not in self.config["include"]['file']:
                    self.config["include"]['file'][realpath] = OrderedDict()
                    self.config["include"]['file'][realpath]['path'] = ['.']
                    self.config["include"]['file'][realpath]['compiler'] = None
                    self.config["include"]['file'][realpath]['compiler_options'] = None
                    self.config["include"]['file'][realpath]['macro'] = OrderedDict()

                for infotype, infovalue in value.items():
                    if infotype=='include':
                        self.config["include"]['file'][realpath]['path'].extend(infovalue)
                    elif infotype in [ 'compiler', 'options', "openmp" ]:
                        self.config["include"]['file'][realpath][infotype] = infovalue
                    else:
                        for mkey, mvalue in infovalue:
                            self.config["include"]['file'][realpath]['macro'][mkey] = mvalue

        # dupulicate paths per each alias
        newpath = set()
        for path in self.config['include']['path']:
            newpath.add(path)
            for p1, p2 in self.config['source']['alias'].items():
                if path.startswith(p1):
                    newpath.add(p2+path[len(p1):])
                elif path.startswith(p2):
                    newpath.add(p1+path[len(p2):])
        self.config['include']['path'] = list(newpath)

        newfile =  OrderedDict()
        for path, value in self.config['include']['file'].items():
            newfile[path] = value
            for p1, p2 in self.config['source']['alias'].items():
                if path.startswith(p1):
                    newpath = p2+path[len(p1):]
                    newfile[newpath] = copy.deepcopy(value)
                elif path.startswith(p2):
                    newpath = p1+path[len(p2):]
                    newfile[newpath] = copy.deepcopy(value)
        self.config['include']['file'] = newfile

        for path, value in self.config['include']['file'].items():
            if "path" in value:
                newpath = set()
                for path in value['path']:
                    newpath.add(path)
                    for p1, p2 in self.config['source']['alias'].items():
                        if path.startswith(p1):
                            newpath.add(p2+path[len(p1):])
                        elif path.startswith(p2):
                            newpath.add(p1+path[len(p2):])
                value['path'] = list(newpath)



    def perform(self, args):

        from fortlab.analyze.kgsearch import f2003_search_unknowns
        import fortlab.analyze.kganalyze as kganalyze

        if args.compile_info:
            cinfo = args.compile_info["_"]

            if isinstance(cinfo, str):
                # read json file
                # cinfo = 
                import pdb; pdb.set_trace()

            if isinstance(cinfo, dict):
                self.read_compile_info(cinfo, self.config)

            else:
                print("Wrong compile-info type: %s" % type(cinfo), file=sys.stderr)
                sys.exit(-1)


        # preprocess if required
        if args.import_source:
            for iarg in args.import_source:
                kgparse.SrcFile(iarg["_"], self.config)

        # read source file that contains callsite stmt
        cs_file = kgparse.SrcFile(args.callsitefile["_"], self.config)
        if len(self.config["callsite"]['stmts'])==0:
            raise kgutils.UserException('Can not find callsite')

        # add geninfo to ancestors
        ancs = self.config["callsite"]['stmts'][0].ancestors()

        self.add_geninfo_ancestors(self.config["callsite"]['stmts'][0])

        # populate parent block parameters
        self.config["parentblock"]['stmt'] = ancs[-1]

        # populate top block parameters
        self.config["topblock"]['stmt'] = ancs[0]
        self.config["topblock"]['filepath'] = os.path.realpath(self.config["topblock"]['stmt'].reader.id)

        # resolve
        for cs_stmt in self.config["callsite"]['stmts']:
            #resolve cs_stmt
            f2003_search_unknowns(cs_stmt, cs_stmt.f2003, self.config)
            if hasattr(cs_stmt, 'unknowns'):
                for uname, req in cs_stmt.unknowns.items():
                    cs_stmt.resolve(req, self.config)
                    if not req.res_stmts:
                        raise kgutils.ProgramException('Resolution fail.')
            else:
                kgutils.logger.warn('Stmt does not have "unknowns" attribute: %s'%str(cs_stmt)) 

        # update state info of callsite and its upper blocks
        kganalyze.update_state_info(self.config["parentblock"]['stmt'], self.config)

        # update state info of modules
        for modname, moddict in self.config["modules"].items():
            modstmt = moddict['stmt']
            if modstmt != self.config["topblock"]['stmt']:
                kganalyze.update_state_info(moddict['stmt'], self.config)

        import pdb; pdb.set_trace()
#
#    def add_geninfo_ancestors(self, stmt):
#        from block_statements import EndStatement
#
#        ancs = stmt.ancestors()
#
#        prevstmt = stmt
#        prevname = None
#
#        for anc in reversed(ancs):
#            if not hasattr(anc, 'geninfo'):
#                anc.geninfo = OrderedDict()
#            if len(anc.content)>0 and isinstance(anc.content[-1], EndStatement) and \
#                not hasattr(anc.content[-1], 'geninfo'):
#                anc.content[-1].geninfo = OrderedDict()
#
#            if prevname:
#                dummy_req = kgparse.ResState(kgparse.KGGenType.STATE_IN, kgutils.KGName(prevname), None, [anc])
#                dummy_req.res_stmts = [ prevstmt ]
#                anc.check_spec_stmts(dummy_req.uname, dummy_req)
#
#            if hasattr(anc, 'name'): prevname = anc.name
#            else: prevname = None
#            prevstmt = anc
#
    def add_geninfo_ancestors(self, stmt):
        from fortlab.analyze.block_statements import EndStatement

        ancs = stmt.ancestors()

        prevstmt = stmt
        prevname = None

        for anc in reversed(ancs):
            if not hasattr(anc, 'geninfo'):
                anc.geninfo = OrderedDict()
            if len(anc.content)>0 and isinstance(anc.content[-1], EndStatement) and \
                not hasattr(anc.content[-1], 'geninfo'):
                anc.content[-1].geninfo = OrderedDict()

            if prevname:
                dummy_req = kgparse.ResState(kgparse.KGGenType.STATE_IN, kgutils.KGName(prevname), None, [anc])
                dummy_req.res_stmts = [ prevstmt ]
                anc.check_spec_stmts(dummy_req.uname, dummy_req)

            if hasattr(anc, 'name'): prevname = anc.name
            else: prevname = None
            prevstmt = anc

