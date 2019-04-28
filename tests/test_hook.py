import json
import shutil

import unittest
from .util import *
import django_git_deploy


class HookTest(unittest.TestCase):

    def setUp(self):
        pass


    def test_make_hook(self):
        with tmpd():
            with self.assertRaises(OSError):
                django_git_deploy.make_hook()

            with open("post-receive.sample", "w") as f:
                pass

            django_git_deploy.make_hook()
            self.assertTrue(os.path.isfile("post-receive"))
            self.assertFalse(os.path.isfile("post-receive.sample"))

            django_git_deploy.make_hook()
            self.assertTrue(os.path.isfile("post-receive"))

            self.assertTrue(os.path.isfile(django_git_deploy.Config.config_file))



if __name__ == "__main__":
    unittest.main()
