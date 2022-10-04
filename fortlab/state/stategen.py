from microapp import App

class FortranStateGenerator(App):

    _name_ = "stategen"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("analysis", help="analysis object")
        self.add_argument("--outdir", help="output directory")

        self.register_forward("statedir", help="state generation code directory")
    
    def perform(self, args):

        raise("stategen is not implemented yet.")
