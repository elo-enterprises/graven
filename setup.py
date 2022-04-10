import sys
import versioneer
from setuptools import setup
if 'darwin' in sys.platform or 'win' in sys.platform:
    err = "Refusing to install for platform `{}`, this tool requires a modern linux with losetup, etc"
    err = err.format(sys.platform)
    raise RunTimeError(err)

try:
    version=versioneer.get_version()
    cmdclass=versioneer.get_cmdclass()
except AttributeError: # running tests from tox?
    version = '0.0.0'
    cmdclass = {}

if __name__ == "__main__":
    try:
        setup(
            version=version,
            cmdclass=cmdclass,)
    except:  # noqa
        raise
