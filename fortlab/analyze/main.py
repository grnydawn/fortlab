
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
        self.config['includefile'] = 'include.ini'
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


    def perform(self, mgr, args):

        from fortlab.analyze.kgsearch import f2003_search_unknowns
        import fortlab.analyze.kganalyze as kganalyze

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
                for uname, req in cs_stmt.unknowns.iteritems():
                    cs_stmt.resolve(req)
                    if not req.res_stmts:
                        raise kgutils.ProgramException('Resolution fail.')
            else:
                kgutils.logger.warn('Stmt does not have "unknowns" attribute: %s'%str(cs_stmt)) 

        # update state info of callsite and its upper blocks
        kganalyze.update_state_info(Config.parentblock['stmt'])

        # update state info of modules
        for modname, moddict in Config.modules.iteritems():
            modstmt = moddict['stmt']
            if modstmt != Config.topblock['stmt']:
                kganalyze.update_state_info(moddict['stmt'])

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
#                anc.geninfo = collections.OrderedDict()
#            if len(anc.content)>0 and isinstance(anc.content[-1], EndStatement) and \
#                not hasattr(anc.content[-1], 'geninfo'):
#                anc.content[-1].geninfo = collections.OrderedDict()
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

