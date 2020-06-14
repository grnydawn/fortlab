
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


#def test_compile(capsys):
#
#    prj = Fortlab()
#
#    workdir = os.path.join(here, "src")
#    jsonfile = os.path.join(workdir, "test.json")
#
#    cmd = "compile make --cleancmd 'make clean' --check --savejson '%s' --verbose --workdir '%s' --assert-forward \"@len(data.keys()) == 3\" " % (jsonfile, workdir)
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
#    cmd = "compile make --cleancmd 'make clean' --savejson '%s' --verbose --workdir '%s'" % (jsonfile, workdir)
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


def test_timing(capsys):

    prj = Fortlab()

    workdir = os.path.join(here, "src")
    outdir = os.path.join(here, "output")
    callsitefile = os.path.join(workdir, "update_mod.F90")
    jsonfile = os.path.join(workdir, "test.json")
    cleancmd = "cd %s; make clean" % workdir 
    buildcmd = "cd %s; make build" % workdir
    runcmd = "cd %s; make run" % workdir

    cmd = "compile '%s' --cleancmd '%s' --savejson '%s' --verbose --workdir '%s'" % (
            buildcmd, cleancmd, jsonfile, workdir)
    cmd += " -- analyze --compile-info '@data' '%s'" % callsitefile
    cmd += " -- timingcodegen '@analysis' --outdir '%s' --cleancmd '%s' --buildcmd '%s' --runcmd '%s'" % (
                outdir, cleancmd, buildcmd, runcmd)
    ret, fwds = prj.run_command(cmd)

    assert ret == 0

    cmd = "shell 'cd %s; make; make recover; cd %s; make clean' --useenv" % (fwds["etimedir"], workdir)

    ret, fwds = prj.run_command(cmd)

    assert ret == 0

    datafiles = os.listdir(os.path.join(outdir, "model", "__data__", "1"))
    assert len(datafiles) > 0

    shutil.rmtree(outdir)
