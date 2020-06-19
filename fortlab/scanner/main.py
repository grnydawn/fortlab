from microapp import App

class MicroappBuildScanner(App):
    _name_ = "buildscan"
    _version_ = "0.1.0"
 
    def __init__(self, mgr):

        self.add_argument("buildcmd", metavar="build command", help="Software build command")
        self.add_argument("--cleancmd", type=str, help="Software clean command.")
        self.add_argument("--workdir", type=str, help="work directory")
        self.add_argument("--outdir", type=str, help="output directory")
        self.add_argument("--savejson", type=str, help="save data in a josn-format file")
        self.add_argument("--verbose", action="store_true", help="show compilation details")
        self.add_argument("--check", action="store_true", help="check strace return code")

        self.register_forward("data", help="json object")

    def perform(self, args):

        cmd = ["compileroption", args.buildcmd["_"]]

        if args.cleancmd:
            cmd += ["--cleancmd", args.cleancmd["_"]]

        if args.workdir:
            cmd += ["--workdir", args.workdir["_"]]

        if args.outdir:
            cmd += ["--outdir", args.outdir["_"]]

        if args.savejson:
            cmd += ["--savejson", args.savejson["_"]]

        if args.verbose:
            cmd += ["--verbose"]

        if args.check:
            cmd += ["--check"]

        ret, fwds = self.manager.run_command(cmd)

        self.add_forward(data=fwds["data"])


class MicroappRunScanner(App):
    _name_ = "runscan"
    _version_ = "0.1.0"

