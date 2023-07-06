""" graven.api
"""

import os
import sys
import time
import functools
from collections import defaultdict

from graven import util

DEFAULT_PAUSE = 5
LOGGER = util.get_logger(__name__)
invoke = functools.partial(util.invoke, log_command=False)

def _assert_root():
    assert os.geteuid() == 0


def copy(src_path=None, dest_path=None, img=None, partition=1, **kargs):
    """
    Copies SRC_PATH into img@ dest_path
    """
    # LOGGER.debug("copying with {}".format([src_path, dest_path, img, partition]))
    assert dest_path.startswith(os.path.sep)
    out = []
    LOGGER.debug("copying from host {} to {} in img {}, part {}..".format(
        src_path, dest_path, img, partition))
    tmp = mount(img, partition=partition)
    out.append(tmp)
    LOGGER.debug("  * mounted img {} @ partition {}".format(
        img, partition))
    mdir = util.get_mnt_dir(img, partition=partition)
    LOGGER.debug("  * using mount-dir {}".format(mdir))
    cmd = "cp {} {}".format(src_path, os.path.join(mdir, dest_path[1:]))
    util.invoke(cmd)
    tmp = umount(img, partition=partition)
    out.append(tmp)
    return out

def block(device_or_file, until=None, disk=None, media=None, delta=2, **kargs):
    """ Block until {MEDIA_INSERTED|MEDIA_REMOVED} """
    LOGGER.debug("Blocking until condition `{}` is met".format(until))
    # validation
    if until in ['MEDIA_INSERTED', 'MEDIA_REMOVED']:
        disk = device_or_file
        assert disk.startswith('/dev/'), 'disk name should start with /dev!'
        media = disk[len('/dev/'):]

    if until=='MEDIA_INSERTED':
        msg = "Waiting for media at `{}` to be inserted (polling every {}s)"
        LOGGER.debug(msg.format(media, delta))
        count = 0
        cmd_t = 'lsblk -do name,tran | grep {} > /dev/null'
        cmd = cmd_t.format(media)
        LOGGER.debug("Will be using this command:")
        LOGGER.debug("  {}".format(cmd))
        while True:
            if os.system(cmd) == 0:
                LOGGER.debug("Media at `{}` appears to be inserted".format(disk))
                break
            else:
                msg = ".. ({}) media at `{}` appears absent"
                LOGGER.debug(msg.format(count, disk))
                time.sleep(delta)
                count += 1

    elif until=='MEDIA_REMOVED':
        disk = device_or_file
        assert disk.startswith('/dev/'), 'disk name should start with /dev!'
        media = disk[len('/dev/'):]
        msg = "Waiting for media at `{}` to be removed (polling every {}s)"
        LOGGER.debug(msg.format(media, delta))
        count = 0
        cmd_t = 'lsblk -do name,tran | grep {} > /dev/null'
        cmd = cmd_t.format(media)
        LOGGER.debug("Will be using this command:")
        LOGGER.debug("  {}".format(cmd))
        while True:
            if os.system(cmd) != 0:
                LOGGER.debug("Media at `{}` appears to be gone!".format(disk))
                break
            else:
                msg = ".. ({}) media at `{}` appears to still be present"
                LOGGER.debug(msg.format(count, disk))
                time.sleep(delta)
                count += 1
    else:
        err = "Unsupported event type for until!"
        LOGGER.error(err)
        raise SystemExit(err)

def flash(src_path=None, dest_path=None, debug=None, force=None, dry_run=None, block_size='5M', **kargs):
    """
    Flashes IMG (or SRC_DEV) to DEST_DEV
    """
    error = False
    actions = []
    assert not (force and dry_run), 'cant use `force` and `dry-run` at the same time!'
    result = dict(src=src_path, dest=dest_path, error=error, actions=actions)

    def doit():
        if dry_run:
            result['error'] = 'DRY_RUN'
        have_pv = invoke('which pv').succeeded
        cmd = 'dd if={} bs={}'.format(src_path,block_size)
        cmd = '{} | pv'.format(cmd) if have_pv else '{}'.format(cmd)
        cmd = '{} | dd of={}'.format(cmd,dest_path)
        msg = "\nPausing {}s before writing to `{}` using command:\n\n  {}"
        LOGGER.warning(msg.format(DEFAULT_PAUSE, dest_path, util.bold(cmd)))
        time.sleep(5)
        flashing = util.actions_in_progress().get('flashing', [])
        action = dict(
                    dest=dest_path, src=src_path,
                    error=False, status="PENDING",)
        LOGGER.debug("Adding action to queue")
        util.update_actions(flashing=flashing + [action])
        tmp = util.invoke(cmd, system=True)
        LOGGER.debug("Popping action from queue")
        flashing = util.actions_in_progress().get('flashing', [])
        flashing = [x for x in flashing if not
            (x.get('src')==src_path and x.get('dest')==dest_path)
        ]
        util.update_actions(flashing=flashing)
        if tmp.succeeded:
            action = dict(flash=dict(
                    dest=dest_path, src=src_path,
                    error=False, status="OK",))
        else:
            LOGGER.critical("Failed trying to write to disk.  Is the media inserted?")
            raise SystemExit(1)
            # action = dict(flash=dict(
            #         dest=dest_path, src=src_path,
            #         error=True, status=tmp.stderr.strip(),))
        result['actions'] += [action]
        return result
    if os.path.isdir(dest_path):
        msg = 'Cannot use an existing directory for `dest_path`'
        LOGGER.critical(msg)
        raise SystemExit(1)
    elif dest_path.startswith('/dev'):
        # Case: Device
        LOGGER.debug("Detected destination `{}` is a device".format(dest_path))
        LOGGER.debug("Asserting device is removable..")
        util.assert_removable(dest_path)
        LOGGER.debug(util.green("  OK"))
        # LOGGER.debug("Checking for presence of media..")
        # if util.has_media(dest_path):
        #     LOGGER.debug(util.green("  OK"))
        # else:
        #     LOGGER.critical(util.red(" Device does not have media!"))
        #     raise SystemExit(1)
        return doit()
    else:
        # Case: Not Device
        LOGGER.debug("Detected destination `{}` is not device".format(dest_path))
        if os.path.exists(dest_path):
            if not force:
                msg = (
                    "\nDestination path `{}` already exists"
                    " and `force` is not set, abandoning effort")
                msg = msg.format(dest_path)
                LOGGER.critical(msg)
                raise SystemExit(1)
            else:
                msg = (
                    "\nDestination at `{}` exists, but `force` is set, "
                    "waiting a few seconds and then proceeding..")
                msg = msg.format(dest_path)
                LOGGER.warning(msg)
                time.sleep(5)
                return doit()
        else:
            return doit()
    raise Exception("undefined behaviour")

def umount(img=None, all=False, partition=None, simple=False,**kargs) -> list:
    """
    Unmounts an IMG from optional path.  If path
    is not given, then it will be unmounted everywhere
    it is mounted.  Returns information about any
    umounts/detachments that occur.
    """
    def has_err(acts:list) -> bool:
        return 'error' in acts or any(['BUSY' in act.values() for act in acts])

    if img and not util.is_string(img) and len(img) > 0:
        LOGGER.debug("unmounting multiple images: {}".format(img))
        return [umount(x) for x in img]
    elif not img:
        if not all:
            raise RuntimeError('expected an image or --all flag')
        else:
            LOGGER.debug(".. detected --all flag")
            st = status()
            actions = [umount(img,simple=True) for img in st['images']['mounted']]
            import functools
            actions = functools.reduce(lambda x,y: x+y, actions, [])
            return dict(error=has_err(actions), actions=actions)
    elif util.is_string(img):
        tmp = util.mount_info(img, **kargs)
        actions = []
        devices = tmp['devices']
        for dev in devices:
            actions.append(util.umount(dev))
            actions.append(util.detach(dev))
        if simple:
            return actions
        return dict(error=has_err(actions), actions=actions)
    else:
        import IPython
        IPython.embed()
        raise Exception('niy')

def mount_all(img=None, mountpoint=None, debug=None):
    """ """
    assert not mountpoint
    x = util.mount_info(img)
    any_lodev = list(x['devices'].keys())[0]
    part_devs = x['devices'][any_lodev]['partition_devices']
    # need 1 or 2, not /dev/loop33p2
    part_enum = [_[_.rfind('p') + 1:] for _ in part_devs]
    [mount(
        img=img, partition=p, debug=debug)
        for p in part_enum]

def mount(img, mountpoint=None, all=False, partition='1', debug=False, **kargs):
    """
    Mounts an image to optional destination.  if dest
    is not given, then $GRAVEN_WORK_DIR will be used.
    no operation performed if already mounted.
    """
    if not util.is_string(mountpoint):
        # accounts for if we're called with nargs=-1
        mountpoint = mountpoint[0] if mountpoint else None
    LOGGER.debug("mounting: img={} mountpoint={} partition={}".format(
        img, mountpoint, 'all' if all else partition,
    ))
    tmp = util.mount_info(img, **kargs)
    devices = tmp['devices']
    mdir = mountpoint or util.get_mnt_dir(img, partition)
    if devices:
        LOGGER.debug("inspecting devices: {}".format(devices))
        if len(devices) > 1:
            msg = '  multiple attachments already exist: {}'.format(devices.keys())
            LOGGER.warning(msg)
        elif len(devices) == 0:
            msg = '  already attached at {}'.format(devices.keys())
            LOGGER.warning(msg)
        for lodev, devdata in devices.items():
            current_mounts = devdata['partition_mounts']
            if all:
                mount_all(img=img, mountpoint=mountpoint, debug=debug)
                return status()['images']['mounted'][img]
            if current_mounts:
                collisions = [m for m in current_mounts if m.endswith(partition)]
                if any(collisions):
                    msg = 'already mounted at: {}'.format(collisions)
                    # return dict(mounts=collisions)
                    return status()['images']['mounted'][img]

            msg = "{} is not mounted yet."  # , will be mounted to {}"
            LOGGER.debug(msg.format(lodev))
            util.mount(lodev, partition, mdir)
            return status()['images']['mounted']
    else:
        LOGGER.debug("no mounts & no attachments found.. attaching")
        LOGGER.debug("attaching..")
        lodev = util.attach(img)
        if all:
            mount_all(img=img,mountpoint=mountpoint,debug=debug)
        else:
            util.mount(lodev, partition, mdir)
        return status()['images']['mounted'][img]
        # return mount(img, mountpoint=mountpoint, all=all,partition=partition)
        # return status()['images']['mounted'][img]
        # # dict(device=lodev, partition_devices=util.find_partition_devs(lodev))

def clean(force=False, dry_run=False, **kargs) -> list:
    """ cleans unused internal mount directories """
    assert not (force and dry_run)
    act = umount(all=True)
    if act['error']:
        LOGGER.critical(
            "\n\nCan't clean due to persistent mounts.  "
            "Is `graven unmount --all` stuck?  "
            "Check your working directories or processes"
            " that might be touching this folder\n")
        raise SystemExit(1)
    else:
        LOGGER.debug("Unmount worked ok, proceeding..")
        # NB: parts must come first!
        clean_dirs = util.get_managed_folders(partitions=True) + util.get_managed_folders(img=True)
        clean_dirs = [x for x in clean_dirs if x.strip()]
        clean_cmd = ["rmdir '{}'".format(x) for x in clean_dirs]
        clean_cmd = ' && '.join(clean_cmd)
        if clean_cmd:
            LOGGER.warning("Clean command will be: `{}`".format(clean_cmd))
            if not force:
                choice = input('\nContinue? ')
                if choice.lower() not in ['y', 'yes']:
                    raise SystemExit("Aborting at user request.")
            if not dry_run:
                util.invoke(clean_cmd)
        return dict(cleaned=clean_dirs)

def detach(img, **kargs) -> list:
    """
    detaches img if attached
    """
    return dict(error='not implemented yet')
    # tmp = util.mount_info(img, **kargs)
    # devices = tmp['devices']
    # LOGGER.debug("detaching {} devices with `losetup -d`..".format(len(devices)))
    # out = []
    # for dev in devices:
    #     mounted = devices[dev]['mounted']
    #     if mounted:
    #         tmp = _umount(dev)
    #         out += [tmp]
    #     result = invoke('losetup -d {}'.format(dev), log_command=False)
    #     if result.succeeded:
    #         out += [{dev: 'OK'}]
    #     else:
    #         out+=[dict(error="{}".format(result.stderr.strip()))]
    # return out


# def mountp(disk, partition_num):
#     """ mount (disk, partition_num) """
#     first_unused = invoke('losetup -f')
#     first_unused = first_unused.success and first_unused.stdout.strip()
#     if not first_unused:
#         err="no unused loop devices found with `lopsetup -f`.  Sudo?"
#         LOGGER.critical(err)
#         raise SystemExit(1)

def versions(**kargs):
    """
    Returns version info for graven, libparted, etc
    """
    losetup_version = util.invoke('losetup --version', log_command=False)
    losetup_version = losetup_version.stdout.strip() if losetup_version.succeeded else None
    try:
        import parted
        tmp = parted.version()
    except ImportError:
        tmp = dict(pyparted=None,libparted=None)
    return dict(
        graven='.1',
        losetup=losetup_version,
        pyparted='.'.join([
            str(x) for x in tmp["pyparted"]])
            if tmp["pyparted"] else tmp["pyparted"],
        libparted=tmp["libparted"])

def status(hint=None, **kargs):
    """
    Returns status, including graven-managed mounts, cache, etc
    """
    return dict(
        graven_home=util.graven_home(),
        versions = versions(),
        images=dict(
            cached=util.get_cached_images(),
            mounted=util.get_mounted_images(),
            # attached=util.get_attached_images(),
        ),
        actions=util.actions_in_progress(),
    )

def ls(img=None, **kargs):
    """
    Returns information for given img, including number of partitions,
    current associated loop-devices, mounts.
    """
    def sizeof_fmt(num, suffix='B'):
        # https://stackoverflow.com/questions/1094841/get-human-readable-version-of-file-size
        for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)
    from graven.f_disk import list as flist
    partitions = flist(img)
    st_size = os.stat(img).st_size
    # os.stat_result(st_mode=33188, st_ino=6419862, st_dev=16777220, st_nlink=1, st_uid=501, st_gid=20, st_size=1564, st_atime=1584299303, st_mtime=1584299400, st_ctime=1584299400)
    out = dict(
        partitions=partitions,
        metadata=dict(
            bootable=any([x['bootable'] for x in partitions]),
            partition_count=len(partitions),
            partition_types=list(set([x['filesystem'] for x in partitions])),
            size=st_size,
            human=dict(
                size=sizeof_fmt(st_size),
            )))
    return {os.path.abspath(img): out}

def split(img, **kargs):
    """
    Splits a composite IMG into 1 image per partition
    """
    return dict(error='not implemented yet')

def cache(img, **kargs):
    """
    Caches IMG in graven work dir (to avoid in-place changes)
    """
    return dict(error='not implemented yet')
