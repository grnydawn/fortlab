"""Microapp compiler inspector"""

import sys
import os
import subprocess

from microapp import App
from fortlab.compile import kgcompiler


STR_EX = b'execve('
STR_EN = b'ENOENT'
STR_UF = b'<unfinished'
STR_RE = b'resumed>'


class MicroappCompile(App):

    _name_ = "compile"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("buildcmd", metavar="build command", help="Software build command")
        self.add_argument("--cleancmd", type=str, help="Software clean command.")
        self.add_argument("--workdir", type=str, help="work directory")
        self.add_argument("--outdir", type=str, help="output directory")
        self.add_argument("--savejson", type=str, help="save data in a josn-format file")
        self.add_argument("--verbose", action="store_true", help="show compilation details")

        self.register_forward("data", help="json object")

    def perform(self, args):

        buildcmd = args.buildcmd["_"]

        cwd = orgcwd = os.getcwd()

        if args.workdir:
            cwd = args.workdir["_"]
            os.chdir(cwd)

        outdir = cwd
        if args.outdir:
            outdir = args.outdir["_"]

        if args.cleancmd:
            cleancmd_output = subprocess.check_output(args.cleancmd["_"], shell=True)

        # build with strace
   
        stracecmd = b'strace -f -q -s 100000 -e trace=execve -v -- /bin/sh -c "%s"'% str.encode(buildcmd)

        try:

            flags = {}

            process = subprocess.Popen(stracecmd, stdin=subprocess.PIPE, \
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, \
                        shell=True)

            while True:

                #line = process.stdout.readline()
                line = process.stderr.readline()

                if line == b'' and process.poll() is not None:
                    break

                if line:
                    pos_execve = line.find(STR_EX)
                    if pos_execve >= 0:
                        pos_enoent = line.rfind(STR_EN)
                        if pos_enoent < 0:
                            pos_last = line.rfind(STR_UF)
                            if pos_last < 0:
                                pos_last = line.rfind(b']')
                            else:
                                pos_last -= 1

                            if pos_last >= 0:
                                try:
                                    lenv = {}
                                    exec(b'exepath, cmdlist, env = %s'%line[pos_execve+len(STR_EX):(pos_last+1)], None, lenv)

                                    exepath = lenv["exepath"]
                                    cmdlist = lenv["cmdlist"]
                                    env = lenv["env"]

                                    compid = cmdlist[0].split('/')[-1]
                                    if exepath and cmdlist and compid==cmdlist[0].split('/')[-1]:
                                        compiler = kgcompiler.CompilerFactory.createCompiler(compid)
                                        if compiler:
                                            srcs, incs, macros, openmp, options = compiler.parse_option(cmdlist, self._getpwd(env))
                                            if len(srcs)>0:
                                                for src in srcs:
                                                    info = {"compiler": exepath, "include": incs,
                                                            "macros": macros, "openmp": openmp,
                                                            "options": options}
                                                    #flags[src] = (exepath, incs, macros, openmp, options)
                                                    flags[src] = info
                                                    if args.verbose:
                                                        print("Compiled: %s by %s" % (src, exepath))
                                                        print(str(options))

                                                    #if src in flags:
                                                    #    flags[src].append((exepath, incs, macros, openmp, options))
                                                    #else:
                                                    #    flags[src] = [ (exepath, incs, macros, openmp, options) ]
                                except Exception as err:
                                    raise
                                    pass

            # get return code
            retcode = process.poll()
                                         
        #except Exception as err:
        #    raise
        finally:
            pass

        if args.cleancmd:
            cleancmd_output = subprocess.check_output(args.cleancmd["_"], shell=True)

        self.add_forward(data=flags)
#
#                    if option=='include':
#                        pathlist = Inc.get(section, option).split(':')
#                        self.config["include"]['file'][realpath]['path'].extend(pathlist)
#                    elif option in [ 'compiler', 'compiler_options' ]:
#                        self.config["include"]['file'][realpath][option] = Inc.get(section, option)
#                    else:
#                        self.config["include"]['file'][realpath]['macro'][option] = Inc.get(section, option)
#

        if args.savejson:
            jsonfile = args.savejson["_"]
            cmd = ["dict2json", "@flags", "-o", jsonfile]
            self.manager.run_command(cmd, forward={"flags": flags})

        os.chdir(orgcwd)

    def _getpwd(self, env):
        for item in env:
            if item.startswith('PWD='):
                return item[4:]
        return None
