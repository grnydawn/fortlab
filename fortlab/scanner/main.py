import os, json

from microapp import App, appdict
from collections import OrderedDict

from fortlab.kggenfile import init_plugins, plugin_config, KERNEL_ID_0

here = os.path.dirname(os.path.realpath(__file__))

class MicroappBuildScanner(App):
    _name_ = "buildscan"
    _version_ = "0.1.0"
 
    def __init__(self, mgr):

        self.add_argument("buildcmd", metavar="build command", help="Software build command")
        self.add_argument("--cleancmd", type=str, help="Software clean command.")
        self.add_argument("--outdir", type=str, help="output directory")
        self.add_argument("--workdir", type=str, help="work directory")
        self.add_argument("--savejson", type=str, help="save data in a josn-format file")
        self.add_argument("--reuse", type=str, help="reuse existing file(s)")
        self.add_argument("--backupdir", type=str, help="saving source files used")
        self.add_argument("--verbose", action="store_true", help="show compilation details")
        self.add_argument("--check", action="store_true", help="check strace return code")

        self.register_forward("data", help="json object")

    def perform(self, args):

        if args.reuse["_"] and os.path.isfile(args.reuse["_"]):
            with open(args.reuse["_"]) as f:
                strace_data = json.load(f)
            self.add_forward(data=strace_data)
            return

        #cmd = ["compileroption", args.buildcmd["_"]]
        opts = [args.buildcmd["_"]]

        if args.cleancmd:
            opts += ["--cleancmd", args.cleancmd["_"]]

        if args.workdir:
            opts += ["--workdir", args.workdir["_"]]

        if args.outdir:
            opts += ["--outdir", args.outdir["_"]]

        if args.savejson:
            opts += ["--savejson", args.savejson["_"]]

        if args.backupdir:
            opts += ["--backupdir", args.backupdir["_"]]

        if args.verbose:
            opts += ["--verbose"]

        if args.check:
            opts += ["--check"]

        ret, fwds = self.run_subapp("compileroption", opts)
        assert ret == 0, "compileroption returned non-zero code."

        self.add_forward(data=fwds["data"])


class MicroappRunScanner(App):
    _name_ = "runscan"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("analysis", help="analysis object")
        self.add_argument("--cleancmd", type=str, help="Software clean command.")
        self.add_argument("--buildcmd", metavar="build command", help="Software build command")
        self.add_argument("--runcmd", metavar="run command", help="Software run command")
        self.add_argument("--outdir", help="output directory")
        self.add_argument("-w", "--wait", help="wait to complete run")
        self.add_argument("-o", "--output", help="json output file")
        self.add_argument("-s", "--add-scan", action="append", help="add scanning method")
        self.add_argument("--no-cache", action="store_true",
                            help="force to collect timing data")
        self.add_argument("--noreuse-rawdata", dest="noreuse_rawdata", action='store_true',
                          help="Control raw data generation for modeling.")

        self.register_forward("model", help="model data file")
        self.register_forward("analysis", help="tree object")

        # model parameters
        self.config = appdict()

        self.config['modelfile'] = 'model.ini'
        self.config['model'] = OrderedDict()
        self.config['model']['path'] = ""
        self.config['model']['reuse_rawdata'] = True
        self.config['model']['types'] = OrderedDict()
        self.config['model']['types']['code'] = OrderedDict()
        self.config['model']['types']['code']['id'] = '0'
        self.config['model']['types']['code']['name'] = 'code'
        self.config['model']['types']['code']['collector'] = 'codecollect'
        self.config['model']['types']['code']['combiner'] = 'codecombine'
        self.config['model']['types']['code']['percentage'] = 99.9
        self.config['model']['types']['code']['filter'] = None
        self.config['model']['types']['code']['ndata'] = 20
        self.config['model']['types']['code']['enabled'] = False
        self.config['model']['types']['etime'] = OrderedDict()
        self.config['model']['types']['etime']['id'] = '1'
        self.config['model']['types']['etime']['name'] = 'etime'
        self.config['model']['types']['etime']['collector'] = 'timingcollect'
        self.config['model']['types']['etime']['combiner'] = 'timingcombine'
        self.config['model']['types']['etime']['nbins'] = 5
        self.config['model']['types']['etime']['ndata'] = 20
        self.config['model']['types']['etime']['minval'] = None
        self.config['model']['types']['etime']['maxval'] = None
        self.config['model']['types']['etime']['timer'] = None
        self.config['model']['types']['etime']['enabled'] = True
        self.config['model']['types']['papi'] = OrderedDict()
        self.config['model']['types']['papi']['id'] = '2'
        self.config['model']['types']['papi']['name'] = 'papi'
        self.config['model']['types']['papi']['collector'] = 'papicollect'
        self.config['model']['types']['papi']['combiner'] = 'papicombine'
        self.config['model']['types']['papi']['nbins'] = 5
        self.config['model']['types']['papi']['ndata'] = 20
        self.config['model']['types']['papi']['minval'] = None
        self.config['model']['types']['papi']['maxval'] = None
        self.config['model']['types']['papi']['header'] = None
        self.config['model']['types']['papi']['event'] = 'PAPI_TOT_INS'
        self.config['model']['types']['papi']['static'] = None
        self.config['model']['types']['papi']['dynamic'] = None
        self.config['model']['types']['papi']['enabled'] = False

    def perform(self, args):

        # generating model raw data
        if args.noreuse_rawdata:
            self.config['model']['reuse_rawdata'] = False if args.noreuse_rawdata else True

        ret, fwds = 0, {}

        outdir = args.outdir["_"] if args.outdir else os.getcwd()
        modeldir = os.path.join(outdir, "model")

        self.config["model"]["path"] = os.path.realpath(modeldir)
 
        mtypes = {u"datatype": u"model", u"datamap": {}, u"collectmap": {},
                  u"combinemap": {}}

        scans = [s["_"] for s in args.add_scan]


        if args.add_scan is None or "timing" in scans:
            self.scan_timing(args, modeldir, mtypes, args.analysis["_"])

        with open('%s/__data__/modeltypes' % modeldir, 'w') as f:
            json.dump(mtypes, f)

        # TODO: wait if needed

        ret, fwds = self.combine_model(modeldir)
        assert ret == 0, "combine_model returned non-zero code."

        if args.output:
            with open(args.output["_"], "w") as f:
                json.dump(fwds["model"], f)

        self.add_forward(model=fwds['model'])
        self.add_forward(analysis=args.analysis['_'])

    def combine_model(self, modeldir):

        #cmd = ["modelcombine", modeldir]

        #return self.manager.run_command(cmd)
        return self.run_subapp("modelcombine", [modeldir])

    def scan_timing(self, args, modeldir, mtypes, config):

        mtypes["datamap"][self.config['model']['types']['etime']['id']] = \
            self.config['model']['types']['etime']['name']

        mtypes["collectmap"][self.config['model']['types']['etime']['id']] = \
            self.config['model']['types']['etime']['collector']

        mtypes["combinemap"][self.config['model']['types']['etime']['id']] = \
            self.config['model']['types']['etime']['combiner']

        etime_plugindir = os.path.join(here, "timing", "plugins", "gencore")

        init_plugins([KERNEL_ID_0], (('etime.gencore', etime_plugindir),), config)

        plugin_config["current"].update(self.config)

        #cmd = ["timinggen", "@analysis"]
        opts = ["@analysis"]

        if args.cleancmd:
            opts += ["--cleancmd", args.cleancmd["_"]]

        if args.buildcmd:
            opts += ["--buildcmd", args.buildcmd["_"]]

        if args.runcmd:
            opts += ["--runcmd", args.runcmd["_"]]

        if args.outdir:
            opts += ["--outdir", args.outdir["_"]]

        if args.no_cache:
            opts += ["--no-cache"]

        #ret, fwds = self.manager.run_command(cmd, forward={"analysis": config})
        ret, fwds = self.run_subapp("timinggen", opts, forward={"analysis": config})
        assert ret == 0, "timinggen returned non-zero code."

        etimedir = fwds["etimedir"]
        #cmd = "shell 'cd %s; make; make recover' --useenv" % fwds["etimedir"]
        opts = ["'make'" , "--useenv", "--workdir", etimedir]
        ret, fwds = self.run_subapp("shell", opts)
        assert ret == 0, "shell make returned non-zero code: %s" % fwds['stderr']

        opts = ["make recover" , "--useenv", "--workdir", etimedir]
        ret, fwds = self.run_subapp("shell", opts)
        assert ret == 0, "shell 'make recover' returned non-zero code: %s" % fwds['stderr']

        
class MicroappModelCombiner(App):

    _name_ = "modelcombine"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("modeldir", metavar="raw datadir", help="Raw model data directory")
        self.add_argument("-o", "--output", type=str, help="output path.")

        self.register_forward("model", help="model object")


    def perform(self, args):

        modeldir = args.modeldir["_"]
        datadir = os.path.join(modeldir, "__data__")
        metafile = os.path.join(datadir, "modeltypes")

        model = appdict()

        with open(metafile, 'r') as fm:
            mtypes = json.load(fm)

            for scanid, scanname in mtypes["datamap"].items():
                scandir = os.path.join(datadir, scanid)

                if os.path.isdir(scandir) and len(os.listdir(scandir)):
                    collector = mtypes["collectmap"][scanid]
                    #cmd = collector + " " + scandir
                    #ret, fwds = self.manager.run_command(cmd)
                    ret, fwds = self.run_subapp(collector, [scandir])
                    assert ret == 0, "%s returned non-zero code." % collector
                    assert "data" in fwds, "No data is defined in %s." % collector
                    assert fwds["data"], "No %s data is collected." % collector

                    model[scanname] = fwds['data']
                    #combiner = mtypes["combinemap"][scanid]
                    #cmd = combiner + " @data"
                    #ret, fwds = self.manager.run_command(cmd,
                    #ret, fwds = self.run_subapp(combiner, ["@data"],
                    #                forward={"data": fwds["data"]})

        self.add_forward(model=model)
