from microapp import Project

from fortlab.compile import MicroappCompile
from fortlab.analyze import FortranAnalyzer

class Fortlab(Project):
    _name_ = "fortlab"
    _version_ = "0.1.3"
    _description_ = "Fortran Analysis Utilities"
    _long_description_ = "Tools for Analysis of Fortran Application and Source code"
    _author_ = "Youngsung Kim"
    _author_email_ = "youngsung.kim.act2@gmail.com"
    _url_ = "https://github.com/grnydawn/fortlab"
    _builtin_apps_ = [MicroappCompile, FortranAnalyzer]
    _requires_ = ["dict2json>=0.1.2"]

    def __init__(self):
        self.add_argument("--test", help="test argument")
