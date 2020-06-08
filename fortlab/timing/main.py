
import os

from collections import OrderedDict
from configparser import ConfigParser
from microapp import App


class FortranTimingCodegen(App):

    _name_ = "timingcodegen"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.config = None

        self.add_argument("analysis", help="analysis object")
        self.add_argument("--outdir", help="output directory")
        self.add_argument("--no-cache", action="store_true",
                            help="force to collect timing data")

        #self.register_forward("analysis", help="analysis object")

    def perform(self, args):

        self.config = args.analysis["_"]

        # create directory if needed
        if not args.outdir:
            args.outdir = os.getcwd()

        if not os.path.exists(args.outdir):
            os.makedirs(args.outdir)

        srcfiles = OrderedDict()

        etimedir = os.path.join(args.outdir, "etime")

        if not self.hasmodel(etimedir) or args.no_cache:

            data_etime_path = os.path.join(model_realpath, "__data__",  self.config["model"]['types']['etime']['id'])
            if os.path.exists(data_etime_path) and len(glob.glob( os.path.join(data_etime_path, "*"))) > 0 and self.config["model"]['reuse_rawdata']:
                kgutils.logger.info('Reusing elapsedtime raw data.')
            else:
                kgutils.logger.info('Generating elapsedtime raw data.')

                if os.path.exists(data_etime_path):
                    shutil.rmtree(data_etime_path)

                rsc_etime_path = os.path.join(model_realpath, "__data__", "__resource__", self.config["model"]['types']['etime']['id'])
                if os.path.exists(rsc_etime_path):
                    shutil.rmtree(rsc_etime_path)

                time.sleep(1)

                os.makedirs(data_etime_path)
                os.makedirs(rsc_etime_path)

        # generate code if not cached
        import pdb; pdb.set_trace()


    def hasmodel(self, modeltype):

        modelfile = os.path.join(self.config["path"]["outdir"], self.config["modelfile"])

        if not os.path.exists(modelfile):
            return False

        has_general = False
        has_modeltype = False
        has_modelsection = False
        section = ''
        required_modelsections = []
        model_sections = {}

        with open(modelfile, 'r') as mf:

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

        with open(modelfile, mode) as mf:
            cfg.write(mf)





    def addmodel(self, modeltype, sections):

        modelfile = '%s/%s'%(Config.path['outdir'], Config.modelfile)

        mode = 'r+'
        if not os.path.exists(modelfile):
            mode = 'w+'

        with open(modelfile, mode) as mf:
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

        with open(modelfile, mode) as mf:
            cfg.write(mf)
                            
