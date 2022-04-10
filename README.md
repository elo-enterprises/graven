<table>
  <tr><th><strong>graven</strong></th>
    <th style="padding:0px 5px;text-align:right;float:right;">
      <small><small>
        <a href=README.md>Index</a> |
        <a href=#overview>Overview</a> |
        <a href=#features>Features</a> |
        <a href=#requirements>Requirements</a> |
        <a href=#installation>Installation</a> |
        <a href=#usage>Usage</a> |
        <a href=#development-notes>Development Notes</a>
        <a href=#future-work>Future Work</a> |
      </small><small>
    </th>
  </tr>
  <tr>
    <td width=15%><img src=img/icon.png style="width:150px"></td>
    <td>
    <center>Graven: a tool for working with disk images</center>
    </td>
  </tr>
</table>

## Overview

Graven is a small tool for working with disk images.

Most of what `graven` does is just automating commands over losetup in a way that is idempotent, with return values that are machine-friendly (JSON).

There are several tools in the same space[1] which you might be interested to try, but `graven` exists because we found them unfriendly for pipelines or we just couldn't get the flexibility we needed out them.

See also:
* [rpi-imager](https://www.raspberrypi.org/blog/raspberry-pi-imager-imaging-utility/)
* [hypriot's flash tool](https://github.com/hypriot/flash)

## Features

1) Idempotent: mounting a already-mounted image gives no result (no error, no redundant mount)
**Detailed, human/api/machine-friendly json output that describes partitions, mountpoints, and the original image:**

```
sudo `which graven` ls images/ubuntu-18.04.5-preinstalled-server-arm64+raspi4.img
{
  "image": {
    "path": "/tmp/images/ubuntu-18.04.5-preinstalled-server-arm64+raspi4.img",
    "size_human": "2.5GiB",
    "size": 2653289472,
    "partitions": [
      {
        "index": 0,
        "filesystem": "fat32",
        "path": "/tmp/images/ubuntu-18.04.5-preinstalled-server-arm64+raspi4.img1",
        "bootable": true,
        "start": 2048,
        "end": 526335,
        "length": 524288,
        "type": 0
      },
      {
        "index": 1,
        "filesystem": "ext4",
        "path": "/tmp/images/ubuntu-18.04.5-preinstalled-server-arm64+raspi4.img2",
        "bootable": false,
        "start": 526336,
        "end": 5182171,
        "length": 4655836,
        "type": 0
      }
    ]
  }
}
```

## Requirements

Graven requires modern linux including [losetup](https://www.linux.org/docs/man8/losetup.html) and friends, plus root.

Root is required because for some distros, non-root members of the `disk` group may still have trouble with mount & umount.. YMMV

## Installation

```
pip install -e git+ssh://git@github.com/elo-enterprises/graven@master#egg=graven
```

## Example Usage

```
$ graven --help

Usage: graven [OPTIONS] COMMAND [ARGS]...

  Tool for working with images. For more detail, use --help on subcommands.

Options:
  --help  Show this message and exit.

Commands:
  block
  cache     Caches IMG in graven work dir (to avoid in-place changes)
  clean     cleans unused internal mount directories
  copy      Copies SRC_PATH into img@ dest_path
  detach    detaches img if attached
  flash     Flashes IMG (or SRC_DEV) to DEST_DEV
  ls        Returns information for given img, including number of...
  mount     Mounts an image to optional destination.
  split     Splits a composite IMG into 1 image per partition
  status    Returns status, including graven-managed mounts, cache, etc
  umount    Unmounts an IMG from optional path.
  versions  Returns version info for graven, libparted, etc
  b         ALIAS for `block`
  cp        ALIAS for `copy`
  d         ALIAS for `detach`
  fl        ALIAS for `flash`
  list      ALIAS for `ls`
  m         ALIAS for `mount`
  st        ALIAS for `status`
  stat      ALIAS for `status`
  u         ALIAS for `umount`
  w         ALIAS for `block`
  wait      ALIAS for `block`
```

## Development Notes

**Building Documentation:** This documentation, with the latest command line help, is built using `make docs`.

**Invocation for developers:** Note that usage generally requires root, so if you're doing development or you just prefer to install to a virtualenv owned by your normal user, this is a useful way to invoke graven:

```
user@host[virtualenv]$ sudo `which graven` ...graven subcommands...
```

## Future Work

* Ansible integration or just examples, for provisioning on top of base images
* Cloud-init integration, for pushing [nocloud configuration](https://cloudinit.readthedocs.io/en/latest/topics/datasources/nocloud.html) into boot partitions of base images (Ubuntu now supports this out of the box!)
* Graven-get-image commands, featuring automatic usage of the cache folders and automatic decompression
