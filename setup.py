""" setup
"""
import os
import sys
from setuptools import setup

GIT_COMMIT = os.environ.get("GIT_COMMIT", "local")

# if 'darwin' in sys.platform or 'win' in sys.platform:
# if 'win' in sys.platform:
#     err = "Refusing to install for platform `{}`, this tool requires a modern linux with losetup, etc"
#     err = err.format(sys.platform)
#     raise SystemExit(err)

if os.environ.get("PYPI_RELEASE", None):
    USE_CALVER = f"%Y.%m.%d.%H.%M"
else:
    USE_CALVER = f"%Y.%m.%d+{GIT_COMMIT}"

if __name__ == "__main__":
    try:
        setup(
            # use_calver=f"%Y.%m.%d.%H.%M+{GIT_COMMIT}",
            use_calver=USE_CALVER,
            setup_requires=["setuptools", "calver", "build<0.10.0"],
        )
    except:  # noqa
        print(
            "\n\nAn error occurred while building the project, "
            "please ensure you have the most updated version of setuptools, "
            "setuptools_scm and wheel with:\n"
            "   pip install -U setuptools setuptools_scm wheel\n\n"
        )
        raise
