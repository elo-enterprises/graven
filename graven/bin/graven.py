##
# requires: pyparted
# adapted from: https://github.com/dcantrell/pyparted/blob/master/src/fdisk/fdisk.py
##

import os
import json

import click
import functools
from graven import (api, cli, util,)

LOGGER = util.get_logger(__name__)
@click.command(cls=cli.Group)
def entry(*args, **kargs):
    """
    Tool for working with images.
    For more detail, use --help on subcommands.
    """
    if not os.geteuid() == 0:
        LOGGER.error("this tool requires root!")
        raise SystemExit(1)
    pass


ApiWrapper = functools.partial(
    cli.ApiWrapper, entry=entry,
    )

status = ApiWrapper(
    fxn=api.status,
    aliases=['st', 'stat'],
    extra_options=[
        # cli.args.img,
    ])

list = ApiWrapper(
    fxn=api.ls,
    aliases=['list'],
    extra_options=[
        cli.args.img,
    ])

clean = ApiWrapper(
    fxn=api.clean,
    aliases=[],
    extra_options=[
        # cli.args.img,
    ])

detach =  ApiWrapper(
    fxn=api.detach,
    aliases=['d'],
    extra_options=[
        cli.args.img,
    ])

mount =  ApiWrapper(
    fxn=api.mount,
    aliases=['m'],
    extra_options=[
        cli.args.mountpoint_maybe,
        cli.args.img,
        # cli.options.mountpoint,
        cli.options.partition,
        cli.options.umount_all,
    ])

umount =  ApiWrapper(
    fxn=api.umount,
    aliases=['u'],
    extra_options=[
        cli.args.img_maybe,
        cli.options.umount_all,
    ])

split = ApiWrapper(
    fxn=api.split,
    extra_options=[
        cli.args.img,
    ])

cache = ApiWrapper(
    fxn=api.cache,
    extra_options=[
        cli.args.img,
    ])

version = ApiWrapper(
    fxn=api.versions,
    extra_options=[])

copy = ApiWrapper(
    fxn=api.copy,
    aliases=['cp'],
    extra_options=[
        cli.args.img,
        cli.args.dest_path,
        cli.args.src_path,
        cli.options.partition,
    ])

flash = ApiWrapper(
    fxn=api.flash,
    aliases=['fl'],
    extra_options=[
        cli.args.dest_path,
        cli.args.src_path,
    ])
