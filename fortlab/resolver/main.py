
import sys
import os

from collections import OrderedDict

from microapp import App
from fortlab.kgutils import UserException, ProgramException, logger, KGName
from fortlab.resolver import kgparse
#from kgconfig import Config
from fortlab.resolver import statements



class FortranNameResolver(App):

    _name_ = "resolve"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("callsitefile", metavar="path", help="callsite file path")
        self.add_argument("--import-source", metavar="srcpath", action="append",
                          help="load source file")
        self.add_argument("--compile-info", metavar="path", help="compiler flags")


        #self.register_shared("config", help="config object")
        #self.register_shared("trees", help="ast object")
        self.register_forward("analysis", help="analysis object")

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


#        # model parameters
#        self.config['modelfile'] = 'model.ini'
#        self.config['model'] = OrderedDict()
#        self.config['model']['reuse_rawdata'] = True
#        self.config['model']['types'] = OrderedDict()
#        self.config['model']['types']['code'] = OrderedDict()
#        self.config['model']['types']['code']['id'] = '0'
#        self.config['model']['types']['code']['name'] = 'code'
#        self.config['model']['types']['code']['percentage'] = 99.9
#        self.config['model']['types']['code']['filter'] = None
#        self.config['model']['types']['code']['ndata'] = 20
#        self.config['model']['types']['code']['enabled'] = False
#        self.config['model']['types']['etime'] = OrderedDict()
#        self.config['model']['types']['etime']['id'] = '1'
#        self.config['model']['types']['etime']['name'] = 'etime'
#        self.config['model']['types']['etime']['nbins'] = 5
#        self.config['model']['types']['etime']['ndata'] = 20
#        self.config['model']['types']['etime']['minval'] = None
#        self.config['model']['types']['etime']['maxval'] = None
#        self.config['model']['types']['etime']['timer'] = None
#        self.config['model']['types']['etime']['enabled'] = True
#        self.config['model']['types']['papi'] = OrderedDict()
#        self.config['model']['types']['papi']['id'] = '2'
#        self.config['model']['types']['papi']['name'] = 'papi'
#        self.config['model']['types']['papi']['nbins'] = 5
#        self.config['model']['types']['papi']['ndata'] = 20
#        self.config['model']['types']['papi']['minval'] = None
#        self.config['model']['types']['papi']['maxval'] = None
#        self.config['model']['types']['papi']['header'] = None
#        self.config['model']['types']['papi']['event'] = 'PAPI_TOT_INS'
#        self.config['model']['types']['papi']['static'] = None
#        self.config['model']['types']['papi']['dynamic'] = None
#        self.config['model']['types']['papi']['enabled'] = False

        # make prerun parameters
        self.config['prerun'] = OrderedDict()
        self.config['prerun']['kernel_build'] = ''
        self.config['prerun']['kernel_run'] = ''
        self.config['prerun']['build'] = ''
        self.config['prerun']['run'] = ''

        # make rebuild parameters
        self.config['rebuild'] = OrderedDict()

        # make cmd parameters
        self.config['cmd_clean'] = OrderedDict()
        self.config['cmd_clean']['cmds'] = ''
        self.config['cmd_build'] = OrderedDict()
        self.config['cmd_build']['cmds'] = ''
        self.config['cmd_run'] = OrderedDict()
        self.config['cmd_run']['cmds'] = ''
        self.config['state_switch'] = OrderedDict()
        self.config['state_switch']['type'] = 'replace'
        self.config['state_switch']['directory'] = ''
        self.config['state_switch']['clean'] = ''

        # exclude parameters
        self.config['exclude'] = OrderedDict()

        # make rebuild parameters
        self.config['path'] = OrderedDict()

        
        # openmp parameters
        self.config['openmp'] = OrderedDict()
        self.config['openmp']['enabled'] = False
        self.config['openmp']['critical'] = True
        self.config['openmp']['maxnum_threads'] = 102

        # Fortran parameters
        self.config['fort'] = OrderedDict()
        self.config['fort']['maxlinelen'] = 132

        # program units
        self.config['program_units'] = OrderedDict()


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

        from fortlab.resolver.kgsearch import f2003_search_unknowns
        import fortlab.resolver.kganalyze as kganalyze

        if args.compile_info:
            cinfo = args.compile_info["_"]

            if isinstance(cinfo, str):
                # read json file
                # cinfo = 
                import pdb; pdb.set_trace()

            if isinstance(cinfo, dict):
                self.read_compile_info(cinfo, self.config)

            else:
                print("Wrong compile-info type: %s" % type(cinfo))
                sys.exit(-1)

        # preprocess if required
        if args.import_source:
            for iarg in args.import_source:
                kgparse.SrcFile(iarg["_"], self.config)


        callsite = args.callsitefile["_"].split(':', 1)
        if not os.path.isfile(callsite[0]):
            raise UserException('ERROR: callsite file, "%s" can not be found.' % callsite[0])

        # set callsite filepath
        self.config["callsite"]['filepath'] = os.path.realpath(callsite[0])

        # set namepath if exists in command line argument
        if len(callsite)==2:
            self.config["callsite"]['namepath'] = callsite[1].lower()

        elif len(callsite)>2:
            raise UserException('ERROR: Unrecognized call-site information(Syntax -> filepath[:subprogramname]): %s'%str(callsite))

        # read source file that contains callsite stmt
        cs_file = kgparse.SrcFile(self.config["callsite"]["filepath"], self.config)
        if len(self.config["callsite"]['stmts'])==0:
            raise UserException('Can not find callsite')

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
                        raise ProgramException('Resolution fail.')
            else:
                logger.warn('Stmt does not have "unknowns" attribute: %s'%str(cs_stmt)) 

        # update state info of callsite and its upper blocks
        kganalyze.update_state_info(self.config["parentblock"]['stmt'], self.config)

        # update state info of modules
        for modname, moddict in self.config["modules"].items():
            modstmt = moddict['stmt']
            if modstmt != self.config["topblock"]['stmt']:
                kganalyze.update_state_info(moddict['stmt'], self.config)

        self.add_forward(analysis=self.config)

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
        from fortlab.resolver.block_statements import EndStatement

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
                dummy_req = kgparse.ResState(kgparse.KGGenType.STATE_IN, KGName(prevname), None, [anc])
                dummy_req.res_stmts = [ prevstmt ]
                anc.check_spec_stmts(dummy_req.uname, dummy_req)

            if hasattr(anc, 'name'): prevname = anc.name
            else: prevname = None
            prevstmt = anc

