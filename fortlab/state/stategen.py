from microapp import App

class FortranStateGenerator(App):

    _name_ = "stategen"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("analysis", help="analysis object")
        self.add_argument("--outdir", help="output directory")

        self.register_forward("statedir", help="state generation code directory")
    
    def perform(self, args):

        self.config = args.analysis["_"]

        # create directory if needed
        args.outdir = args.outdir["_"] if args.outdir else os.getcwd()

        if not os.path.exists(args.outdir):
            os.makedirs(args.outdir)

        import pdb; pdb.set_trace()
        state_realpath = os.path.realpath(os.path.join(args.outdir, "state"))

        self.add_forward(statedir=state_realpath)


