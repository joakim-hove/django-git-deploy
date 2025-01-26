import sys
import os
import os.path
import subprocess
import shutil
import time
import yaml
import fnmatch
from contextlib import contextmanager


@contextmanager
def env_context(env):
    env0 = os.environ.copy()
    for key, value in env.items():
        if value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = value

    yield

    for key in os.environ:
        if key in env0:
            os.environ[key] = env0[key]
        else:
            del os.environ[key]


@contextmanager
def pushd(path):
    cwd0 = os.getcwd()
    if path:
        os.chdir(path)

    yield

    os.chdir(cwd0)


class Config(object):
    config_file = "deploy_config.yml"

    def __init__(self, config_file="hooks/{}".format(config_file)):
        self.data = yaml.safe_load(open(config_file))

        for config_branch, config in self.data.items():
            if not "path" in config:
                raise OSError("Must have a path setting in the branch payload")

            path = config["path"]
            if not os.path.isdir(path):
                print("path: {} does not exist".format(path))
                raise OSError("The path setting must point to an existing directory")

            if os.path.isdir(os.path.join(path, ".git")):
                raise OSError("Target path should not be the git repository")

        self.repo, _ = os.path.splitext(os.path.basename(os.getcwd()))
        self.repo_path = os.path.dirname(os.getcwd())

    def config_branch(self, git_branch):
        for config_branch in self.data.keys():
            if fnmatch.fnmatch(git_branch, config_branch):
                return config_branch

        return None

    def path(self, config_branch):
        return self.data[config_branch]["path"]

    def script(self, config_branch):
        return self.data[config_branch].get("script")

    def env(self, config_branch):
        return self.data[config_branch].get("env", {})


def reload_apache():
    subprocess.call(["sudo", "systemctl", "reload", "apache2"])


def update_wc(git_branch, conf):
    config_branch = conf.config_branch(git_branch)
    if config_branch is None:
        return

    path = conf.path(config_branch)
    env = {"GIT_DIR": None, "GIT_WORK_TREE": None}
    env.update(conf.env(config_branch))

    with env_context(env):
        with pushd(path):
            if not os.path.isdir(conf.repo):
                subprocess.call(
                    [
                        "git",
                        "clone",
                        "--recursive",
                        "{}/{}".format(conf.repo_path, conf.repo),
                    ]
                )
            os.chdir(conf.repo)

            cmd_list = [
                ["git", "fetch", "origin"],
                ["git", "reset", "--hard", "origin/%s" % git_branch],
            ]

            static_source = os.path.join(path, conf.repo, "staticfiles")
            if not os.path.isdir(static_source):
                os.mkdir(static_source)

            for cmd in cmd_list:
                print("[{}/{}]: {}".format(path, conf.repo, " ".join(cmd)))
                subprocess.call(
                    cmd, stdout=open(os.devnull, "w"), stderr=open(os.devnull, "w")
                )

            script = conf.script(config_branch)
            if script:
                if os.path.isfile(script) and os.access(script, os.X_OK):
                    path, f = os.path.split(script)
                    with pushd(path):
                        subprocess.call([os.path.abspath(f)])
                else:
                    print("script path: {} does not exist".format(script))
                    raise OSError("Script does not exist")


def post_receive():
    conf = Config()
    for line in sys.stdin.readlines():
        (_, _, ref) = line.split()
        git_branch = ref.split("/")[-1]
        update_wc(git_branch, conf)
    reload_apache()


def deploy(branch):
    conf = Config()
    update_wc(branch, conf)
    reload_apache()
