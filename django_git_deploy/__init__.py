import sys
import os
import subprocess
import shutil
import time
import yaml
from contextlib import contextmanager

root_map = { "devel"  : "/var/django/sleipner/devel/sleipner",
             "master" : "/var/django/sleipner/master/sleipner" }

res_root = "/home/munin/res/sleipner/static"

sleipner_mode = {"devel"  : "DEVEL" ,
                 "master" : "SLEIPNER"}




@contextmanager
def env_context(env):
    env0 = os.environ.copy()
    for key,value in env.items():
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
    os.chdir(path)

    yield

    os.chdir(cwd0)




class Config(object):
    config_file = "deploy_config.yml"

    def __init__(self, config_file = "hooks/{}".format(config_file)):
        self.data = yaml.load(open(config_file))

        for branch,config in self.data.items():
            if not "path" in config:
                raise OSError("Must have a path setting in the branch payload")

            path = config["path"]
            if not os.path.isdir(path):
                raise OSError("The path setting must point to an existing directory")

            if os.path.isdir(os.path.join(path, ".git")):
                raise OSError("Target path should not be the git repository")

        self.repo, _ = os.path.splitext( os.path.basename( os.getcwd() ))
        self.repo_path = os.path.dirname( os.getcwd() )


    def __contains__(self, branch):
        return branch in self.data


    def path(self, branch):
        return self.data[branch]["path"]


    def env(self, branch):
        return self.data[branch].get("env", {})



def update_wc(branch, conf):
    if not branch in conf:
        return

    path = conf.path(branch)
    env = {"GIT_DIR" : None, "GIT_WORK_TREE": None}
    env.update(conf.env(branch))

    with env_context(env):
        with pushd(path):
            if not os.path.isdir(conf.repo):
                subprocess.call(["git", "clone", "--recursive" , "{}/{}".format(conf.repo_path, conf.repo)])
            os.chdir(conf.repo)

            cmd_list = (["git" , "fetch" , "origin"],
                        ["git" , "reset" , "--hard","origin/%s" % branch],
                        ["python", "manage.py", "collectstatic", "--noinput"])


            static_source = os.path.join( path , "staticfiles" )
            if not os.path.isdir( static_source ):
                os.mkdir( static_source )

            for cmd in cmd_list:
                print "[{}/{}]: {}".format(path, conf.repo, " ".join(cmd))
                subprocess.call( cmd ,
                                 stdout = open(os.devnull , "w") ,
                                 stderr = open(os.devnull , "w") )

            # static_target = os.path.join( res_root , branch )
            # if os.path.isdir(static_target):
                # shutil.rmtree( static_target )

            # os.makedirs( static_target )
            # for entry in os.listdir( static_source ):
                # src = os.path.join( static_source , entry )
                # target = os.path.join( static_target , entry )
                # if os.path.isfile( entry ):
                    # shutil.copyfile( src , target )
                # else:
                    # shutil.copytree( src , target )


def post_receive():
    conf = Config()
    for line in sys.stdin.readlines():
        (old , new , ref) = line.split()
        branch = ref.split("/")[-1]
        update_wc(branch, conf)


def deploy(branch):
    conf = Config()
    update_wc(branch, conf)



def make_hook():
    if os.path.exists("post-receive.sample"):
        print("Removing existing post-receive.sample file")
    elif os.path.exists("post-receive"):
        print("Updating existing post-receive file")
    else:
        raise OSError("The make_hook script must be invoked from the hooks/ directory in a git repo")

    with open("post-receive", "w") as f:
        f.write("""
#!/usr/bin/python
from django_git_deploy import post_receive

post_receive()
        """)

    os.chmod("post-receive", 0o755)
    if os.path.exists("post-receive.sample"):
        os.unlink("post-receive.sample")


    if not os.path.exists(Config.config_file):
        d = {"master": {"path": "/path/to/deploy/master",
                        "env": {"KEY1" : "VALUE1"}}}
        with open(Config.config_file, "w") as f:
            f.write(yaml.dump(d))
        print("Sample configuration stored in: {}".format(Config.config_file))
