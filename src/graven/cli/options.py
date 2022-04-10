# -*- coding: utf-8 -*-
""" graven.cli.options (boilerplate for click)

    Common CLI arguments for reuse
"""
from __future__ import absolute_import

from functools import partial

import click

version = click.option(
    '--version',
    is_flag=True, required=False, default=False,
    help='Show versions for libparted')
umount_all = click.option('--all',
    is_flag=True, required=False, default=False,
    help='unmount all graven-managed loop devs')

partition = click.option('--partition',
    help='partition number to use (default is 1)', required=False, default='1')

mountpoint = click.option('--mountpoint',
    help='mountpoint to use (default is $GRAVEN_HOME/mnt/<IMG>',
    required=False, default=None)
