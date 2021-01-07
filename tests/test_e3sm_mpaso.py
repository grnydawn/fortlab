
import os, shutil, platform

from fortlab import Fortlab

here = os.path.dirname(os.path.abspath(__file__))
is_summit = len([k for k in os.environ.keys() if k.startswith("OLCF_")]) > 3

def test_summit(capsys):

    if not is_summit:
        return

    prj = Fortlab()

    mpidir = os.environ["MPI_ROOT"]

    # ./cime/scripts/create_test SMS_P12x2.ne4_oQU240.A_WCYCL1850
    #/home/users/coe0165/repos/github/E3SM/components/eam/src/physics/cam/
    #/home/users/coe0165/repos/github/E3SM/components/eam/src/physics/cam/micro_mg_cam.F90
    #/home/users/coe0165/repos/github/E3SM/components/eam/src/physics/cam/micro_mg_cam.F90
    e3smdir = "/ccs/home/grnydawn/repos/github/E3SM"
    #casedir = "/home/groups/coegroup/e3sm/scratch/coe0165/SMS_P12x2.ne4_oQU240.A_WCYCL1850.tulip_gnu.20200918_134511_d1oute"
    casedir = "/ccs/home/grnydawn/prjdir/e3sm_scratch/ERS_Ld5.T62_oQU120.CMPASO-NYF.summit_pgi.20201112_170629_a0e7o3"
    outdir = "/ccs/home/grnydawn/prjdir/kernels/kgentest/ERS_Ld5.T62_oQU120.CMPASO-NYF"

    outfile = os.path.join(outdir, "model.json")
    
    callsitefile1 = os.path.join(e3smdir, "components/mpas-source/src/core_ocean/shared/mpas_ocn_gm.F")
    callsitefile2 = os.path.join(casedir, "bld/cmake-bld/core_ocean/shared/mpas_ocn_gm.f90")
    patchfile1 = os.path.join(here, "res", "mpas_ocn_gm.F")
    patchfile2 = os.path.join(here, "res", "mpas_ocn_gm.f90")
    patchpath1 = os.path.join(e3smdir, "components/mpas-source/src/core_ocean/shared")
    patchpath2 = os.path.join(casedir, "bld/cmake-bld/core_ocean/shared")
    compjson = os.path.join(outdir, "compile.json")
    analysisjson = os.path.join(outdir, "analysis.json")
    cleancmd = "cd %s; ./case.build --clean-all" % casedir 
    buildcmd = "cd %s; ./case.build" % casedir
    runcmd = "cd %s; ./case.submit" % casedir
    excludefile = "/ccs/home/grnydawn/bin/exclude_e3sm_mpas.ini"

    # copy patch file to workaround fparser bug of parsing array constructor using "[", "]"
    shutil.copy(patchfile1, patchpath1)
    shutil.copy(patchfile2, patchpath2)

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

    #cmd = " -- buildscan '%s' --cleancmd '%s' --savejson '%s' --reuse '%s'  --verbose" % (
    #        buildcmd, cleancmd, compjson, compjson)
    cmd = " -- buildscan '%s' --savejson '%s' --reuse '%s'  --verbose" % (
            buildcmd, compjson, compjson)
    ret, fwds = prj.run_command(cmd)

    assert ret == 0

    #cmd = " -- resolve --compile-info '@data' '%s'" % callsitefile
    rescmd = (" -- resolve --mpi header='%s/include/mpif.h' --openmp enable"
             " --compile-info '%s' --keep '%s' --exclude-ini '%s' '%s'" % (
            mpidir, compjson, analysisjson, excludefile, callsitefile2))
    #ret, fwds = prj.run_command(cmd)
    #assert ret == 0

    # TODO wait??
    cmd = rescmd + " -- runscan '@analysis' -s 'timing' --outdir '%s' --cleancmd '%s' --buildcmd '%s' --runcmd '%s' --output '%s'" % (
                outdir, cleancmd, buildcmd, runcmd, outfile)
    #ret, fwds = prj.run_command(cmd)
    # add model config to analysis

    cmd = cmd + " -- kernelgen '@analysis' --model '@model' --repr-etime 'ndata=40,nbins=10'  --outdir '%s'" % outdir
    ret, fwds = prj.run_command(cmd)

    import pdb; pdb.set_trace()
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


    assert os.path.isfile(os.path.join(outdir, "kernel", "ocn_gm_velocity.0.0.1"))

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
