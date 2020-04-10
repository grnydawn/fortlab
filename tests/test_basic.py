import fortlab


def test_basic():

    cmd = "input <1> --forward '<x=2>'"
    ret = fortlab.main(cmd)

    assert ret == 0

def test_print(capsys):

    cmd = "input <1> --forward '<x=2>' -- print <x> <data>"
    ret = fortlab.main(cmd)

    assert ret == 0

    captured = capsys.readouterr()
    assert captured.out == "2 1\n"
    assert captured.err == ""
