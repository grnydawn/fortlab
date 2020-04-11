from microapp import Project

class Fortlab(Project):
    _name_ = "fortlab"
    _version_ = "0.1.0"

    def __init__(self):
        self.add_argument("test", help="test argument")
