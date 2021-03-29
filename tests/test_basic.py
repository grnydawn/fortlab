
import os, shutil

from fortlab import Fortlab

here = os.path.dirname(os.path.abspath(__file__))

def test_basic():

    prj = Fortlab()

    cmd = "input @1 --forward '@x=2'"
    ret, fwds = prj.run_command(cmd)

    assert ret == 0

def test_print(capsys):

    prj = Fortlab()

    cmd = "-- input @1 --forward '@x=2' -- print @x @data[0]"
    ret, fwds = prj.run_command(cmd)

    assert ret == 0

    captured = capsys.readouterr()
    assert captured.out == "21\n"
    assert captured.err == ""


#def test_compflag(capsys):
#
#    prj = Fortlab()
#
#    workdir = os.path.join(here, "src")
#    jsonfile = os.path.join(workdir, "test.json")
#
#    cmd = "compflag make --cleancmd 'make clean' --check --savejson '%s' --verbose --workdir '%s' --assert-forward \"@len(data.keys()) == 3\" " % (jsonfile, workdir)
#    ret, fwds = prj.run_command(cmd)
#
#    assert ret == 0
#
#    captured = capsys.readouterr()
#    assert captured.err == ""
#    assert "Compiled" in captured.out
#    assert os.path.isfile(jsonfile)
#    os.remove(jsonfile)
#
#
#def test_analyze(capsys):
#
#    prj = Fortlab()
#
#    workdir = os.path.join(here, "src")
#    callsitefile = os.path.join(workdir, "update_mod.F90")
#    jsonfile = os.path.join(workdir, "test.json")
#
#    cmd = "comflag make --cleancmd 'make clean' --savejson '%s' --verbose --workdir '%s'" % (jsonfile, workdir)
#    cmd += " -- analyze --compile-info '@data' '%s'" % callsitefile
#    ret, fwds = prj.run_command(cmd)
#
#    assert ret == 0
#
#    captured = capsys.readouterr()
#    assert captured.err == ""
#    assert "Compiled" in captured.out
#    assert os.path.isfile(jsonfile)
#    os.remove(jsonfile)

#
#def test_timing(capsys):
#
#    prj = Fortlab()
#
#    workdir = os.path.join(here, "src")
#    outdir = os.path.join(here, "output")
#    callsitefile = os.path.join(workdir, "update_mod.F90")
#    jsonfile = os.path.join(workdir, "test.json")
#    cleancmd = "cd %s; make clean" % workdir 
#    buildcmd = "cd %s; make build" % workdir
#    runcmd = "cd %s; make run" % workdir
#
#    cmd = "comflag '%s' --cleancmd '%s' --savejson '%s' --verbose --workdir '%s'" % (
#            buildcmd, cleancmd, jsonfile, workdir)
#    cmd += " -- analyze --compile-info '@data' '%s'" % callsitefile
#    cmd += " -- timingcodegen '@analysis' --outdir '%s' --cleancmd '%s' --buildcmd '%s' --runcmd '%s'" % (
#                outdir, cleancmd, buildcmd, runcmd)
#    ret, fwds = prj.run_command(cmd)
#
#    assert ret == 0
#
#    cmd = "shell 'cd %s; make; make recover; cd %s; make clean' --useenv" % (fwds["etimedir"], workdir)
#
#    ret, fwds = prj.run_command(cmd)
#
#    assert ret == 0
#
#    datafiles = os.listdir(os.path.join(outdir, "model", "__data__", "1"))
#    assert len(datafiles) > 0
#
#    shutil.rmtree(outdir)


#def test_model(capsys):
#
#    prj = Fortlab()
#
#    workdir = os.path.join(here, "src")
#    outdir = os.path.join(here, "output")
#    outfile = os.path.join(outdir, "model.json")
#    callsitefile = os.path.join(workdir, "update_mod.F90")
#    jsonfile = os.path.join(outdir, "compile.json")
#    cleancmd = "cd %s; make clean" % workdir 
#    buildcmd = "cd %s; make build" % workdir
#    runcmd = "cd %s; make run" % workdir
#
#    #if os.path.exists(outdir):
#    #    os.makedirs(outdir)
#
#    cmd = "--logging debug"
#    cmd += " -- buildscan '%s' --cleancmd '%s' --savejson '%s' --verbose --workdir '%s'" % (
#            buildcmd, cleancmd, jsonfile, workdir)
#    cmd += " -- resolve --compile-info '@data' '%s'" % callsitefile
#    cmd += " -- runscan '@analysis' -s 'timing' --outdir '%s' --cleancmd '%s' --buildcmd '%s' --runcmd '%s' --output '%s'" % (
#                outdir, cleancmd, buildcmd, runcmd, outfile)
#    ret, fwds = prj.run_command(cmd)
#
#    assert ret == 0
#
#    ret, fwds = prj.run_command("shell 'make clean' --useenv --workdir '%s'" % workdir)
#
#    assert ret == 0
#
#    #cmd = "shell 'cd %s; make; make recover; cd %s; make clean' --useenv" % (fwds["etimedir"], workdir)
#    #ret, fwds = prj.run_command(cmd)
#    #assert ret == 0
#
#    assert os.path.isfile(outfile) is True
#
#    import pdb; pdb.set_trace()
#    shutil.rmtree(outdir)


def test_state(capsys):

    prj = Fortlab()

    workdir = os.path.join(here, "src")
    outdir = os.path.join(here, "output")
    outfile = os.path.join(outdir, "model.json")
    callsitefile = os.path.join(workdir, "update_mod.F90")
    jsonfile = os.path.join(outdir, "compile.json")
    cleancmd = "cd %s; make clean" % workdir 
    buildcmd = "cd %s; make build" % workdir
    runcmd = "cd %s; make run" % workdir

    #if os.path.exists(outdir):
    #    os.makedirs(outdir)

    #Summit cmd = "--shell 'module load gcc' --logging debug"
    cmd = "--logging debug"
    cmd += " -- buildscan '%s' --cleancmd '%s' --savejson '%s' --verbose --workdir '%s'" % (
            buildcmd, cleancmd, jsonfile, workdir)
    cmd += " -- resolve --compile-info '@data' '%s'" % callsitefile
    cmd += " -- runscan '@analysis' -s 'timing' --outdir '%s' --cleancmd '%s' --buildcmd '%s' --runcmd '%s' --output '%s'" % (
                outdir, cleancmd, buildcmd, runcmd, outfile)
    cmd += " -- kernelgen '@analysis' --outdir '%s'" % outdir
    ret, fwds = prj.run_command(cmd)

    assert ret == 0

    ret, fwds = prj.run_command("shell 'make clean' --useenv --workdir '%s'" % workdir)

    assert ret == 0

    #cmd = "shell 'cd %s; make; make recover; cd %s; make clean' --useenv" % (fwds["etimedir"], workdir)
    #ret, fwds = prj.run_command(cmd)
    #assert ret == 0

    assert os.path.isfile(outfile) is True

#    captured = capsys.readouterr()
#    assert captured.err == ""
#    assert "Compiled" in captured.out
#    assert os.path.isfile(jsonfile)


    assert os.path.isfile(os.path.join(outdir, "kernel", "calc.0.0.1"))

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
