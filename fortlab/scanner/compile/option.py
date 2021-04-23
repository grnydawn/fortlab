"""Microapp compiler flag inspector"""

import sys
import os
import re
import io
import shutil
import time
import subprocess
import multiprocessing

from microapp import App
from fortlab.scanner.compile import kgcompiler


STR_EX = b'execve('
STR_EN = b'ENOENT'
STR_UF = b'<unfinished'
STR_RE = b'resumed>'

RE_INCLUDE = re.compile(r'(\A|^)#include\s+(\'|")(?P<name>(\w|\.)+)(\'|")\s*(!.*|)$',re.I | re.M)

class FortranCompilerOption(App):

    _name_ = "compileroption"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("buildcmd", metavar="build command", help="Software build command")
        self.add_argument("--cleancmd", type=str, help="Software clean command.")
        self.add_argument("--workdir", type=str, help="work directory")
        self.add_argument("--savejson", type=str, help="save data in a josn-format file")
        self.add_argument("--backupdir", type=str, help="saving source files used")
        self.add_argument("--verbose", action="store_true", help="show compilation details")
        self.add_argument("--check", action="store_true", help="check strace return code")

        self.register_forward("data", help="json object")

    def perform(self, args):

        buildcmd = args.buildcmd["_"]


        cwd = orgcwd = os.getcwd()

        if args.workdir:
            cwd = args.workdir["_"]
            os.chdir(cwd)

        if args.cleancmd:
            cleancmd_output = subprocess.check_output(args.cleancmd["_"], shell=True)

        if args.backupdir:
            backupdir = args.backupdir["_"]

        else:
            backupdir = os.path.join(os.getcwd(), "backup", "src")

        if not os.path.exists(backupdir):
            os.makedirs(backupdir)

        inq = multiprocessing.Queue()
        outq = multiprocessing.Queue()
        proc = multiprocessing.Process(target=self.get_includes, args=(backupdir, inq, outq))
        proc.start()

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
                                                    #flags[src] = (exepath, incs, macros, openmp, options)
                                                    flags[src] = {"compiler": exepath, "include": incs,
                                                            "macros": macros, "openmp": openmp,
                                                            "options": options, "srcbackup": []}

                                                    if backupdir:
                                                        if os.path.isfile(src):
                                                            inq.put((src, incs))

                                                        else:
                                                            print("Warning: %s is not backuped" % src)

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

            inq.put(None)

            # get return code
            retcode = process.poll()
                                         
            if args.check and retcode != 0:
                raise Exception("strace returned non-zero value: %d" % retcode)

            backupsrcs = outq.get()

            proc.join()


        #except Exception as err:
        #    raise
        finally:
            pass

        #if args.cleancmd:
        #    cleancmd_output = subprocess.check_output(args.cleancmd["_"], shell=True)

        for fname, backups in backupsrcs.items():
            flags[fname]["srcbackup"].extend(backups)

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
            dirname = os.path.dirname(jsonfile)

            if not os.path.exists(dirname):
                os.makedirs(dirname)

            #cmd = ["dict2json", "@flags", "-o", jsonfile]
            opts = ["@flags", "-o", jsonfile]
            #self.manager.run_command(cmd, forward={"flags": flags})
            ret, fwds = self.run_subapp("dict2json", opts, forward={"flags": flags})
            assert ret == 0, "dict2json returned non-zero code."

        os.chdir(orgcwd)

    def _getpwd(self, env):
        for item in env:
            if item.startswith('PWD='):
                return item[4:]
        return None

    def get_includes(self, outdir, inq, outq):

        data = {}

        srcnum = 0

        if not os.path.isdir(outdir):
            os.makedirs(outdir)

        while(True):
            if inq.empty():
                time.sleep(0.001)

            else:
                srcincs = inq.get()

                if srcincs is None:
                    break

                else:
                    self._backup(outdir, srcnum, srcincs, data)
                    srcnum += 1

        outq.put(data)

    def _backup(self, outdir, srcnum, srcincs, data):

        path, incs = srcincs

        backup = os.path.join(outdir, str(srcnum))
        shutil.copy(path, backup)
        data[path] = [backup]

        dirname = os.path.dirname(path)
        incs.insert(0, dirname)

        with io.open(path,'r', encoding="utf-8") as f:
            lines = f.read()

            for incidx, match in enumerate(RE_INCLUDE.findall(lines)):
                incfilename = match[2].strip()

                for incdir in incs: 
                    incsrc = os.path.join(incdir, incfilename)

                    if os.path.isfile(incsrc):
                        incbackup = os.path.join(outdir, "%d-%d" % (srcnum, incidx))
                        shutil.copy(incsrc, incbackup)
                        data[path].append((incsrc, incbackup))
                        break
