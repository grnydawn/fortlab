
import os

from fortlab import Fortlab

here = os.path.dirname(os.path.abspath(__file__))

def test_basic():

    prj = Fortlab()

    cmd = "input @1 --forward '@x=2'"
    ret = prj.main(cmd)

    assert ret == 0

def test_print(capsys):

    prj = Fortlab()

    cmd = "-- input @1 --forward '@x=2' -- print @x @data[0]"
    ret = prj.main(cmd)

    assert ret == 0

    captured = capsys.readouterr()
    assert captured.out == "21\n"
    assert captured.err == ""


def test_compile(capsys):

    prj = Fortlab()

    workdir = os.path.join(here, "src")

    cmd = "compile make --cleancmd 'make clean' --verbose --workdir '%s' --assert-forward \"@len(data.keys()) == 3\" " % workdir
    ret = prj.main(cmd)

    assert ret == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "Compiled" in captured.out
