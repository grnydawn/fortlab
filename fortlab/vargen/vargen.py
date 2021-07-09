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
        varlist_plugindir = os.path.join(here, "plugins", "genvarlist")

        plugins = (
            ("ext.gencore", gencore_plugindir),
            ("ext.genvarlist", varlist_plugindir),
        )

        init_plugins([KERNEL_ID_0], plugins, self.config)
        plugin_config["current"].update(self.config)

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

        if self.config["state_switch"]["clean"]:
            run_shcmd(self.config["state_switch"]["clean"])

        return
