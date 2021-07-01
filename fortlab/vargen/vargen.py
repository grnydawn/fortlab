import os, io, locale, math, random

from collections import OrderedDict
from microapp import App
from fortlab.kggenfile import (
    genkobj,
    gensobj,
    KERNEL_ID_0,
    event_register,
    create_rootnode,
    create_programnode,
    init_plugins,
    append_program_in_root,
    set_indent,
    plugin_config,
)
from fortlab.kgutils import (
    ProgramException,
    UserException,
    remove_multiblanklines,
    run_shcmd,
    tounicode,
)
from fortlab.resolver.kgparse import KGGenType
from fortlab.kgextra import (
    kgen_utils_file_head,
    kgen_utils_file_checksubr,
    kgen_get_newunit,
    kgen_error_stop,
    kgen_utils_file_tostr,
    kgen_utils_array_sumcheck,
    kgen_rankthread,
)

here = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
KGUTIL = "kgen_utils.f90"


class FortranVariableAnalyzer(App):
    _name_ = "vargen"
    _version_ = "0.1.0"

    def __init__(self, mgr):
        self.add_argument("analysis", help="analysis object")
        self.add_argument("--outdir", help="output directory")

        self.register_forward("kerneldir", help="kernel generation code directory")

    def perform(self, args):

        self.config = args.analysis["_"]

        args.outdir = args.outdir["_"] if args.outdir else os.getcwd()

        if not os.path.exists(args.outdir):
            os.makedirs(args.outdir)

        self._trees = []
        self.genfiles = []

        self.config["used_srcfiles"].clear()

        state_realpath = os.path.realpath(os.path.join(args.outdir, "state"))
        kernel_realpath = os.path.realpath(os.path.join(args.outdir, "kernel"))

        self.config["path"]["kernel_output"] = kernel_realpath
        self.config["path"]["state_output"] = state_realpath

        self.add_forward(kerneldir=kernel_realpath)

        if not os.path.exists(kernel_realpath):
            os.makedirs(kernel_realpath)

        gencore_plugindir = os.path.join(here, "plugins", "gencore")

        plugins = (
            ("ext.gencore", gencore_plugindir),
        )

        init_plugins([KERNEL_ID_0], plugins, self.config)
        plugin_config["current"].update(self.config)

        driver = create_rootnode(KERNEL_ID_0)
        self._trees.append(driver)
        program = create_programnode(driver, KERNEL_ID_0)
        program.name = self.config["kernel_driver"]["name"]
        append_program_in_root(driver, program)

        for filepath, (srcobj, mods_used, units_used) in self.config[
            "srcfiles"].items():
            if hasattr(srcobj.tree, "geninfo") and KGGenType.has_state(
                srcobj.tree.geninfo
            ):
                kfile = genkobj(None, srcobj.tree, KERNEL_ID_0)
                sfile = gensobj(None, srcobj.tree, KERNEL_ID_0)
                sfile.kgen_stmt.used4genstate = False
                if kfile is None or sfile is None:
                    raise kgutils.ProgramException(
                        "Kernel source file is not generated for %s." % filepath
                    )
                self.genfiles.append((kfile, sfile, filepath))
                self.config["used_srcfiles"][filepath] = (
                    kfile,
                    sfile,
                    mods_used,
                    units_used,
                )

        for plugin_name in event_register.keys():
            if not plugin_name.startswith("ext"):
                continue
            for kfile, sfile, filepath in self.genfiles:
                kfile.created([plugin_name])
                sfile.created([plugin_name])

            for tree in self._trees:
                tree.created([plugin_name])

        for plugin_name in event_register.keys():
            if not plugin_name.startswith("ext"):
                continue
            for kfile, sfile, filepath in self.genfiles:
                kfile.process([plugin_name])
                sfile.process([plugin_name])

            for tree in self._trees:
                tree.process([plugin_name])

        for plugin_name in event_register.keys():
            if not plugin_name.startswith("ext"):
                continue
            for kfile, sfile, filepath in self.genfiles:
                kfile.finalize([plugin_name])
                sfile.finalize([plugin_name])

            for tree in self._trees:
                tree.finalize([plugin_name])

        for plugin_name in event_register.keys():
            if not plugin_name.startswith("ext"):
                continue
            for kfile, sfile, filepath in self.genfiles:
                kfile.flatten(KERNEL_ID_0, [plugin_name])
                sfile.flatten(KERNEL_ID_0, [plugin_name])

            for tree in self._trees:
                tree.flatten(KERNEL_ID_0, [plugin_name])

        kernel_files = []
        state_files = []
        enc = locale.getpreferredencoding(False)

        for kfile, sfile, filepath in self.genfiles:
            filename = os.path.basename(filepath)
            set_indent("")
            klines = kfile.tostring()
            if klines is not None:
                klines = remove_multiblanklines(klines)
                kernel_files.append(filename)
                with io.open(
                    os.path.join(kernel_realpath, filename), "w", encoding=enc
                ) as (fd):
                    fd.write(tounicode(klines))

        with io.open(
            os.path.join(
                kernel_realpath, "%s.f90" % self.config["kernel_driver"]["name"]
            ),
            "w",
            encoding=enc,
        ) as (fd):
            set_indent("")
            lines = driver.tostring()
            if lines is not None:
                lines = remove_multiblanklines(lines)
                fd.write(tounicode(lines))

        kernel_files.append(self.config["kernel"]["name"])
        kernel_files.append(KGUTIL)
        self.generate_kgen_utils(kernel_realpath, enc)

        if self.config["state_switch"]["clean"]:
            run_shcmd(self.config["state_switch"]["clean"])

        return

    def generate_kgen_utils(self, kernel_path, enc):
        with io.open(os.path.join(kernel_path, KGUTIL), "w", encoding=enc) as (f):
            f.write(tounicode("MODULE kgen_utils_mod"))
            f.write(tounicode(kgen_utils_file_head))
            f.write(tounicode("\n"))
            f.write(tounicode("CONTAINS"))
            f.write(tounicode("\n"))
            f.write(tounicode(kgen_utils_array_sumcheck))
            f.write(tounicode(kgen_utils_file_tostr))
            f.write(tounicode(kgen_utils_file_checksubr))
            f.write(tounicode(kgen_get_newunit))
            f.write(tounicode(kgen_error_stop))
            f.write(tounicode(kgen_rankthread))
            f.write(tounicode("END MODULE kgen_utils_mod\n"))
