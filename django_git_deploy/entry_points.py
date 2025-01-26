import os
import os.path
import yaml

from django_git_deploy import Config


def make_hook():
    _, hook_path = os.path.split(os.path.abspath(os.getcwd()))
    if hook_path != "hooks":
        raise OSError(
            "The make_hook script must be invoked from the hooks/ directory in a git repo"
        )

    if os.path.exists("post-receive.sample"):
        print("Removing existing post-receive.sample file")
        if os.path.exists("post-receive.sample"):
            os.unlink("post-receive.sample")

    with open("post-receive", "w") as f:
        f.write("""#!/usr/bin/env python3
from django_git_deploy import post_receive

post_receive()
        """)

    os.chmod("post-receive", 0o755)

    if not os.path.exists(Config.config_file):
        d = {"master": {"path": "/path/to/deploy/master", "env": {"KEY1": "VALUE1"}}}
        with open(Config.config_file, "w") as f:
            f.write(yaml.dump(d))
        print("Sample configuration stored in: {}".format(Config.config_file))
