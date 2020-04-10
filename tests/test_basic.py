import fortlab
import unittest

# Command-line interface
class TaskCLITests(unittest.TestCase):

    def setUp(self):

        self.prj = fortlab.Fortlab()

    def tearDown(self):
        pass

    def test_basic(self):

        cmd = "input <1> --forward '<x=2>'"
        ret = self.prj.main(cmd)

        self.assertEqual(ret, 0)

    def test_print(self):

        cmd = "input <1> --forward '<x=2>' -- print <x> <data>"
        ret = self.prj.main(cmd)

        self.assertEqual(ret, 0)

