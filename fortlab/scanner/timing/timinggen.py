
import os, time, glob, shutil, locale, io

from collections import OrderedDict
from configparser import ConfigParser
from microapp import App

from fortlab.kgutils import logger, remove_multiblanklines, dequote, UserException
from fortlab.kggenfile import gensobj, KERNEL_ID_0, event_register, Gen_Statement, set_indent, init_plugins


class FortranTimingGenerator(App):

    _name_ = "timinggen"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.config = None
        self.genfiles = []

        self.add_argument("analysis", help="analysis object")
        self.add_argument("--cleancmd", type=str, help="Software clean command.")
        self.add_argument("--buildcmd", metavar="build command", help="Software build command")
        self.add_argument("--runcmd", metavar="run command", help="Software run command")
        self.add_argument("--outdir", help="output directory")
        self.add_argument("--no-cache", action="store_true",
                            help="force to collect timing data")

        self.register_forward("etimedir", help="elapsedtime instrumented code directory")
        self.register_forward("modeldir", help="elapsedtime data directory")

    def perform(self, args):

        self.config = args.analysis["_"]

        if args.cleancmd:
            self.config["cmd_clean"]['cmds'] = dequote(args.cleancmd["_"])

        if args.buildcmd:
            self.config["cmd_build"]['cmds'] = dequote(args.buildcmd["_"])

        else:
            raise UserException("'--buildcmd' option is not given.")

        if args.runcmd:
            self.config["cmd_run"]['cmds'] = dequote(args.runcmd["_"])

        else:
            raise UserException("'--runcmd' option is not given.")

        # create directory if needed
        args.outdir = args.outdir["_"] if args.outdir else os.getcwd()

        if not os.path.exists(args.outdir):
            os.makedirs(args.outdir)

        srcfiles = OrderedDict()

        #etimedir = os.path.join(args.outdir, "etime")

        model_realpath = os.path.realpath(os.path.join(args.outdir, "model"))
        etime_realpath = os.path.realpath(os.path.join(args.outdir, "etime"))

        self.add_forward(etimedir=etime_realpath, modeldir=model_realpath)

        if not self.hasmodel(args.outdir) or args.no_cache:
            data_etime_path = os.path.join(model_realpath, "__data__",
                                self.config["model"]['types']['etime']['id'])

            if not os.path.exists(etime_realpath):
                os.makedirs(etime_realpath)

            if (os.path.exists(data_etime_path) and len(glob.glob(os.path.join(
                    data_etime_path, "*"))) > 0 and
                    self.config["model"]['reuse_rawdata']):
                logger.info('Reusing elapsedtime raw data.')

            else:
                logger.info('Generating elapsedtime raw data.')

                if os.path.exists(data_etime_path):
                    shutil.rmtree(data_etime_path)

                rsc_etime_path = os.path.join(model_realpath, "__data__",
                    "__resource__", self.config["model"]['types']['etime']['id'])

                if os.path.exists(rsc_etime_path):
                    shutil.rmtree(rsc_etime_path)

                time.sleep(1)

                os.makedirs(data_etime_path)
                os.makedirs(rsc_etime_path)

                # generate wrapper nodes
                for filepath, (srcobj, mods_used, units_used) in self.config["srcfiles"].items():
                    if os.path.realpath(filepath) == os.path.realpath(self.config["callsite"]['filepath']):
                        sfile = gensobj(None, srcobj.tree, KERNEL_ID_0)
                        sfile.used4etime = True
                        self.genfiles.append((sfile, filepath))
                        self.config["used_srcfiles"][filepath] = (sfile, mods_used, units_used)


#                here = os.path.dirname(os.path.realpath(__file__))
#                etime_plugindir = os.path.join(here, "plugins", "gencore")
#
#                self.config["path"]["model_path"] = model_realpath 
#
#                init_plugins([KERNEL_ID_0], {'etime.gencore': etime_plugindir}, self.config)

                # process each nodes in the tree
                for plugin_name in event_register.keys():
                    if not plugin_name.startswith('etime'): continue

                    for sfile, filepath in self.genfiles:
                        sfile.created([plugin_name])

                for plugin_name in event_register.keys():
                    if not plugin_name.startswith('etime'): continue

                    for sfile, filepath in self.genfiles:
                        sfile.process([plugin_name])

                for plugin_name in event_register.keys():
                    if not plugin_name.startswith('etime'): continue

                    for sfile, filepath in self.genfiles:
                        sfile.finalize([plugin_name])

                for plugin_name in event_register.keys():
                    if not plugin_name.startswith('etime'): continue

                    for sfile, filepath in self.genfiles:
                        sfile.flatten(KERNEL_ID_0, [plugin_name])

                # generate source files from each node of the tree
                etime_files = []
                #import pdb; pdb.set_trace()
                for sfile, filepath in self.genfiles:
                    #import pdb; pdb.set_trace()
                    filename = os.path.basename(filepath)
                    if sfile.used4etime:
                        set_indent('')
                        slines = sfile.tostring()
                        if slines is not None:
                            slines = remove_multiblanklines(slines)
                            etime_files.append(filename)
                            enc = locale.getpreferredencoding(False)
                            with io.open(os.path.join(etime_realpath, filename), 'w', encoding=enc) as fd:
                                fd.write(slines)
                            with io.open(os.path.join(etime_realpath, filename+".kgen"), 'w', encoding=enc) as ft:
                                ft.write('\n'.join(sfile.kgen_stmt.prep))

                self.gen_makefile(etime_realpath)

    def hasmodel(self, outdir):

        modelfile = os.path.join(outdir, "model.ini")

        if not os.path.exists(modelfile):
            return False

        has_general = False
        has_modeltype = False
        has_modelsection = False
        section = ''
        required_modelsections = []
        model_sections = {}

        with io.open(modelfile, 'r') as mf:

            for line in mf.readlines():
                if line.startswith('['):
                    pos = line.find(']')
                    if pos > 0:
                        section = line[1:pos].strip()
                        if section == 'general':
                            has_general = True
                        else:
                            mtype, msec = section.split('.')
                            if mtype not in model_sections:
                                model_sections[mtype] = []
                            model_sections[mtype].append(msec)
                elif section == 'general' and line.find('=') > 0:
                    mtype, msections = line.split('=')
                    if mtype.strip() == modeltype:
                        required_modelsections = [s.strip() for s in
                                                    msections.split(',')]
                        has_modeltype = True
                if has_modeltype and modeltype in model_sections and all(
                    (msec in model_sections[modeltype]) for msec in
                        required_modelsections):
                    has_modelsection = True

                if has_general and has_modeltype and has_modelsection:
                    break

        return has_general and has_modeltype and has_modelsection

    def addsection(self, modeltype, section, options):

        modelfile = os.path.join(self.config["path"]["outdir"], self.config["modelfile"])

        mode = 'r+'
        if not os.path.exists(modelfile):
            raise Exception('Modelfile does not exists: %s'%modelfile)

        cfg = ConfigParser()
        cfg.optionxform = str
        cfg.read(modelfile)

        subsec = '%s.%s'%(modeltype, section)
        if cfg.has_section(subsec):
            raise Exception('Section already exists: %s'%subsec)

        cfg.add_section(subsec)

        for opt, val in options:
            cfg.set(subsec, opt, val)

        with io.open(modelfile, mode) as mf:
            cfg.write(mf)


    def addmodel(self, modeltype, sections):

        modelfile = '%s/%s'%(self.config["path"]['outdir'], self.config["modelfile"])

        mode = 'r+'
        if not os.path.exists(modelfile):
            mode = 'w+'

        with io.open(modelfile, mode) as mf:
            mf.seek(0, os.SEEK_END)
            size = mf.tell()
            if size == 0:
                mf.write('; KGen Model Data File\n')

        cfg = ConfigParser()
        cfg.optionxform = str
        cfg.read(modelfile)

        if not cfg.has_section(GEN):
            cfg.add_section(GEN)

        if not cfg.has_option(GEN, modeltype):
            cfg.set(GEN, modeltype, ', '.join(sections))
#
#        for sec in sections:
#            secname = '%s.%s'%(modeltype, sec)
#            if not cfg.has_section(secname):
#                cfg.add_section(secname)

        with io.open(modelfile, mode) as mf:
            cfg.write(mf)
                            

    def gen_makefile(self, etime_realpath):

        org_files = [ filepath for filepath, (sfile, mods_used, units_used) in self.config["used_srcfiles"].items() if sfile.used4etime ]

        if not self.config["topblock"]['stmt'].reader.id in org_files:
            org_files.append(self.config["topblock"]['filepath'])

        enc = locale.getpreferredencoding(False)
        with io.open('%s/Makefile'%etime_realpath, 'w', encoding=enc) as f:

            self.write(f, '# Makefile for KGEN-generated instrumentation')
            self.write(f, '')

            cwd = os.getcwd()

            prerun_build_str = ''
            if self.config["prerun"]['build']:
                self.write(f, 'PRERUN_BUILD := %s'%self.config["prerun"]['build'])
                prerun_build_str = '${PRERUN_BUILD}; '

            prerun_run_str = ''
            if self.config["prerun"]['run']:
                self.write(f, 'PRERUN_RUN := %s'%self.config["prerun"]['run'])
                prerun_run_str = '${PRERUN_RUN}; '

            self.write(f, '')
            if len(self.config["cmd_run"]['cmds']) > 0:
                self.write(f, 'run: build')
                self.write(f, '%s%s'%(prerun_run_str, self.config["cmd_run"]['cmds']), t=True)
            else:
                self.write(f, 'echo "No information is provided to run. Please specify run commands using \'state-run\' command line option"; exit -1', t=True)
            self.write(f, '')

            if len(self.config["cmd_build"]['cmds'])>0:
                self.write(f, 'build: %s'%self.config["state_switch"]['type'])
                self.write(f, '%s%s'%(prerun_build_str, self.config["cmd_build"]['cmds']), t=True)
                for org_file in org_files:
                    self.write(f, 'mv -f %(f)s.kgen_org %(f)s'%{'f':org_file}, t=True)
            else:
                self.write(f, 'echo "No information is provided to build. Please specify build commands using \'state-build\' command line option"; exit -1', t=True)
            self.write(f, '')

            self.write(f, '%s: save'%self.config["state_switch"]['type'])
            if self.config["state_switch"]['type']=='replace':
                for org_file in org_files:
                    basename = os.path.basename(org_file)
                    self.write(f, 'rm -f %s'%org_file, t=True)
                    self.write(f, 'cp -f %(f1)s %(f2)s'%{'f1':basename, 'f2':org_file}, t=True)
            elif self.config["state_switch"]['type']=='copy':
                for org_file in org_files:
                    basename = os.path.basename(org_file)
                    self.write(f, 'rm -f %s/%s'%(self.config["state_switch"]['directory'], basename), t=True)
                    self.write(f, 'cp -f %s/%s %s'%(etime_realpath, basename, self.config["state_switch"]['directory']), t=True)
            self.write(f, '')

            self.write(f, 'recover:')
            for org_file in org_files:
                self.write(f, 'rm -f %s'%org_file, t=True)
                self.write(f, 'cp -f %s.kgen_org %s'%(os.path.basename(org_file), org_file), t=True)
            self.write(f, '')

            self.write(f, 'recover_from_srcdir:')
            for org_file in org_files:
                self.write(f, 'rm -f %s'%org_file, t=True)
                self.write(f, 'cp -f %(f)s.kgen_org %(f)s'%{'f':org_file}, t=True)
            self.write(f, '')


            self.write(f, 'save:')
            for org_file in org_files:
                self.write(f, 'if [ ! -f %(f)s.kgen_org ]; then cp -f %(f)s %(f)s.kgen_org; fi'%{'f':org_file}, t=True)
                self.write(f, 'if [ ! -f %(g)s.kgen_org ]; then cp -f %(f)s %(g)s.kgen_org; fi'%{'f':org_file, 'g':os.path.basename(org_file)}, t=True)
            self.write(f, '')

            if len(self.config["cmd_clean"]['cmds']) > 0:
                self.write(f, 'clean:')
                self.write(f, self.config["cmd_clean"]['cmds'], t=True)
            self.write(f, '')

    def write(self, f, line, n=True, t=False):
        nl = ''
        tab = ''
        if n: nl = '\n'
        if t: tab = '\t'
        text = tab + line + nl

        if type(text) == type(u""):
            f.write(text)

        else:
            enc = locale.getpreferredencoding(False)
            f.write(text.decode(enc))

