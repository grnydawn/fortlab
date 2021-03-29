# uncompyle6 version 3.7.2
# Python bytecode 2.7 (62211)
# Decompiled from: Python 3.6.9 (default, Apr 18 2020, 01:56:04)
# [GCC 8.4.0]
# Embedded file name: /home/grnydawn/repos/github/fortlab/fortlab/kernel/kernelgen.py
# Compiled at: 2020-07-13 10:26:24
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


class FortranKernelGenerator(App):
    _name_ = "kernelgen"
    _version_ = "0.1.0"

    def __init__(self, mgr):
        self.add_argument("analysis", help="analysis object")
        self.add_argument("--outdir", help="output directory")
        self.add_argument("--model", help="model object")

        self.add_argument("--repr-etime", dest="repr_etime", action='append', type=str, help="Specifying elapsedtime representativeness feature flags")
        self.add_argument("--repr-papi", dest="repr_papi", action='append', type=str, help="Specifying papi counter representativeness feature flags")
        self.add_argument("--repr-code", dest="repr_code", action='append', type=str, help="Specifying code coverage representativeness feature flags")

        self.register_forward("kerneldir", help="kernel generation code directory")
        self.register_forward("statedir", help="state generation code directory")

    def _process_repr_flags(self, opts):

        if opts.repr_etime:
            for line in opts.repr_etime:
                line = line["_"]
                for eopt in line.split(','):
                    split_eopt = eopt.split('=', 1)
                    if len(split_eopt)==1:
                        if split_eopt[0] == 'enable':
                            self.config['model']['types']['etime']['enabled'] = True
                        elif split_eopt[0] == 'disable':
                            self.config['model']['types']['etime']['enabled'] = False
                        else:
                            raise UserException('Unknown elapsed-time flag option: %s' % eopt)
                    elif len(split_eopt)==2:

                        self.config['model']['types']['etime']['enabled'] = True

                        if split_eopt[0] in [ 'minval', 'maxval' ]:
                            self.config['model']['types']['etime'][split_eopt[0]] = float(split_eopt[1])
                        elif split_eopt[0] in ('nbins', 'ndata'):
                            self.config['model']['types']['etime'][split_eopt[0]] = int(split_eopt[1])
                        elif split_eopt[0] in ('timer', ):
                            self.config['model']['types']['etime'][split_eopt[0]] = split_eopt[1]
                        else:
                            raise UserException('Unknown elapsed-time flag option: %s' % eopt)

        if opts.repr_papi:
            for line in opts.repr_papi:
                line = line["_"]
                for popt in line.split(','):
                    split_popt = popt.split('=', 1)
                    if len(split_popt)==1:
                        if split_popt[0] == 'enable':
                            self.config['model']['types']['papi']['enabled'] = True
                        elif split_popt[0] == 'disable':
                            self.config['model']['types']['papi']['enabled'] = False
                        else:
                            raise UserException('Unknown papi-counter flag option: %s' % popt)
                    elif len(split_popt)==2:

                        self.config['model']['types']['papi']['enabled'] = True

                        if split_popt[0] in [ 'minval', 'maxval', 'header', 'static', 'dynamic', 'event' ]:
                            self.config['model']['types']['papi'][split_popt[0]] = split_popt[1]
                        elif split_popt[0] in ('nbins', 'ndata'):
                            self.config['model']['types']['papi'][split_popt[0]] = int(split_popt[1])
                        else:
                            raise UserException('Unknown papi-counter flag option: %s' % popt)
        if opts.repr_code:
            for line in opts.repr_code:
                line = line["_"]
                for copt in line.split(','):
                    split_copt = copt.split('=', 1)
                    if len(split_copt)==1:
                        if split_copt[0] == 'enable':
                            self.config['model']['types']['code']['enabled'] = True
                        elif split_copt[0] == 'disable':
                            self.config['model']['types']['code']['enabled'] = False
                        else:
                            raise UserException('Unknown code-coverage flag option: %s' % copt)
                    elif len(split_copt)==2:

                        self.config['model']['types']['code']['enabled'] = True

                        if split_copt[0] in [ 'percentage' ]:
                            self.config['model']['types']['code'][split_copt[0]] = float(split_copt[1])
                        elif split_copt[0] in [ 'filter' ]:
                            self.config['model']['types']['code'][split_copt[0]] = split_copt[1].strip().split(':')
                        elif split_copt[0] in ( 'ndata' ):
                            self.config['model']['types']['code'][split_popt[0]] = int(split_copt[1])
                        else:
                            raise UserException('Unknown code-coverage flag option: %s' % copt)

            # enable coverage feature at extractor
            #if self.config['model']['types']['code']['enabled']:
            #    self.config['plugin']['priority']['ext.coverage'] = '%s/plugins/coverage'%KGEN_EXT

    def perform(self, args):

        self.config = args.analysis["_"]

        # process representativeness flags
        self._process_repr_flags(args)

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

        self.add_forward(kerneldir=kernel_realpath, statedir=state_realpath)

        if not os.path.exists(kernel_realpath):
            os.makedirs(kernel_realpath)

        if not os.path.exists(state_realpath):
            os.makedirs(state_realpath)

        state_makefile = os.path.realpath(os.path.join(state_realpath, "Makefile"))
        kernel_makefile = os.path.realpath(os.path.join(kernel_realpath, "Makefile"))
        gencore_plugindir = os.path.join(here, "plugins", "gencore")
        verify_plugindir = os.path.join(here, "plugins", "verification")
        timing_plugindir = os.path.join(here, "plugins", "simple_timing")
        perturb_plugindir = os.path.join(here, "plugins", "perturb")

        if args.model:
            try:
                if os.path.exists(args.model["_"]):
                    with open(args.model["_"]) as f:
                        self.read_model(json.load(f), self.config)
            except:
                self.read_model(args.model["_"], self.config)
        else:
            self.config["invocation"]["triples"].append(
                (("0", "0"), ("0", "0"), ("1", "1"))
            )

        plugins = (
            ("ext.gencore", gencore_plugindir),
            ("ext.verification", verify_plugindir),
            ("ext.simple_timing", timing_plugindir),
            ("ext.perturb", perturb_plugindir),
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
            if sfile.kgen_stmt.used4genstate:
                set_indent("")
                slines = sfile.tostring()
                if slines is not None:
                    slines = remove_multiblanklines(slines)
                    state_files.append(filename)
                    with io.open(
                        os.path.join(state_realpath, filename), "w", encoding=enc
                    ) as (fd):
                        fd.write(tounicode(slines))

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
        self.generate_kernel_makefile(kernel_realpath, enc)
        kernel_files.append("Makefile")
        self.generate_state_makefile(state_realpath, enc)
        state_files.append("Makefile")

        if self.config["cmd_clean"]["cmds"]:
            run_shcmd(self.config["cmd_clean"]["cmds"])

        if self.config["state_switch"]["clean"]:
            run_shcmd(self.config["state_switch"]["clean"])

        out, err, retcode = run_shcmd("make", cwd=state_realpath)

        if retcode != 0:
            print("ERROR: state make error")

        out, err, retcode = run_shcmd("make recover", cwd=state_realpath)

        if retcode != 0:
            print("ERROR: state recover error")

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

    def write(self, f, line, n=True, t=False):
        nl = ""
        tab = ""
        if n:
            nl = "\n"
        if t:
            tab = "\t"
        f.write(tounicode(tab + line + nl))

    def obj(self, file):
        l = file.split(".")
        if len(l) > 1:
            l[-1] = "o"
        return (".").join(l)

    def generate_kernel_makefile(self, kernelpath, enc):
        openmp_flags = ["-fopenmp", "-qopenmp", "-mp", "-xopenmp", "-qsmp=omp"]
        callsite_base = os.path.basename(self.config["callsite"]["filepath"])
        driver_base = "%s.f90" % self.config["kernel_driver"]["name"]
        dep_base_srcfiles = [
            os.path.basename(filepath)
            for filepath, srclist in self.config["used_srcfiles"].items()
        ]
        dep_bases = dep_base_srcfiles + [driver_base]
        all_objs_srcfiles = [
            self.obj(dep_base_srcfile) for dep_base_srcfile in dep_base_srcfiles
        ]
        all_objs = all_objs_srcfiles + [self.obj(driver_base), self.obj(KGUTIL)]
        depends = OrderedDict()
        depends[driver_base] = (" ").join(all_objs_srcfiles + [self.obj(KGUTIL)])
        for filepath, (kfile, sfile, mods_used, units_used) in self.config[
            "used_srcfiles"
        ].items():
            dep = [self.obj(KGUTIL)]
            for mod in mods_used:
                if (
                    mod.reader.id != filepath
                    and self.obj(os.path.basename(mod.reader.id)) not in dep
                ):
                    dep.append(self.obj(os.path.basename(mod.reader.id)))

            for unit in units_used:
                if (
                    unit.item.reader.id != filepath
                    and self.obj(os.path.basename(unit.item.reader.id)) not in dep
                ):
                    dep.append(self.obj(os.path.basename(unit.item.reader.id)))

            basename = os.path.basename(filepath)
            if basename == callsite_base:
                dobjs = all_objs[:]
                dobjs.remove(self.obj(callsite_base))
                dobjs.remove(self.obj(driver_base))
                depends[basename] = (" ").join(dobjs)
            else:
                depends[basename] = (" ").join(dep)

        compilers = OrderedDict()
        compiler_options = OrderedDict()
        for path, kfile in self.config["include"]["file"].items():
            base = os.path.basename(path)
            if base not in dep_bases:
                continue
            comp = None
            if "compiler" in kfile:
                comp = kfile["compiler"]
            elif "compiler" in self.config["include"]["compiler"]:
                comp = self.config["include"]["compiler"]["compiler"]
            if comp:
                if comp in compilers:
                    if base not in compilers[comp]:
                        compilers[comp].append(base)
                else:
                    compilers[comp] = [base, driver_base]
            opts = ""
            if "compiler_options" in self.config["include"]["compiler"]:
                opts = (
                    opts + " " + self.config["include"]["compiler"]["compiler_options"]
                )
            if "compiler_options" in kfile and kfile["compiler_options"]:
                opts = opts + " " + kfile["compiler_options"]
            if self.config["model"]["types"]["code"]["enabled"]:
                if comp:
                    compname = os.path.basename(comp)
                    if compname == "ifort":
                        opts += " -fpp "
                    elif compname == "gfortran":
                        opts += " -cpp "
                    elif compname.startswith("pg"):
                        opts += " -Mpreprocess "
                opts += ' -D KGEN_COVERAGE # Comment out "-D KGEN_COVERAGE" to turn off coverage feature.'
            if self.config["add_mpi_frame"]["enabled"]:
                if comp:
                    compname = os.path.basename(comp)
                    if compname == "ifort" and "-fpp" not in opts:
                        opts += " -fpp "
                    elif compname == "gfortran" and "-cpp" not in opts:
                        opts += " -cpp "
                    elif compname.startswith("pg") and "-Mpreprocess" not in opts:
                        opts += " -Mpreprocess "
                    opts += " -D_MPI "
            if len(opts) > 0:
                if opts in compiler_options:
                    if base not in compiler_options[opts]:
                        compiler_options[opts].append(base)
                else:
                    compiler_options[opts] = [base, driver_base]

        link_flags = (" ").join(self.config["kernel_option"]["linker"]["add"])
        objects = ""
        if "import" in self.config["include"]:
            for path, import_type in self.config["include"]["import"].items():
                if import_type == "library" or import_type == "shared_library":
                    inc = "-L" + path
                    pos1 = import_type.find("(")
                    pos2 = import_type.find(")")
                    lib = "-l" + import_type[pos1 + 1 : pos2].strip()
                    link_flags += " %s %s" % (inc, lib)
                elif import_type == "static-library":
                    link_flags += " %s" % path
                elif import_type == "object":
                    objects += " %s" % os.path.basename(path)
                    shutil.copy(
                        path,
                        "%s/%s"
                        % (
                            self.config["path"]["outdir"],
                            self.config["path"]["kernel"],
                        ),
                    )

        with io.open(os.path.join(kernelpath, "Makefile"), "w", encoding=enc) as (f):
            self.write(f, "# Makefile for KGEN-generated kernel")
            self.write(f, "")
            if self.config["kernel_option"]["FC"]:
                self.write(f, "FC_0 := %s" % self.config["kernel_option"]["FC"])
            else:
                if self.config["add_mpi_frame"]["enabled"]:
                    self.write(f, "# Originally used compiler(s)")
                    for i, compiler in enumerate(compilers):
                        self.write(f, "#FC_%d := %s" % (i, compiler))

                    self.write(f, "FC_0 := %s" % self.config["add_mpi_frame"]["mpifc"])
                else:
                    for i, compiler in enumerate(compilers):
                        self.write(f, "FC_%d := %s" % (i, compiler))

                if self.config["kernel_option"]["FC_FLAGS"]:
                    self.write(
                        f,
                        "FC_FLAGS_SET_0 := %s"
                        % self.config["kernel_option"]["FC_FLAGS"],
                    )
                else:
                    for i, options in enumerate(compiler_options):
                        opt_list = options.split()
                        L = len(opt_list)
                        new_options = []
                        if L > 1:
                            skip_next = False
                            for opt in opt_list:
                                if skip_next:
                                    skip_next = False
                                    continue
                                if (
                                    opt
                                    in self.config["kernel_option"]["compiler"][
                                        "remove"
                                    ]
                                ):
                                    pass
                                elif (
                                    "%s+" % opt
                                    in self.config["kernel_option"]["compiler"][
                                        "remove"
                                    ]
                                ):
                                    skip_next = True
                                elif opt not in openmp_flags:
                                    new_options.append(opt)

                        for add_opt in self.config["kernel_option"]["compiler"]["add"]:
                            if add_opt not in new_options:
                                new_options.append(add_opt)

                        self.write(
                            f, "FC_FLAGS_SET_%d := %s" % (i, (" ").join(new_options))
                        )

            prerun_build_str = ""
            if (
                self.config["prerun"]["kernel_build"]
                or self.config["prerun"]["build"]
                or self.config["prerun"]["kernel_run"]
                or self.config["prerun"]["run"]
            ):
                self.write(
                    f,
                    "# Comment-out below if your system environment is different from one that this kernel is extracted from.",
                )
                self.write(
                    f,
                    "# NOTE: the environment is valid only if you are using this kernel on the same computing system that the kernel was extracted from.",
                )
            if self.config["prerun"]["kernel_build"]:
                self.write(
                    f, "PRERUN_BUILD := %s; " % self.config["prerun"]["kernel_build"]
                )
                prerun_build_str = "${PRERUN_BUILD}"
            elif self.config["prerun"]["build"]:
                self.write(f, "PRERUN_BUILD := %s; " % self.config["prerun"]["build"])
                prerun_build_str = "${PRERUN_BUILD}"
            prerun_run_str = ""
            if self.config["prerun"]["kernel_run"]:
                self.write(
                    f, "PRERUN_RUN := %s; " % self.config["prerun"]["kernel_run"]
                )
                prerun_run_str = "${PRERUN_RUN}"
            else:
                if self.config["prerun"]["run"]:
                    self.write(f, "PRERUN_RUN := %s; " % self.config["prerun"]["run"])
                    prerun_run_str = "${PRERUN_RUN}"
                self.write(f, "")
                self.write(f, "ALL_OBJS := %s" % (" ").join(all_objs))
                self.write(f, "")
                if self.config["model"]["types"]["papi"]["enabled"]:
                    self.write(
                        f,
                        "PAPI_EVENT := %s"
                        % self.config["model"]["types"]["papi"]["event"],
                    )
                    self.write(f, "")
                self.write(f, "build: ${ALL_OBJS}")
                fc_str = "FC_0"
                fc_flags_str = "FC_FLAGS_SET_0"
                self.write(
                    f,
                    "%s${%s} ${%s} -o kernel.exe $^ %s %s"
                    % (prerun_build_str, fc_str, fc_flags_str, link_flags, objects),
                    t=True,
                )
                self.write(f, "")
                self.write(f, "run: build")
                if self.config["add_mpi_frame"]["enabled"]:
                    self.write(
                        f,
                        "%s%s -np %s ./kernel.exe"
                        % (
                            prerun_run_str,
                            self.config["add_mpi_frame"]["mpirun"],
                            self.config["add_mpi_frame"]["np"],
                        ),
                        t=True,
                    )
                else:
                    self.write(f, "%s./kernel.exe" % prerun_run_str, t=True)
                self.write(f, "")
                if self.config["model"]["types"]["papi"]["enabled"]:
                    self.write(f, "papi: build-papi")
                    if self.config["add_mpi_frame"]["enabled"]:
                        self.write(
                            f,
                            "%s%s -np %s ./kernel.exe"
                            % (
                                prerun_run_str,
                                self.config["add_mpi_frame"]["mpirun"],
                                self.config["add_mpi_frame"]["np"],
                            ),
                            t=True,
                        )
                    else:
                        self.write(f, "%s./kernel.exe" % prerun_run_str, t=True)
                    self.write(f, "")
                if self.config["model"]["types"]["papi"]["enabled"]:
                    self.write(f, "build-papi: ${ALL_OBJS}")
                    fc_str = "FC_0"
                    fc_flags_str = "FC_FLAGS_SET_0"
                    if self.config["model"]["types"]["papi"]["static"] is not None:
                        link_flags += (
                            " %s" % self.config["model"]["types"]["papi"]["static"]
                        )
                    if self.config["model"]["types"]["papi"]["dynamic"] is not None:
                        ddir, dlib = os.path.split(
                            self.config["model"]["types"]["papi"]["dynamic"]
                        )
                        root, ext = dlib.split(".", 1)
                        if len(root) > 3:
                            link_flags += " -L%s -l%s" % (ddir, root[3:])
                    self.write(
                        f,
                        "%s${%s} ${%s} -o kernel.exe $^ %s %s"
                        % (prerun_build_str, fc_str, fc_flags_str, link_flags, objects),
                        t=True,
                    )
                    self.write(f, "")
                for dep_base in dep_bases:
                    self.write(
                        f,
                        "%s: %s %s" % (self.obj(dep_base), dep_base, depends[dep_base]),
                    )
                    dfc_str = "FC"
                    dfc_flags_str = "FC_FLAGS"
                    if self.config["kernel_option"]["FC"] is None:
                        for i, (compiler, files) in enumerate(compilers.items()):
                            if dep_base in files:
                                dfc_str += "_%d" % i
                                break

                    if self.config["kernel_option"]["FC_FLAGS"] is None:
                        for i, (compiler_option, files) in enumerate(
                            compiler_options.items()
                        ):
                            if dep_base in files:
                                dfc_flags_str += "_SET_%d" % i
                                break

                    if dfc_str == "FC" or self.config["add_mpi_frame"]["enabled"]:
                        dfc_str = "FC_0"
                    if dfc_flags_str == "FC_FLAGS":
                        dfc_flags_str = "FC_FLAGS_SET_0"
                    if (
                        self.config["model"]["types"]["papi"]["enabled"]
                        and self.config["model"]["types"]["papi"]["header"] is not None
                        and dep_base in [callsite_base, driver_base]
                    ):
                        self.write(f, "ifeq (${MAKECMDGOALS}, papi)")
                        papi_flags_str = (
                            " -DKGEN_PAPI -I%s"
                            % os.path.split(
                                self.config["model"]["types"]["papi"]["header"]
                            )[0]
                        )
                        self.write(
                            f,
                            '%s %s %s $< | sed "s/KGENPAPIEVENT/${PAPI_EVENT}/g" > tmp.$<'
                            % (
                                self.config["bin"]["pp"],
                                self.config["bin"]["cpp_flags"],
                                papi_flags_str,
                            ),
                            t=True,
                        )
                        self.write(f, "else")
                        self.write(
                            f,
                            "%s %s $< tmp.$<"
                            % (
                                self.config["bin"]["pp"],
                                self.config["bin"]["cpp_flags"],
                            ),
                            t=True,
                        )
                        self.write(f, "endif")
                        self.write(
                            f,
                            "%s${%s} ${%s} -c -o $@ tmp.$<"
                            % (prerun_build_str, dfc_str, dfc_flags_str),
                            t=True,
                        )
                        self.write(f, "rm -f tmp.$<", t=True)
                    else:
                        self.write(
                            f,
                            "%s${%s} ${%s} -c -o $@ $<"
                            % (prerun_build_str, dfc_str, dfc_flags_str),
                            t=True,
                        )
                    self.write(f, "")

            self.write(f, "%s: %s" % (self.obj(KGUTIL), KGUTIL))
            self.write(
                f,
                "%s${%s} ${%s} -c -o $@ $<" % (prerun_build_str, fc_str, fc_flags_str),
                t=True,
            )
            self.write(f, "")
            self.write(
                f,
                "%s${%s} ${%s} -c -o $@ $<" % (prerun_build_str, fc_str, fc_flags_str),
                t=True,
            )
            self.write(f, "")
            self.write(f, "clean:")
            self.write(f, "rm -f kernel.exe *.mod ${ALL_OBJS}", t=True)
        return

    def generate_state_makefile(self, statepath, enc):

        org_files = [
            filepath
            for filepath, (kfile, sfile, mods_used, units_used) in self.config[
                "used_srcfiles"
            ].items()
            if sfile.kgen_stmt.used4genstate
        ]
        if self.config["topblock"]["stmt"].reader.id not in org_files:
            org_files.append(self.config["topblock"]["filepath"])
        with io.open(os.path.join(statepath, "Makefile"), "w", encoding=enc) as (f):
            self.write(f, "# Makefile for KGEN-generated instrumentation")
            self.write(f, "")
            cwd = os.path.realpath(self.config["cwd"])
            prerun_build_str = ""
            if self.config["prerun"]["build"]:
                self.write(f, "PRERUN_BUILD := %s" % self.config["prerun"]["build"])
                prerun_build_str = "${PRERUN_BUILD}; "
            prerun_run_str = ""
            if self.config["prerun"]["run"]:
                self.write(f, "PRERUN_RUN := %s" % self.config["prerun"]["run"])
                prerun_run_str = "${PRERUN_RUN}; "
            self.write(f, "")
            if len(self.config["cmd_run"]["cmds"]) > 0:
                self.write(f, "run: build")
                self.write(
                    f,
                    "%scd %s; %s"
                    % (prerun_run_str, cwd, self.config["cmd_run"]["cmds"]),
                    t=True,
                )
            else:
                self.write(
                    f,
                    "echo \"No information is provided to run. Please specify run commands using 'state-run' command line option\"; exit -1",
                    t=True,
                )
            self.write(f, "")
            if len(self.config["cmd_build"]["cmds"]) > 0:
                self.write(f, "build: %s" % self.config["state_switch"]["type"])
                self.write(
                    f,
                    "%scd %s; %s"
                    % (prerun_build_str, cwd, self.config["cmd_build"]["cmds"]),
                    t=True,
                )
                for org_file in org_files:
                    self.write(
                        f, "mv -f %(f)s.kgen_org %(f)s" % {"f": org_file}, t=True
                    )

            else:
                self.write(
                    f,
                    "echo \"No information is provided to build. Please specify build commands using 'state-build' command line option\"; exit -1",
                    t=True,
                )
            self.write(f, "")
            self.write(f, "%s: save" % self.config["state_switch"]["type"])
            if self.config["state_switch"]["type"] == "replace":
                for org_file in org_files:
                    basename = os.path.basename(org_file)
                    self.write(f, "rm -f %s" % org_file, t=True)
                    self.write(
                        f,
                        "cp -f %(f1)s %(f2)s" % {"f1": basename, "f2": org_file},
                        t=True,
                    )

            elif self.config["state_switch"]["type"] == "copy":
                for org_file in org_files:
                    basename = os.path.basename(org_file)
                    self.write(
                        f,
                        "rm -f %s/%s"
                        % (self.config["state_switch"]["directory"], basename),
                        t=True,
                    )
                    self.write(
                        f,
                        "cp -f %s/%s/%s %s"
                        % (
                            self.config["path"]["outdir"],
                            self.config["path"]["state"],
                            basename,
                            self.config["state_switch"]["directory"],
                        ),
                        t=True,
                    )

            self.write(f, "")
            self.write(f, "recover:")
            for org_file in org_files:
                self.write(f, "rm -f %s" % org_file, t=True)
                self.write(
                    f,
                    "cp -f %s.kgen_org %s" % (os.path.basename(org_file), org_file),
                    t=True,
                )

            self.write(f, "")
            self.write(f, "recover_from_srcdir:")
            for org_file in org_files:
                self.write(f, "rm -f %s" % org_file, t=True)
                self.write(f, "cp -f %(f)s.kgen_org %(f)s" % {"f": org_file}, t=True)

            self.write(f, "")
            self.write(f, "save:")
            for org_file in org_files:
                self.write(
                    f,
                    "if [ ! -f %(f)s.kgen_org ]; then cp -f %(f)s %(f)s.kgen_org; fi"
                    % {"f": org_file},
                    t=True,
                )
                self.write(
                    f,
                    "if [ ! -f %(g)s.kgen_org ]; then cp -f %(f)s %(g)s.kgen_org; fi"
                    % {"f": org_file, "g": os.path.basename(org_file)},
                    t=True,
                )

            self.write(f, "")
            if len(self.config["cmd_clean"]["cmds"]) > 0:
                self.write(f, "clean:")
                self.write(f, "%s" % self.config["cmd_clean"]["cmds"], t=True)
            self.write(f, "")

    def read_model(self, modeljson, config):

        if "etime" not in modeljson:
            raise UserException("'etime' is not in model json file")

        emeta = modeljson["etime"]["_summary_"]
        del modeljson["etime"]["_summary_"]
        etimes = modeljson["etime"]

        try:
            etimemin = emeta["elapsedtime_min"]
            etimemax = emeta["elapsedtime_max"]
            netimes = emeta["number_eitmes"]
            etimediff = etimemax - etimemin
            etimeres = emeta["elapsedtime_res"]
            if etimediff == 0:
                nbins = 1
            else:
                nbins = max(min(config["model"]["types"]["etime"]["nbins"], netimes), 2)
            if nbins > 1:
                etimebins = [{} for _ in range(nbins)]
                etimecounts = [0 for _ in range(nbins)]
            else:
                etimebins = [{}]
                etimecounts = [0]
            idx = 0
            for ranknum, d1 in etimes.items():
                for threadnum, d2 in d1.items():
                    for invokenum, (start, stop) in d2.items():

            #for opt in cfg.options("elapsedtime.elapsedtime"):
            #    ranknum, threadnum, invokenum = tuple(num for num in opt.split())
            #    start, stop = cfg.get("elapsedtime.elapsedtime", opt).split(",")
                        estart = float(start)
                        eend = float(stop)
                        etimeval = eend - estart
                        if nbins > 1:
                            binnum = int(
                                math.floor((etimeval - etimemin) / etimediff * (nbins - 1))
                            )
                        else:
                            binnum = 0
                        etimecounts[binnum] += 1
                        invokenum = int(invokenum)
                        if invokenum not in etimebins[binnum]:
                            etimebins[binnum][invokenum] = {}
                        if ranknum not in etimebins[binnum][invokenum]:
                            etimebins[binnum][invokenum][ranknum] = {}
                        if threadnum not in etimebins[binnum][invokenum][ranknum]:
                            etimebins[binnum][invokenum][ranknum][threadnum] = float(etimeval)
                        else:
                            raise Exception(
                                "Dupulicated data: (%s, %s, %s, %s)"
                                % (invokenum, ranknum, threadnum, etimeval)
                            )
                        idx += 1
                        if idx % 100000 == 0:
                            print(
                                "Processed %d items: %s"
                                % (
                                    idx,
                                    datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"),
                                )
                            )

        except Exception as e:
            raise Exception("Please check the format of elapsedtime file: %s" % str(e))

        totalcount = sum(etimecounts)
        countdist = [float(count) / float(totalcount) for count in etimecounts]
        ndata = config["model"]["types"]["etime"]["ndata"]
        datacollect = [int(round(dist * ndata)) for dist in countdist]
        triples = []
        for binnum, etimebin in enumerate(etimebins):
            bin_triples = []
            range_begin = (
                binnum * (etimemax - etimemin) / nbins + etimemin
                if binnum > 0
                else etimemin
            )
            range_end = (
                (binnum + 1) * (etimemax - etimemin) / nbins + etimemin
                if binnum < nbins - 1
                else None
            )
            bunit = "sec"
            if range_begin < 1e-06:
                bunit = "usec"
                range_begin *= 1000000.0
            if range_end is None:
                print(
                    "From bin # %d [ %f (%s) ~ ] %f %% of %d"
                    % (binnum, range_begin, bunit, countdist[binnum] * 100, totalcount)
                )
            else:
                eunit = "sec"
                if range_end < 1e-06:
                    eunit = "usec"
                    range_end *= 1000000.0
                print(
                    "From bin # %d [ %f (%s) ~ %f (%s) ] %f %% of %d"
                    % (
                        binnum,
                        range_begin,
                        bunit,
                        range_end,
                        eunit,
                        countdist[binnum] * 100,
                        totalcount,
                    )
                )
            for invokenum in sorted(etimebin.keys()):
                if len(bin_triples) >= datacollect[binnum]:
                    break
                bininvokes = list(etimebin[invokenum].keys())
                random.shuffle(bininvokes)
                for ranknum in bininvokes:
                    if len(bin_triples) >= datacollect[binnum]:
                        break
                    binranks = list(etimebin[invokenum][ranknum].keys())
                    random.shuffle(binranks)
                    for threadnum in binranks:
                        bin_triples.append((ranknum, threadnum, invokenum))
                        print(
                            "        invocation triple: %s:%s:%s"
                            % (ranknum, threadnum, invokenum)
                        )

            triples.extend(bin_triples)

        print("Number of bins: %d" % nbins)
        print("Minimun elapsed time: %f" % etimemin)
        print("Maximum elapsed time: %f" % etimemax)
        for ranknum, threadnum, invokenum in triples:
            config["invocation"]["triples"].append(
                (
                    (str(ranknum), str(ranknum)),
                    (str(threadnum), str(threadnum)),
                    (str(invokenum), str(invokenum)),
                )
            )

        return


# okay decompiling kernelgen.pyc
