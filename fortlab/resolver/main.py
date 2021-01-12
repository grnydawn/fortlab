
import sys, os, json, re

from collections import OrderedDict

from microapp import App
from fortlab.kgutils import (UserException, ProgramException, logger, KGName, run_shcmd,
                             KgenConfigParser, traverse)
from fortlab.resolver import kgparse
#from kgconfig import Config
from fortlab.resolver import statements

SRCROOT = os.path.dirname(os.path.realpath(__file__))
KGEN_MACHINE = '%s/../machines'%SRCROOT

def get_MPI_PARAM(node, bag, depth):
    from fortlab.resolver.Fortran2003 import Specification_Part, Type_Declaration_Stmt, Entity_Decl, Parameter_Stmt, Named_Constant_Def, \
        NoMatchError, Module_Stmt, Program_Stmt, Named_Constant_Def_List

    if isinstance(node, Type_Declaration_Stmt):
        if isinstance(node.items[2], Entity_Decl) and node.items[2].items[0].string.upper()==bag['key']:
            pass
    elif isinstance(node, Parameter_Stmt):
        if isinstance(node.items[1], Named_Constant_Def) and node.items[1].items[0].string.upper()==bag['key']:
            bag[bag['key']].append(str(node.items[1].items[1]).replace(' ', ''))
        elif isinstance(node.items[1], Named_Constant_Def_List):
            for item in node.items[1].items:
                if isinstance(item, Named_Constant_Def) and item.items[0].string.upper()==bag['key']:
                    bag[bag['key']].append(str(item.items[1]).replace(' ', ''))


class FortranNameResolver(App):

    _name_ = "resolve"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("callsitefile", metavar="path", help="callsite file path")
        self.add_argument("--import-source", metavar="srcpath", action="append",
                          help="load source file")
        self.add_argument("--compile-info", metavar="path", help="compiler flags")
        self.add_argument("--keep", metavar="analysis", help="keep analysis")

        ###############################################################
        # Add common options
        ###############################################################
        self.add_argument("-i", "--include-ini", dest="include_ini", action='store', type=str, help="information used for analysis")
        self.add_argument("-e", "--exclude-ini", dest="exclude_ini", action='store', type=str, help="information excluded for analysis")
        self.add_argument("-I", dest="include", action='append', type=str, help="include path information used for analysis")
        self.add_argument("-D", dest="macro", action='append', type=str, help="macro information used for analysis")
        self.add_argument("--outdir", dest="outdir", action='store', type=str, help="path to create outputs")
        self.add_argument("--source", dest="source", action='append', type=str, help="Setting source file related properties")
        self.add_argument("--intrinsic", dest="intrinsic", action='append', type=str, help="Specifying resolution for intrinsic procedures during searching")
        self.add_argument("--machinefile", dest="machinefile", action='store', type=str, help="Specifying machinefile")
        self.add_argument("--debug", dest="debug", action='append', type=str)
        self.add_argument("--logging", dest="logging", action='append', type=str)

        ###############################################################
        # Add extraction options
        ###############################################################

        self.add_argument("--invocation", dest="invocation", action='append', type=str, help="(process, thread, invocation) pairs of kernel for data collection")
        self.add_argument("--data", dest="data", action='append', type=str, help="Control state data generation")
        self.add_argument("--openmp", dest="openmp", action='append', type=str, help="Specifying OpenMP options")
        self.add_argument("--mpi", dest="mpi", action='append', type=str, help="MPI information for data collection")
        self.add_argument("--timing", dest="timing", action='store', type=str, help="Timing measurement information")
        self.add_argument("--prerun", dest="prerun", action='append', type=str, help="prerun commands")
        self.add_argument("--rebuild", dest="rebuild", action='append', type=str, help="rebuild controls")
        self.add_argument("--state-switch", dest="state_switch", action='append', type=str, help="Specifying how to switch orignal sources with instrumented ones.")
        self.add_argument("--kernel-option", dest="kernel_option", action='append', type=str, help="Specifying kernel compiler and linker options")
        self.add_argument("--check", dest="check", action='append', type=str, help="Kernel correctness check information")
        self.add_argument("--verbose", dest="verbose_level", action='store', type='int', help="Set the verbose level for verification output")
        self.add_argument("--add-mpi-frame", dest="add_mpi_frame", action='store', type=str, help="Add MPI frame codes in kernel_driver")
        self.add_argument("--add-cache-pollution", dest="add_cache_pollution", action='store', type=str, help="Add cache pollution frame codes in kernel_driver")

        self.add_argument("--repr-etime", dest="repr_etime", action='append', type=str, help="Specifying elapsedtime representativeness feature flags")
        self.add_argument("--repr-papi", dest="repr_papi", action='append', type=str, help="Specifying papi counter representativeness feature flags")
        self.add_argument("--repr-code", dest="repr_code", action='append', type=str, help="Specifying code coverage representativeness feature flags")

        #self.register_shared("config", help="config object")
        #self.register_shared("trees", help="ast object")
        self.register_forward("analysis", help="analysis object")

        # database
        self.config = {}

        # KGEN version
        self.config['kgen'] = OrderedDict()
        self.config['kgen']['version'] = [ 0, 9, '0' ]

        # machine parameters
        self.config['machine'] = OrderedDict()
        self.config['machine']['inc'] = None
        self.config['machine']['general'] = OrderedDict()
        self.config['machine']['general']['name'] = 'Generic Machine'
        self.config['machine']['general']['id'] = 'generic'
        self.config['machine']['compiler'] = OrderedDict()
        self.config['machine']['compiler']['gnu'] = ''
        self.config['machine']['compiler']['intel'] = ''
        self.config['machine']['compiler']['pgi'] = ''
        self.config['machine']['compiler']['cray'] = ''
        self.config['machine']['variable'] = OrderedDict()
        self.config['machine']['variable']['work_directory'] = os.path.expandvars('${HOME}/kgen_workspace')

        # logging parameters
        self.config['logging'] = OrderedDict()
        self.config['logging']['select'] = OrderedDict()

        # path parameters
        self.config['cwd'] = os.getcwd()
        self.config['path'] = OrderedDict()
        self.config['path']['outdir'] = '.'
        self.config['path']['state'] = 'state'
        self.config['path']['kernel'] = 'kernel'
        self.config['path']['model'] = 'model'
        self.config['path']['coverage'] = 'coverage'
        self.config['path']['etime'] = 'elapsedtime'
        self.config['path']['papi'] = 'papi'

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

        # make kernel parameters
        self.config['kernel_option'] = OrderedDict()
        self.config['kernel_option']['FC'] =  ''
        self.config['kernel_option']['FC_FLAGS'] = ''
        self.config['kernel_option']['compiler'] = OrderedDict()
        self.config['kernel_option']['compiler']['add'] = []
        self.config['kernel_option']['compiler']['remove'] = []
        self.config['kernel_option']['linker'] = OrderedDict()
        self.config['kernel_option']['linker']['add'] = []

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

        # debugging parameters
        self.config['debug'] = OrderedDict()
        self.config['debug']['printvar'] = []

        # invocation parameters
        self.config['invocation'] = OrderedDict()
        self.config['invocation']['triples'] = []

        # data parameters
        self.config['data'] = OrderedDict()
        self.config['data']['condition'] = []
        self.config['data']['maxnuminvokes'] = None

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

        # add mpi frame code in kernel driver
        self.config['add_mpi_frame'] = OrderedDict()
        self.config['add_mpi_frame']['enabled'] = False
        self.config['add_mpi_frame']['np'] = '2'
        self.config['add_mpi_frame']['mpifc'] = 'mpif90'
        self.config['add_mpi_frame']['mpirun'] = 'mpirun'

        # add mpi frame code in kernel driver
        self.config['add_cache_pollution'] = OrderedDict()
        self.config['add_cache_pollution']['enabled'] = False
        self.config['add_cache_pollution']['size'] = 0

        # plugin parameters
        #self.config['plugin'] = OrderedDict()
        #self.config['plugin']['priority'] = OrderedDict()

        self.config['plugindb'] = OrderedDict()

        # verification parameters
        self.config['verify'] = OrderedDict()
        self.config['verify']['tolerance'] = '1.D-14'
        self.config['verify']['minval'] = '1.D-14'
        self.config['verify']['verboselevel'] = '1'


        # kernel correctness check parameters
        self.config['check'] = OrderedDict()
        #self.config['check']['pert_invar'] = ['*']
        self.config['check']['pert_invar'] = []
        self.config['check']['pert_lim'] = '1.0E-15'

    def read_compile_info(self, cinfo, config):

        for key, value in cinfo.items():
            #if key in [ 'type', 'rename', 'state', 'extern' ]:
            if key in [ 'type', 'macro' ]:
                for option in Inc.options(section):
                    self.config["include"][key][option] = Inc.get(section, option).strip()
            elif key=='import':
                for option in Inc.options(section):
                    self.config["include"][key][option] = Inc.get(section, option).strip()
    #                subflags = OrderedDict()
    #                for subf in Inc.get(section, option).split(','):
    #                    subflags[subf.strip()] = None
    #                self.config["include"][key][option] = subflags
            elif key=='include':
                for option in Inc.options(section):
                    self.config["include"]['path'].append(option.strip())
            elif key=='compiler':
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
                    self.config["include"]['file'][realpath]['srcbackup'] = []

                for infotype, infovalue in value.items():
                    if infotype=='include':
                        self.config["include"]['file'][realpath]['path'].extend(infovalue)
                    elif infotype in [ 'compiler', 'options', "openmp", "srcbackup" ]:
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
                with open(cinfo) as f:
                    self.read_compile_info(json.load(f), self.config)

            elif isinstance(cinfo, dict):
                self.read_compile_info(cinfo, self.config)

            else:
                print("Wrong compile-info type: %s" % type(cinfo))
                sys.exit(-1)

        # process default flags
        self._process_default_flags(args)

        # process extraction flags
        self._process_extract_flags(args)

#        # process representativeness flags
#        self._process_repr_flags(args)

        if self.config['mpi']['enabled']:
            self.collect_mpi_params()

        # preprocess if required
        if args.import_source:
            for iarg in args.import_source:
                iarg = iarg["_"]
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

#        def jsondefault(o):
#            with open("test.json", "w") as f:
#                ll = []
#                import pdb; pdb.set_trace()
#                for i, c in enumerate(o.content):
#                    print("TTTT", i)
#                    ll.append(json.dump(f, c))

        if args.keep:
            print("save option is not supported yet.")
#            output_file = open(args.save["_"], 'w')
#            json.dump(self.config, output_file, indent=4, separators=(',', ': '), default=jsondefault)
#            output_file.write('\n')
#            output_file.close()

            #opts = ["@analysis", "-o", args.["_"]]
            #ret, fwds = self.run_subapp("dict2json", opts, forward={"analysis": self.config})
            #assert ret == 0, "dict2json returned non-zero code during analysis saving."

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

    def collect_mpi_params(self):
        #from parser.api import parse, walk
        from fortlab.resolver import api

        if self.config['mpi']['enabled']:
            # get path of mpif.h
            mpifpath = ''
            if os.path.isabs(self.config['mpi']['header']):
                if os.path.exists(self.config['mpi']['header']):
                    mpifpath = self.config['mpi']['header']
                else:
                    raise UserException('Can not find %s'%self.config['mpi']['header'])
            else:
                for p in self.config['include']['path']:
                    fp = os.path.join(p, self.config['mpi']['header'])
                    if os.path.exists(fp):
                        mpifpath = fp
                        break
                if not mpifpath:
                    for incpath, incdict in self.config['include']['file'].items():
                        for p in incdict['path']:
                            fp = os.path.join(p, self.config['mpi']['header'])
                            if os.path.exists(fp):
                                mpifpath = fp
                                break
                        if mpifpath: break

            # collect required information
            if mpifpath:
                try:
                    with open(mpifpath, 'r') as f:
                        filelines = f.read().split('\n')
                        lines = '\n'.join(handle_include(os.path.dirname(mpifpath), filelines, self.config))
                        #reader = FortranStringReader(lines)
                    tree = api.parse(lines, ignore_comments=True, analyze=False, isfree=True, isstrict=False, include_dirs=None, source_only=None )
                    for stmt, depth in api.walk(tree, -1):
                        stmt.parse_f2003()

                    #import pdb; pdb.set_trace()
                    #spec = Specification_Part(reader)
                    bag = {}
                    config_name_mapping = [
                        ('comm', 'MPI_COMM_WORLD'),
                        ('logical', 'MPI_LOGICAL'),
                        ('status_size', 'MPI_STATUS_SIZE'),
                        ('any_source', 'MPI_ANY_SOURCE'),
                        ('source', 'MPI_SOURCE'),
                        ]
                    for config_key, name in config_name_mapping:
                        if config_key not in self.config['mpi'] or self.config['mpi'][config_key] is None:
                            for stmt, depth in api.walk(tree, -1):
                                bag['key'] = name
                                bag[name] = []
                                if hasattr(stmt, 'f2003'):
                                    traverse(stmt.f2003, get_MPI_PARAM, bag, subnode='content')
                                    if len(bag[name]) > 0:
                                        self.config['mpi'][config_key] = bag[name][-1]
                                        break

                    for config_key, name in config_name_mapping:
                        if config_key not in self.config['mpi'] or self.config['mpi'][config_key] is None:
                            raise UserException('Can not find {name} in mpif.h'.format(name=name))

                except UserException:
                    raise  # Reraise this exception rather than catching it below
                except Exception as e:
                    raise UserException('Error occurred during reading %s.'%mpifpath)
            else:
                raise UserException('Can not find mpif.h. Please provide a path to the file')


    def _process_default_flags(self, opts):

        # check if exists fpp or cpp
        output = ''
        try:
            out, err, retcode = run_shcmd('which cpp', show_error_msg=False)
            output = out.strip()
        except Exception as e: pass
        if output.endswith(b'cpp'):
            self.config["bin"]['pp'] = str(output, "utf-8")
        else:
            print('ERROR: cpp is not found.')
            sys.exit(-1)

        # parsing intrinsic skip option
        if opts.intrinsic:
            subflags = []
            for line in opts.intrinsic:
                line = line["_"]
                subflags.extend(line.split(','))

            for subf in subflags:
                if subf and subf.find('=')>0:
                    key, value = subf.split('=')
                    if key=='except':
                        self.config['search']['except'].extend(value.split(';'))
                    elif key=='add_intrinsic':
                        Intrinsic_Procedures.extend([name.lower() for name in value.split(';')])
                    else:
                        raise UserException('Unknown intrinsic sub option: %s' % subf)
                else:
                    if subf=='skip':
                        self.config['search']['skip_intrinsic'] = True
                    elif subf=='noskip':
                        self.config['search']['skip_intrinsic'] = False
                    else:
                        raise UserException('Unknown intrinsic option(s) in %s' % subf)

        # parsing include parameters
        if opts.include:
            for inc in opts.include:
                inc = inc["_"]
                inc_eq = inc.split('=')
                if len(inc_eq)==1:
                    for inc_colon in inc_eq[0].split(':'):
                        self.config['include']['path'].append(inc_colon)
                if len(inc_eq)==1:
                    for inc_colon in inc_eq[0].split(':'):
                        self.config['include']['path'].append(inc_colon)
                elif len(inc_eq)==2:
                    # TODO: support path for each file
                    pass
                else: raise UserException('Wrong format include: %s'%inc)

        if opts.include_ini:
            self.config['include']['opt'] = opts.include_ini["_"]

        if opts.exclude_ini:
            self.process_exclude_option(opts.exclude_ini["_"], self.config['exclude'])

        # parsing macro parameters
        if opts.macro:
            for line in opts.macro:
                line = line["_"]
                for macro in line.split(','):
                    macro_eq = macro.split('=')
                    if len(macro_eq)==1:
                        self.config['include']['macro'][macro_eq[0]] = None
                    elif len(macro_eq)==2:
                        self.config['include']['macro'][macro_eq[0]] = macro_eq[1]
                    else: raise UserException('Wrong format include: %s'%inc)

        files = None
        if opts.source:

            isfree = None
            isstrict = None

            for line in opts.source:
                line = line["_"]
                flags = OrderedDict()
                for subflag in line.split(','):
                    if subflag.find('=')>0:
                        key, value = subflag.split('=')
                        if key=='format':
                            if value == 'free':
                                isfree = True
                            elif value == 'fixed':
                                isfree = False
                            self.config['source']['isfree'] = isfree
                        elif key=='strict':
                            if value == 'yes':
                                isstrict = True
                            elif value == 'no':
                                isstrict = False
                            self.config['source']['isstrict'] = isstrict

            for line in opts.source["_"]:
                flags = OrderedDict()
                for subflag in line.split(','):
                    if subflag.find('=')>0:
                        key, value = subflag.split('=')
                        if key=='file':
                            flags[key] = value.split(':')
                        elif key=='alias':
                            p1, p2 = value.split(':')
                            if p1.endswith('/'): p1 = p1[:-1]
                            if p2.endswith('/'): p2 = p2[:-1]
                            self.config['source']['alias'][p1] = p2
                        elif key=='state':
                            for path in value.split(':'):
                                if os.path.exists(path):
                                    realpath = os.path.realpath(path)
                                    self.config['source'][key].append(realpath)
                                else:
                                    raise UserException('%s does not exist.'%os.path.realpath(path))
                        else:
                            flags[key] = value
                    else:
                        flags[subflag] = None

                isfree = None
                isstrict = None

            for line in opts.source["_"]:
                flags = OrderedDict()
                for subflag in line.split(','):
                    if subflag.find('=')>0:
                        key, value = subflag.split('=')
                        if key=='file':
                            flags[key] = value.split(':')
                        elif key=='alias':
                            p1, p2 = value.split(':')
                            if p1.endswith('/'): p1 = p1[:-1]
                            if p2.endswith('/'): p2 = p2[:-1]
                            self.config['source']['alias'][p1] = p2
                        elif key=='state':
                            for path in value.split(':'):
                                if os.path.exists(path):
                                    realpath = os.path.realpath(path)
                                    self.config['source'][key].append(realpath)
                                else:
                                    raise UserException('%s does not exist.'%os.path.realpath(path))
                        else:
                            flags[key] = value
                    else:
                        flags[subflag] = None

                isfree = None
                isstrict = None


        # parsing debugging options
        # syntax: a.b.c=d,e,f
        if opts.debug:
            for dbg in opts.debug:
                dbg = dbg["_"]
                param_path, value = dbg.split('=')
                param_split = param_path.lower().split('.')
                value_split = value.lower().split(',')
                curdict = self.config['debug']
                for param in param_split[:-1]:
                    curdict = curdict[param]
                exec('curdict[param_split[-1]] = value_split')

        # parsing logging options
        if opts.logging:
            for log in opts.logging:
                log = log["_"]
                param_path, value = log.split('=')
                param_split = param_path.lower().split('.')
                value_split = value.lower().split(',')
                curdict = self.config['logging']
                for param in param_split[:-1]:
                    curdict = curdict[param]
                exec('curdict[param_split[-1]] = value_split')

        if opts.outdir:
            self.config['path']['outdir'] = opts.outdir["_"]

        if opts.machinefile:
            if os.path.exists(opts.machinefile["_"]):
                self.config['machine']['inc'] = KgenConfigParser(allow_no_value=True)
                inc.read(opts.machinefile["_"])
            else:
                print('WARNING: "%s" machine file does not exist.'%opts.machinefile["_"])
        else:
            self.config['machine']['inc'] = self.find_machine()

        if self.config['machine']['inc']:
            self.read_machinefile(self.config['machine'], self.config['prerun'])

        if not os.path.exists(self.config['machine']['variable']['work_directory']):
            os.makedirs(self.config['machine']['variable']['work_directory'])

        # create state directories and change working directory
        if not os.path.exists(self.config['path']['outdir']):
            os.makedirs(self.config['path']['outdir'])
        os.chdir(self.config['path']['outdir'])

    def _process_extract_flags(self, opts):

        # parsing invocation parameters
        if opts.invocation:
            for line in opts.invocation:
                line = line["_"]
                for invocation in line.split(','):
                    t = invocation.split(':')
                    if len(t) != 3:
                        raise UserException('Wrong invocation syntax: expected <mpi ranks>:<openmp numbers>:invocations but used %s'%invocation)

                    triple = []
                    for pair in t:
                        r = pair.split('-')
                        if len(r)==1:
                            triple.append((r[0],r[0]))
                        elif len(r)==2:
                            triple.append(r)
                        else:
                            raise UserException('Wrong invocation syntax: expected a single number or "number-number" format but used %s'%pair)
                    try:
                        int(triple[2][0])
                        int(triple[2][1])
                    except:
                        raise UserException('The last item in invocation triple should be number.')
                    self.config['invocation']['triples'].append(triple)

        # parsing data parameters
        if opts.data:
            for line in opts.data:
                line = line["_"]
                for data in line.split(','):
                    key, value = data.split('=', 1)
                    if key == 'condition':
                        t = value.strip().split(':')
                        if len(t) == 1:
                            self.config['data']['condition'].append(('and', t[0]))
                        elif len(t) == 2:
                            #if t[0] in ('set', 'or', 'and'):
                            if t[0] in ('and'): # supports "and" only
                                self.config['data']['condition'].append((t[0], t[1]))
                            else:
                                raise UserException('Unknown condition action type: %s' % t[0])
                        else:
                            raise UserException('Wrong number of condition subvalues: %s' % value)
                    elif key == 'maxnuminvokes':
                        self.config['data']['maxnuminvokes'] = int(value)
                    else:
                        raise UserException('Unknown data option: %s' % key)
        # parsing OpenMP parameters
        if opts.openmp:
            self.config['openmp']['enabled'] = True
            for line in opts.openmp:
                line = line["_"]
                for openmp in line.split(','):
                    if openmp=='enable':
                        pass
                    else:
                        key, value = openmp.split('=')
                        if key=='kernel-in-critical-region':
                            if value=='no':
                                self.config['openmp']['critical'] = False
                        elif key=='omp_num_threads':
                            if isinstance(value, str) and value.isdigit():
                                self.config['openmp']['maxnum_threads'] = int(value)
                        else:
                            raise UserException('Unknown OpenMP option: %s' % openmp)

        # parsing MPI parameters
        if opts.mpi:
            self.config['mpi']['enabled'] = True

            for line in opts.mpi:
                line = line["_"]
                for mpi in line.split(','):
                    if mpi=='enable':
                        pass
                    else:
                        key, value = mpi.split('=', 1)
                        if key=='comm':
                            self.config['mpi'][key] = value
                        elif key=='use':
                            mod_name, identifier = value.split(':')
                            self.config['mpi']['use_stmts'].append((mod_name, [identifier]))
                        elif key=='ranks':
                            print('ranks subflag for mpi is not supported. Please use invocation flag instead')
                            sys.exit(-1)
                            #self.config['mpi'][key] = value.split(':')
                            #self.config['mpi']['size'] = len(self.config['mpi'][key])
                        elif key=='header':
                            self.config['mpi'][key] = value
                        else:
                            raise UserException('Unknown MPI option: %s' % mpi)
        # parsing kernel makefile parameters
        if opts.prerun:
            for line in opts.prerun:
                line = line["_"]
                for comp in line.split(','):
                    key, value = comp.split('=', 1)
                    if key in [ 'build', 'run', 'kernel_build', 'kernel_run' ] :
                        self.config['prerun'][key] = dequote(value)
                    else:
                        raise UserException('Unknown prerun option: %s' % comp)

        if opts.rebuild:
            for line in opts.rebuild:
                line = line["_"]
                for comp in line.split(','):
                    self.config['rebuild'][comp] = True
#
#        if opts.cmd_clean:
#            self.config['cmd_clean']['cmds'] = dequote(opts.cmd_clean["_"])
#
#
#        if opts.cmd_build:
#            self.config['cmd_build']['cmds'] = dequote(opts.cmd_build["_"])
#
#        if opts.cmd_run:
#            self.config['cmd_run']['cmds'] = dequote(opts.cmd_run["_"])

        if opts.state_switch:
            for line in opts.state_switch:
                line = line["_"]
                for run in line.split(','):
                    key, value = run.split('=', 1)
                    if key in [ 'directory', 'type', 'clean', 'script' ] :
                        self.config['state_switch'][key] = dequote(value)
                    else:
                        raise UserException('Unknown state-switch option: %s' % run)

        if opts.kernel_option:
            for line in opts.kernel_option:
                line = line["_"]
                for kopt in line.split(','):
                    split_kopt = kopt.split('=', 1)
                    if len(split_kopt)==1:
                        self.config['kernel_option']['compiler']['add'].append(dequote(split_kopt[0]))
                    elif len(split_kopt)==2:
                        if split_kopt[0] in [ 'FC', 'FC_FLAGS' ]:
                            self.config['kernel_option'][split_kopt[0]] = dequote(split_kopt[1])
                        elif split_kopt[0] in ('add', 'remove'):
                            self.config['kernel_option']['compiler'][split_kopt[0]].extend(dequote(split_kopt[1]).split(':'))
                        elif split_kopt[0]=='link':
                            self.config['kernel_option']['linker']['add'].extend(dequote(split_kopt[1]).split(':'))
                        else:
                            raise UserException('Unknown state-switch option: %s' % kopt)

        # kernel correctness checks
        if opts.check:
            for line in opts.check:
                line = line["_"]
                for checkparams in line.split(','):
                    key, value = checkparams.split('=', 1)
                    key = key.lower()
                    value = value.lower()
                    if key=='pert_invar':
                        self.config['check'][key] = value.split(':')
                    elif key=='pert_lim':
                        self.config['check'][key] = value
                    elif key=='tolerance':
                        self.config['verify'][key] = value
                    else:
                        print('WARNING: %s is not supported check parameter'%key)

        # parsing logging options
        if opts.verbose_level:
            self.config['verify']['verboselevel'] = str(opts.verbose_level["_"])

        # mpi frame code in kernel driver
        if opts.add_mpi_frame:
            for checkparams in opts.add_mpi_frame["_"].split(','):
                sparam = checkparams.split('=')
                if len(sparam) == 2:
                    key, value = sparam
                    key = key.lower()
                    if key in ['np', 'mpirun', 'mpifc']:
                        self.config['add_mpi_frame']['enabled'] = True
                        self.config['add_mpi_frame'][key] = value
                    else:
                        print('WARNING: %s is not supported add_mpi_frame parameter'%key)
                elif len(sparam) == 1:
                    if sparam[0] == "enabled":
                        self.config['add_mpi_frame']['enabled'] = True
                    else:
                        print('WARNING: %s is not supported add_mpi_frame parameter'%sparam[0])

        # cache pollution frame code in kernel driver
        if opts.add_cache_pollution:
            if opts.add_cache_pollution["_"].isdigit():
                self.config['add_cache_pollution']['enabled'] = True
                self.config['add_cache_pollution']['size'] = int(opts.add_cache_pollution["_"])
            else:
                print('WARNING: %s is not supported add_cache_pollution parameter'%opts.add_cache_pollution["_"])

#
#    def _process_repr_flags(self, opts):
#
#        if opts.repr_etime:
#            for line in opts.repr_etime:
#                line = line["_"]
#                for eopt in line.split(','):
#                    split_eopt = eopt.split('=', 1)
#                    if len(split_eopt)==1:
#                        if split_eopt[0] == 'enable':
#                            self.config['model']['types']['etime']['enabled'] = True
#                        elif split_eopt[0] == 'disable':
#                            self.config['model']['types']['etime']['enabled'] = False
#                        else:
#                            raise UserException('Unknown elapsed-time flag option: %s' % eopt)
#                    elif len(split_eopt)==2:
#
#                        self.config['model']['types']['etime']['enabled'] = True
#
#                        if split_eopt[0] in [ 'minval', 'maxval' ]:
#                            self.config['model']['types']['etime'][split_eopt[0]] = float(split_eopt[1])
#                        elif split_eopt[0] in ('nbins', 'ndata'):
#                            self.config['model']['types']['etime'][split_eopt[0]] = int(split_eopt[1])
#                        elif split_eopt[0] in ('timer', ):
#                            self.config['model']['types']['etime'][split_eopt[0]] = split_eopt[1]
#                        else:
#                            raise UserException('Unknown elapsed-time flag option: %s' % eopt)
#
#        if opts.repr_papi:
#            for line in opts.repr_papi:
#                line = line["_"]
#                for popt in line.split(','):
#                    split_popt = popt.split('=', 1)
#                    if len(split_popt)==1:
#                        if split_popt[0] == 'enable':
#                            self.config['model']['types']['papi']['enabled'] = True
#                        elif split_popt[0] == 'disable':
#                            self.config['model']['types']['papi']['enabled'] = False
#                        else:
#                            raise UserException('Unknown papi-counter flag option: %s' % popt)
#                    elif len(split_popt)==2:
#
#                        self.config['model']['types']['papi']['enabled'] = True
#
#                        if split_popt[0] in [ 'minval', 'maxval', 'header', 'static', 'dynamic', 'event' ]:
#                            self.config['model']['types']['papi'][split_popt[0]] = split_popt[1]
#                        elif split_popt[0] in ('nbins', 'ndata'):
#                            self.config['model']['types']['papi'][split_popt[0]] = int(split_popt[1])
#                        else:
#                            raise UserException('Unknown papi-counter flag option: %s' % popt)
#        if opts.repr_code:
#            for line in opts.repr_code:
#                line = line["_"]
#                for copt in line.split(','):
#                    split_copt = copt.split('=', 1)
#                    if len(split_copt)==1:
#                        if split_copt[0] == 'enable':
#                            self.config['model']['types']['code']['enabled'] = True
#                        elif split_copt[0] == 'disable':
#                            self.config['model']['types']['code']['enabled'] = False
#                        else:
#                            raise UserException('Unknown code-coverage flag option: %s' % copt)
#                    elif len(split_copt)==2:
#
#                        self.config['model']['types']['code']['enabled'] = True
#
#                        if split_copt[0] in [ 'percentage' ]:
#                            self.config['model']['types']['code'][split_copt[0]] = float(split_copt[1])
#                        elif split_copt[0] in [ 'filter' ]:
#                            self.config['model']['types']['code'][split_copt[0]] = split_copt[1].strip().split(':')
#                        elif split_copt[0] in ( 'ndata' ):
#                            self.config['model']['types']['code'][split_popt[0]] = int(split_copt[1])
#                        else:
#                            raise UserException('Unknown code-coverage flag option: %s' % copt)
#
#            # enable coverage feature at extractor
#            #if self.config['model']['types']['code']['enabled']:
#            #    self.config['plugin']['priority']['ext.coverage'] = '%s/plugins/coverage'%KGEN_EXT

    def get_exclude_actions(self, section_name, *args ):
        if section_name=='namepath':
            if len(args)<1: return []

            if section_name in self.config["exclude"]:
                options = self.config["exclude"][section_name]
                for pattern, actions in options.items():
                    if match_namepath(pattern, args[0]):
                        return actions
            return []
        else:
            UserException('Not supported section name in exclusion input file: %s'%section)

    def process_exclude_option(self, exclude_option, excattrs):

        # collect exclude configuration information
        Exc = KgenConfigParser(allow_no_value=True)
        #Exc.optionxform = str
        Exc.read(exclude_option)
        if len(Exc.sections())>0:
            for section in Exc.sections():
                lsection = section.lower().strip()
                if lsection=='common':
                    print('ERROR: a section of "common" is discarded in INI file for exclusion. Please use "namepath" section instead')
                    sys.exit(-1)

                excattrs[lsection] = OrderedDict()
                for option in Exc.options(section):
                    loption = option.lower().strip()
                    excattrs[lsection][loption] = Exc.get(section, option).strip().split('=')
        else:
            UserException('Can not find exclude file: %s'%exclude_option)



    def process_include_option(self):

        incattrs = self.config["include"]

        if incattrs['opt']:
            self.config["includefile"] = os.path.basename(incattrs['opt'])
            shutil.copy(incattrs['opt'], self.config["path"]['outdir'])

        # collect include configuration information
        Inc = KgenConfigParser(allow_no_value=True)
        #Inc.optionxform = str
        Inc.read('%s/%s'%(self.config["path"]['outdir'], self.config["includefile"]))
        for section in Inc.sections():
            lsection = section.lower().strip()
            #if lsection in [ 'type', 'rename', 'state', 'extern' ]:
            if lsection in [ 'type', 'macro' ]:
                for option in Inc.options(section):
                    incattrs[lsection][option] = Inc.get(section, option).strip()
            elif lsection=='import':
                for option in Inc.options(section):
                    incattrs[lsection][option] = Inc.get(section, option).strip()
    #                subflags = OrderedDict()
    #                for subf in Inc.get(section, option).split(','):
    #                    subflags[subf.strip()] = None
    #                incattrs[lsection][option] = subflags
            elif lsection=='include':
                for option in Inc.options(section):
                    incattrs['path'].append(option.strip())
            elif lsection=='compiler':
                for option in Inc.options(section):
                    incattrs[lsection][option] = Inc.get(section, option).strip()
            elif os.path.isfile(section):
                realpath = os.path.realpath(section)
                if realpath not in incattrs['file']:
                    incattrs['file'][realpath] = OrderedDict()
                    incattrs['file'][realpath]['path'] = ['.']
                    incattrs['file'][realpath]['compiler'] = None
                    incattrs['file'][realpath]['compiler_options'] = None
                    incattrs['file'][realpath]['macro'] = OrderedDict()
                for option in Inc.options(section):
                    if option=='include':
                        pathlist = Inc.get(section, option).split(':')
                        incattrs['file'][realpath]['path'].extend(pathlist)
                    elif option in [ 'compiler', 'compiler_options' ]:
                        incattrs['file'][realpath][option] = Inc.get(section, option)
                    else:
                        incattrs['file'][realpath]['macro'][option] = Inc.get(section, option)
            else:
                pass
                #print '%s is either not suppored keyword or can not be found. Ignored.' % section
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


    def find_machine(self):

        import glob

        # find machine files
        inc = None
        for path in glob.glob('%s/*'%KGEN_MACHINE):
            try:
                inc = KgenConfigParser(allow_no_value=True)
                inc.read(path)
                cmd = inc.get('shell', 'command')
                out, err, retcode = run_shcmd(cmd)
                if retcode == 0:
                    if inc.has_option('shell', 'startswith'):
                        if any( out.startswith(s.strip()) for s in inc.get('shell', 'startswith').split(',') ):
                            break
                    elif inc.has_option('shell', 'pattern'):
                        if any( re.match(p.strip(), out) for p in inc.get('shell', 'pattern').split(',') ):
                            break
                inc = None
            except:
                inc = None

        if inc is None:
            inc = KgenConfigParser(allow_no_value=True)
            inc.read('%s/generic_Linux'%KGEN_MACHINE)

        return inc


    def read_machinefile(self, machine, prerun):

        # populate contents of the machine file
        try:
            inc = machine['inc']
            if inc.has_section('general'):
                if inc.has_option('general', 'name') and inc.get('general', 'name'):
                    machine['general']['name'] = inc.get('general', 'name')
                if inc.has_option('general', 'id') and inc.get('general', 'id'):
                    machine['general']['id'] = inc.get('general', 'id')
            if inc.has_section('variable'):
                if inc.has_option('variable', 'prerun_build') and inc.get('variable', 'prerun_build'):
                    prerun['build'] = inc.get('variable', 'prerun_build')
                if inc.has_option('variable', 'prerun_run') and inc.get('variable', 'prerun_run'):
                    prerun['run'] = inc.get('variable', 'prerun_run')
                if inc.has_option('variable', 'prerun_kernel_build') and inc.get('variable', 'prerun_kernel_build'):
                    prerun['kernel_build'] = inc.get('variable', 'prerun_kernel_build')
                if inc.has_option('variable', 'prerun_kernel_run') and inc.get('variable', 'prerun_kernel_run'):
                    prerun['kernel_run'] = inc.get('variable', 'prerun_kernel_run')
                if inc.has_option('variable', 'work_directory') and inc.get('variable', 'work_directory'):
                    machine['variable']['work_directory'] = os.path.expandvars(inc.get('variable', 'work_directory'))
            if inc.has_section('compiler'):
                if inc.has_option('compiler', 'gnu') and inc.get('compiler', 'gnu'):
                    machine['compiler']['gnu'] = inc.get('compiler', 'gnu')
                if inc.has_option('compiler', 'intel') and inc.get('compiler', 'intel'):
                    machine['compiler']['intel'] = inc.get('compiler', 'intel')
                if inc.has_option('compiler', 'pgi') and inc.get('compiler', 'pgi'):
                    machine['compiler']['pgi'] = inc.get('compiler', 'pgi')
        except:
            pass

def handle_include(mpifdir, lines, config):

    insert_lines = []
    for i, line in enumerate(lines):
        match = re.match(r'^\s*include\s*("[^"]+"|\'[^\']+\')\s*\Z', line, re.I)
        if match:
            include_dirs = [mpifdir]+config["include"]['path']
            filename = match.group(1)[1:-1].strip()
            path = filename
            for incl_dir in include_dirs:
                path = os.path.join(incl_dir, filename)
                if os.path.exists(path):
                    break
            if os.path.isfile(path):
                with open(path, 'r') as f:
                    included_lines = f.read()
                    insert_lines.extend(handle_include(mpifdir, included_lines.split('\n'), config))
            else:
                raise UserException('Can not find %s in include paths.'%path)
        else:
            insert_lines.append(line)

    return insert_lines
