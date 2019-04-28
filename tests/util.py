import os
import tempfile
import shutil
from contextlib import contextmanager

@contextmanager
def tmpd():
    cwd0 = os.getcwd()
    tmpd = tempfile.mkdtemp()
    os.chdir(tmpd)

    yield tmpd

    os.chdir(cwd0)
    shutil.rmtree(tmpd)


