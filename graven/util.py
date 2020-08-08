# -*- coding: utf-8 -*-
""" graven.util
"""
from __future__ import absolute_import

import os
import json
import logging
import functools
from logging import Formatter

from six import string_types
import coloredlogs
import psutil
import subprocess
import six
import termcolor

## BEGIN: boilerplate for colors

blue = functools.partial(termcolor.colored, color='blue')
bold = functools.partial(termcolor.colored, attrs=['bold'])
green = functools.partial(termcolor.colored, color='green')
red = functools.partial(termcolor.colored, color='red')
yellow = functools.partial(termcolor.colored, color='yellow')

## BEGIN: boilerplate logging tools

def is_string(obj):
    """ the py3 way to check for strings """
    return isinstance(obj, string_types)

def fatal_error(msg):
    """ drop dead with a scary looking msg """
    LOGGER.info('{0} {1}'.format(red('error:'), msg))
    raise SystemExit(1)

def indent(txt, level=2):
    """ formatting helper for indention """
    if not is_string(txt):
        import pprint as _pprint
        txt =  _pprint.pformat(txt)
    return '\n'.join([
        (' ' * level) + line
        for line in txt.split('\n') if line.strip()])

def get_logger(name):
    """
    utility function for returning a logger
    with standard formatting patterns, etc
    """
    class DuplicateFilter(logging.Filter):
        def filter(self, record):
            # add other fields if you need more granular comparison, depends on your app
            current_log = (record.module, record.levelno, record.msg)
            if current_log != getattr(self, "last_log", None):
                self.last_log = current_log
                return True
            return False
    formatter = coloredlogs.ColoredFormatter(
        fmt=' - '.join([
            # "[%(asctime)s]",
            "%(levelname)s\t",
            "%(name)s\t",
            "%(message)s"]),
        # datefmt="%Y-%m-%d %H:%M:%S",
        )
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    if not logger.handlers:
        # prevents duplicate registration
        logger.addHandler(log_handler)
    logger.addFilter(DuplicateFilter())  # add the filter to it
    # FIXME: get this from some kind of global config
    logger.setLevel('DEBUG')
    return logger


LOGGER = get_logger(__name__)

## BEGIN: boilerplate for subprocess control

def invoke(cmd=None, stdin='', interactive=False, large_output=False, log_command=True, environment={}, log_stdin=True, system=False):
    """
    helper/boilerplatefor running shell commands.  this is a replacement
    for the usual fabric/invoke/subprocess/os module incantations, which
    either have lots of dependencies, or aren't easy to use and don't always
    work that well with pipes
    """
    assert isinstance(environment,(dict,)),'expected dictionary for environment'
    log_command and LOGGER.info("running command: {}".format(bold(indent(cmd))))
    if system:
        assert not stdin and not interactive
        error = os.system(cmd)
        class result(object):
            failed = failure = bool(error)
            success = succeeded = not bool(error)
            stdout = stdin = '<os.system>'
        return result
    env_string = [ "{}='{}'".format(k, v) for k,v in environment.items() ]
    env_string = ' '.join(env_string)
    cmd = "{} {}".format(env_string, cmd)
    exec_kwargs = dict(shell=True, )
    if stdin:
        msg = "command will receive pipe:\n{}"
        log_stdin and LOGGER.debug(msg.format(blue(indent(stdin))))
        exec_kwargs.update(
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        exec_cmd = subprocess.Popen(cmd, **exec_kwargs)
        exec_cmd.stdin.write(stdin.encode('utf-8'))
        exec_cmd.stdin.close()
        exec_cmd.wait()
    else:
        if not interactive:
            exec_kwargs.update(
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        exec_cmd = subprocess.Popen(cmd, **exec_kwargs)
        exec_cmd.wait()
    if exec_cmd.stdout:
        exec_cmd.stdout = '<LargeOutput>' if large_output else exec_cmd.stdout.read().decode('utf-8')
    else:
        exec_cmd.stdout = '<Interactive>'
    if exec_cmd.stderr:
        exec_cmd.stderr = exec_cmd.stderr.read().decode('utf-8')
    exec_cmd.failed = exec_cmd.returncode > 0
    exec_cmd.succeeded = not exec_cmd.failed
    exec_cmd.success = exec_cmd.succeeded
    exec_cmd.failure = exec_cmd.failed
    return exec_cmd

## BEGIN: graven state/config/preferences utilities

def graven_home():
    """ return $GRAVEN_HOME or default to ~/.graven """
    if 'GRAVEN_HOME' in os.environ:
        result = os.environ['GRAVEN_HOME']
    else:
        user = os.environ['USER']
        result = os.path.join(
            os.path.expanduser('~{}'.format(user)),
            '.graven')
    return result

def get_cached_images():
    """ """
    return os.listdir(get_cache_dir())

def graven_mnt_base():
    """ """
    home = graven_home()
    out = os.path.join(home, 'mnt')
    result = invoke("mkdir -p {}".format(out), log_command=False)
    if result.failed:
        msg = "Failed to create mnt dir ({}), error follows:\n\n".format(out, result.stderr)
        return fatal_error(msg)
    return out

def get_cache_dir():
    """ """
    home = graven_home()
    out = os.path.join(home, 'cache')
    result = invoke("mkdir -p {}".format(out), log_command=False)
    if result.failed:
        msg = "Failed to create cache dir ({}), error follows:\n\n".format(out, result.stderr)
        return fatal_error(msg)
    return out

def get_mnt_dir(img:str, partition=1):
    """ returns a specific folder to mount image into """
    return os.path.join(
        graven_mnt_base(),
        os.path.basename(img),
        str(partition))

def get_mounted_images(debug=False) -> dict:
    """ returns images for graven-managed mounts """
    managed_mounts_dir = graven_mnt_base()
    chan = LOGGER.debug if debug else (lambda *args: None)
    chan("managed mounts dir is: {}".format(managed_mounts_dir))
    alleged = invoke('ls {}'.format(managed_mounts_dir)).stdout.split('\n')
    alleged = [ _.strip() for _ in alleged  if _.strip()]
    out = {}
    for mp in alleged:
        cmd = invoke('mount | grep {}'.format(mp))
        if cmd.succeeded:
            is_mounted = True
            lodev_p = cmd.stdout.strip().split()[0]
            lodev = lodev_p[:lodev_p.rfind('p')]
            devs = json.loads(invoke('losetup --json --list').stdout)
            matches = [ x for x in devs['loopdevices'] if x['name']==lodev]
            for m in matches:
                m_lodev = m['name']
                m_img = m['back-file']
                inf = mount_info(m_img)
                out[m_img] = dict(
                    device=m_lodev,
                    **inf['devices'][m_lodev])
        else:
            is_mounted = False
        chan("  checking if {} is mounted.. {}".format(mp, is_mounted))
    return out

def get_managed_folders(img=False, partitions=False) -> list:
    """
    this is used to decide what to clean.
    returns either the img folders at `${GRAVEN_HOME}/mnt/foo.img` or
    the partition folders `${GRAVEN_HOME}/mnt/foo.img/N` for partition N
    """
    assert img ^ partitions
    if img:
        i = 1
    if partitions:
        i = 2
    cmd_t = "find {} -mindepth {} -maxdepth {} -type d"
    cmd = cmd_t.format(graven_mnt_base(), i, i)
    tmp = invoke(cmd)
    if tmp.succeeded:
        return [x.strip() for x in tmp.stdout.strip().split('\n') if x.strip()]
    return []

## BEGIN: graven loop-dev state helpers

def find_partition_devs(lodev:str):
    """ finds partitions for given loop device"""
    result = invoke("ls {}p*".format(lodev), log_command=False)
    result = result.stdout.split('\n')
    return [_.strip() for _ in result if _.strip()]

def get_mountpoints(lodev:str) -> list:
    """ returns any places where this lodev is already mounted """
    partitions = psutil.disk_partitions()
    return [p.mountpoint for p in partitions if p.device.startswith(lodev)]

# FIXME: fxn not reliable
# maybe instead : grep -H . /sys/block/sda/{capability,uevent,removable,device/{model,type,vendor,uevent}}
# def has_media(dev:str):
#     """ """
#     dev = _clean_dev_name(dev)
#     fname="/sys/block/{}/device/device_busy".format(dev)
#     LOGGER.debug(" checking {}".format(fname))
#     with open(fname, 'r') as fhandle:
#         return '1' == fhandle.read().strip()

def _clean_dev_name(dev:str):
    # /sys/block/sda/device/device_busy
    # LOGGER.debug("Checking if {} is removable..".format({}))
    if dev.startswith('/dev/'):
        dev=dev.replace('/dev/', '')
    return dev

def assert_removable(dev:str):
    """
    asserts device is removable.
    (this might only work with recent ubuntu)
    """
    dev=_clean_dev_name(dev)
    fname = '/sys/block/{}/removable'.format(dev)
    with open(fname, 'r') as fhandle:
        contents = fhandle.read().strip()
        assert '1' == contents, err

def assert_loopdev(lodev:str):
    """
    assert that the string is actually a loop-device
    """
    # FIXME: use regex
    err = 'expected a loop device, refusing to operate on {}'
    if not lodev.startswith('/dev/loop'):
        LOGGER.error(err.format(lodev))
        raise SystemExit(1)

# def assert_looppartdev(): ...

def mount_info(img=None, debug=False, **kargs) -> dict:
    """ returns mount info for the given img """
    img = img or graven_home()
    cmd = "losetup -a | grep {}"
    tmp = invoke(cmd.format(img), log_command=debug)
    lines = tmp.stdout.split('\n')
    devices = [ x.split(':')[0] for x in lines if x.strip() ]
    devices = dict(
        [ [x, dict(
            partition_devices=find_partition_devs(x),
            mount_base=os.path.dirname(get_mnt_dir(img)),
            partition_mounts=get_mountpoints(x))] for x in devices ])
    return dict(devices=devices)

## BEGIN: low-level graven action protocols

def detach(lodev:str) -> dict:
    """
    low-level detachment protocol, just leaning on shell commands
    """
    cmd = "losetup --detach {}"
    tmp = invoke(cmd.format(lodev), log_command=False)
    result = None
    if tmp.succeeded:
        # check if it's really gone
        tmp = invoke('ls {}'.format(lodev), log_command=False)
        if tmp.failed:
            result = {lodev: 'DETACH_FAILED'}
            # LOGGER.warning(tmp.stderr.strip())
            col = red
        else:
            result = {lodev: 'OK'}
            col = green
    else:
        col = red
        result = {lodev: 'ERROR: '+tmp.stderr.strip()}
    LOGGER.warning("detaching {}: {}".format(
        lodev, col(result[lodev])))
    return result

def attach(img:str, **kargs) -> str:
    """
    low-level attachment protocol, just leaning on shell commands
    """
    tmp = invoke('losetup -f').stdout.strip()
    LOGGER.debug("next loop device is: {}".format(tmp))
    result = invoke('losetup -P {} {}'.format(tmp, img))
    return tmp


def mount(lodev:str, partition:str, mdir:str) -> dict:
    """
    low-level mount protocol, just leaning on shell commands
    """
    LOGGER.debug("mounting: {}".format(lodev, partition, mdir))
    invoke('mkdir -p {}'.format(mdir))
    tmp = invoke('mount {}p{} {}'.format(lodev, partition, mdir))
    return {mdir: tmp.succeeded}

def umount(lodev:str) -> dict:
    """
    low-level umount protocol, just leaning on shell commands
    """
    assert_loopdev(lodev)
    LOGGER.warning("umounting {}".format(lodev))
    result = {}
    chan = LOGGER.warning
    for p in find_partition_devs(lodev):
        cmd = "umount -f {}".format(p)
        tmp = invoke(cmd)
        if tmp.succeeded:
            chan("..ok: {}".format(tmp.stdout.strip()))
            result[p] = 'OK'
        else:
            err = tmp.stderr.strip()
            # chan("..error: {}".format(err))
            if 'not mounted' in err or 'Invalid argument' in err:
                result[p] = 'NOT_MOUNTED'
                col=yellow
            elif 'target is busy' in err:
                result[p] = 'BUSY'
                col = red
            else:
                col = red
                result[p] = err
            chan('  partition {}: {}'.format(p, col(str(result[p]))))
    return result
