"""graven
"""
# NB: this should have been set by CI immediately
# before pypi-upload.  but the `except` below might
# be triggered by local development.
try:
    from ._version import __version__  # noqa
except (ImportError, AttributeError):
    __version__ = "0.0.0+local"
