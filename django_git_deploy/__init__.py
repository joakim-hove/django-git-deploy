from pathlib import Path
import sys
import os
import os.path
import subprocess
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

        for config in self.data.values():
            if "deploy_path" not in config:
                raise OSError("Must have a path setting in the branch payload")

            deploy_path = config["deploy_path"]
            if not os.path.isdir(deploy_path):
                print("path: {} does not exist".format(deploy_path))
                raise OSError("The path setting must point to an existing directory")

            if os.path.isdir(os.path.join(deploy_path, ".git")):
                raise OSError("Target path should not be the git repository")

        self.repo, _ = os.path.splitext(os.path.basename(os.getcwd()))
        self.repo_path = os.path.dirname(os.getcwd())

    def config_branch(self, git_branch):
        for config_branch in self.data.keys():
            if fnmatch.fnmatch(git_branch, config_branch):
                return config_branch

        return None

    def deploy_path(self, config_branch):
        return Path(self.data[config_branch]["deploy_path"])

    def script(self, config_branch):
        script_arg = self.data[config_branch].get("script")
        if script_arg is None:
            return None

        return Path(script_arg)

    def env(self, config_branch):
        return self.data[config_branch].get("env", {})


# Comment
def reload_apache():
    print("Running reload apache")
    # subprocess.call(["sudo", "systemctl", "reload", "apache2"])


def update_work_tree(git_branch, conf):
    config_branch = conf.config_branch(git_branch)
    if config_branch is None:
        return

    deploy_path = conf.deploy_path(config_branch)
    env = {"GIT_DIR": None, "GIT_WORK_TREE": None}
    env.update(conf.env(config_branch))

    with env_context(env):
        cmd = [
            "git",
            "checkout",
            "-f",
            "--work-tree",
            str(deploy_path),
            "-C",
            f"{conf.repo_path}/{conf.repo}",
            git_branch,
        ]
        print(" ".join(cmd))
        subprocess.run(cmd, check=True)
        with pushd(deploy_path):
            os.chdir(conf.repo)

            static_source = os.path.join(deploy_path, conf.repo, "staticfiles")
            if not os.path.isdir(static_source):
                os.mkdir(static_source)

            script = conf.script(config_branch)
            if script:
                if script.is_file() and os.access(script, os.X_OK):
                    subprocess.run([str(script)], check=True)
                else:
                    print("script path: {} does not exist".format(script))
                    raise OSError("Script does not exist")


def post_receive():
    conf = Config()
    for line in sys.stdin.readlines():
        (_, _, ref) = line.split()
        git_branch = ref.split("/")[-1]
        update_work_tree(git_branch, conf)


def deploy(branch):
    conf = Config()
    update_work_tree(branch, conf)
