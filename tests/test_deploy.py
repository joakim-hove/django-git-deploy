import yaml
import os
import unittest

import django_git_deploy
from .util import tmpd


class DeployTest(unittest.TestCase):

    def setUp(self):
        pass


    def test_main(self):
        pass


    def test_config(self):
        config_file = "hooks/deploy_config.yml"
        with tmpd() as wd:
            os.makedirs("repo.git/hooks")
            with django_git_deploy.pushd("repo.git"):
                d = {"branch" : {}}
                with open(config_file, "w") as f:
                    f.write(yaml.dump(d))
                with self.assertRaises(OSError):
                    c = django_git_deploy.Config()

                d = {"branch" : {"path" : "/does/not/exist"}}
                with open(config_file, "w") as f:
                    f.write(yaml.dump(d))
                with self.assertRaises(OSError):
                    c = django_git_deploy.Config()


                os.makedirs("path/.git")
                d = {"branch" : {"path" : "path"}}
                with open(config_file, "w") as f:
                    f.write(yaml.dump(d))
                with self.assertRaises(OSError):
                    c = django_git_deploy.Config()

                os.makedirs("path2")
                d = {"branch" : {"path" : "path2"}}
                with open(config_file, "w") as f:
                    f.write(yaml.dump(d))
                c = django_git_deploy.Config()

                self.assertEqual( c.path("branch"), "path2")
                self.assertIn("branch", c)
                self.assertNotIn("branch2", c)

                self.assertEqual(len(c.env("branch")), 0)

                d = {"branch" : {"path" : "path2", "env" : {"KEY" : "VALUE"}}}
                with open("hooks/deploy_config2.yml", "w") as f:
                    f.write(yaml.dump(d))
                c = django_git_deploy.Config( config_file = "hooks/deploy_config2.yml")
                env = c.env("branch")
                self.assertIn("KEY", env)
                self.assertEqual(env["KEY"], "VALUE")

                self.assertEqual(c.repo , "repo")
                self.assertEqual(c.repo_path, wd)



if __name__ == "__main__":
    unittest.main()
