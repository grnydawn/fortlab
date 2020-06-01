
from microapp import App


class FortranTiming(App):

    _name_ = "timing"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("analysis", help="analysis object")

        #self.register_forward("analysis", help="analysis object")

    def perform(self, mgr, args):

        import pdb; pdb.set_trace()
