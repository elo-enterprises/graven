# -*- coding: utf-8 -*-
""" graven.cli.args (boilerplate for click)

    Common CLI arguments for reuse
"""
from __future__ import absolute_import
import click
from functools import partial

img = click.argument('img', type=click.Path(exists=True), nargs=1)
img_maybe = click.argument('img', type=click.Path(exists=True), nargs=-1)
src_path = click.argument('src_path', type=click.Path(exists=True), nargs=1)
dest_path = click.argument('dest_path', type=click.Path(exists=False), nargs=1)
mountpoint_maybe = click.argument('mountpoint', nargs=-1)
