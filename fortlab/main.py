from microapp import Project

# TODO: buildmodel and runmodell will go to langlab project

from fortlab.scanner import (MicroappBuildScanner, MicroappRunScanner,
                             MicroappModelCombiner)
from fortlab.scanner.compile import FortranCompilerOption
from fortlab.scanner.timing import (FortranTimingGenerator,
            FortranTimingCollector, FortranTimingCombiner)
from fortlab.resolver import FortranNameResolver
from fortlab.kernel import FortranKernelGenerator
from fortlab.state import FortranStateGenerator
from fortlab.vargen import FortranVariableAnalyzer

class Fortlab(Project):
    _name_ = "fortlab"
    _version_ = "0.1.15"
    _description_ = "Fortran Kernel and Analysis Framework"
    _long_description_ = "Tools for Analysis of Fortran Application and Source code"
    _author_ = "Youngsung Kim"
    _author_email_ = "youngsung.kim.act2@gmail.com"
    _url_ = "https://github.com/grnydawn/fortlab"
    _builtin_apps_ = [MicroappBuildScanner, MicroappRunScanner,
                      FortranCompilerOption, FortranNameResolver,
                      FortranTimingGenerator, FortranKernelGenerator,
                      FortranStateGenerator, MicroappModelCombiner,
                      FortranTimingCollector, FortranTimingCombiner,
                      FortranVariableAnalyzer]
    _requires_ = ["dict2json>=0.1.2"]

    def __init__(self):
        self.add_argument("--test", help="test argument")
