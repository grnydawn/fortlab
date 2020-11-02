
import os, shutil, platform

from fortlab import Fortlab

here = os.path.dirname(os.path.abspath(__file__))
node = platform.node()

def test_tulip(capsys):

    if node != "tulip":
        return

    prj = Fortlab()

    mpidir = "/home/groups/coegroup/e3sm/soft/openmpi/2.1.6/gcc/8.2.0"

    # ./cime/scripts/create_test SMS_P12x2.ne4_oQU240.A_WCYCL1850
    #/home/users/coe0165/repos/github/E3SM/components/eam/src/physics/cam/
    #/home/users/coe0165/repos/github/E3SM/components/eam/src/physics/cam/micro_mg_cam.F90
    #/home/users/coe0165/repos/github/E3SM/components/eam/src/physics/cam/micro_mg_cam.F90
    e3smdir = "/home/users/coe0165/repos/github/E3SM"
    #casedir = "/home/groups/coegroup/e3sm/scratch/coe0165/SMS_P12x2.ne4_oQU240.A_WCYCL1850.tulip_gnu.20200918_134511_d1oute"
    casedir = "/home/groups/coegroup/e3sm/scratch/coe0165/SMS_P12x2.ne4_oQU240.A_WCYCL1850.tulip_gnu.20200930_144757_0y89r2"
    outdir = "/home/groups/coegroup/coe0165/kernels/tulip/SMS_P12x2.ne4_oQU240.A_WCYCL1850"

    outfile = os.path.join(outdir, "model.json")
    
    
    callsitefile = os.path.join(e3smdir, "components/eam/src/physics/cam/micro_mg_cam.F90")
    callsitepath = "micro_mg_cam:micro_mg_cam_tend:micro_mg_tend2_0"
    patchfile = os.path.join(here, "res", "micro_mg_utils.F90")
    patchpath = os.path.join(e3smdir, "components/eam/src/physics/cam")
    compjson = os.path.join(outdir, "compile.json")
    analysisjson = os.path.join(outdir, "analysis.json")
    cleancmd = "cd %s; ./case.build --clean-all" % casedir 
    buildcmd = "cd %s; ./case.build" % casedir
    runcmd = "cd %s; ./case.submit" % casedir

    # copy patch file to workaround fparser bug of parsing array constructor using "[", "]"
    shutil.copy(patchfile, patchpath)

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    #Summit cmd = "--shell 'module load gcc' --logging debug"
    #cmd = "--logging debug"
#    cmd = ""
#    cmd += " -- buildscan '%s' --cleancmd '%s' --savejson '%s' --reuse '%s'  --verbose" % (
#            buildcmd, cleancmd, compjson, compjson)
#    cmd += " -- resolve --compile-info '@data' '%s'" % callsitefile + ":" + callsitepath
#    cmd += " -- runscan '@analysis' -s 'timing' --outdir '%s' --cleancmd '%s' --buildcmd '%s' --runcmd '%s' --output '%s'" % (
#                outdir, cleancmd, buildcmd, runcmd, outfile)
#    cmd += " -- kernelgen '@analysis' --outdir '%s'" % outdir
#    ret, fwds = prj.run_command(cmd)
#
#    assert ret == 0

    cmd = " -- buildscan '%s' --cleancmd '%s' --savejson '%s' --reuse '%s'  --verbose" % (
            buildcmd, cleancmd, compjson, compjson)
    ret, fwds = prj.run_command(cmd)

    assert ret == 0

    #cmd = " -- resolve --compile-info '@data' '%s'" % callsitefile + ":" + callsitepath
    rescmd = (" -- resolve --mpi header='%s/include/mpif.h' --openmp enable"
             " --compile-info '%s' --keep '%s' '%s'" % (
            mpidir, compjson, analysisjson, callsitefile + ":" + callsitepath))
    #ret, fwds = prj.run_command(cmd)
    #assert ret == 0

    cmd = rescmd + " -- runscan '@analysis' -s 'timing' --outdir '%s' --cleancmd '%s' --buildcmd '%s' --runcmd '%s' --output '%s'" % (
                outdir, cleancmd, buildcmd, runcmd, outfile)
    #ret, fwds = prj.run_command(cmd)

    #import pdb; pdb.set_trace()
    # add model config to analysis

    cmd = cmd + " -- kernelgen '@analysis' --model '@model' --repr-etime 'ndata=40,nbins=10'  --outdir '%s'" % outdir
    ret, fwds = prj.run_command(cmd)

    assert ret == 0

    #ret, fwds = prj.run_command("shell '%s'" % cleancmd)

    #assert ret == 0

    #cmd = "shell 'cd %s; make; make recover; cd %s; make clean' --useenv" % (fwds["etimedir"], workdir)
    #ret, fwds = prj.run_command(cmd)
    #assert ret == 0

    assert os.path.isfile(outfile) is True

#    captured = capsys.readouterr()
#    assert captured.err == ""
#    assert "Compiled" in captured.out
#    assert os.path.isfile(compjson)


    assert os.path.isfile(os.path.join(outdir, "kernel", "micro_mg_tend2_0.0.0.1"))

    ret, fwds = prj.run_command("shell 'make' --workdir '%s'" % os.path.join(outdir, "kernel"))

    assert ret == 0
    if fwds["stderr"]:
        print("STDERR")
        print(fwds["stderr"])
    #assert not fwds["stderr"]

    ret, fwds = prj.run_command("shell './kernel.exe' --workdir '%s'" % os.path.join(outdir, "kernel"))

    assert ret == 0
    assert not fwds["stderr"]
    assert b"calc: PASSED verification" in fwds["stdout"]

    shutil.rmtree(outdir)
