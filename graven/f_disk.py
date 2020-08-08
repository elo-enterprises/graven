###
#
###
import parted

def list(img, **kargs):
    """ lists img partitions """
    path = img
    device = parted.getDevice(path)
    (cylinders, heads, sectors) = device.biosGeometry
    sizeInBytes = device.length * device.sectorSize
    disk = parted.Disk(device)
    partlist = []
    for partition in disk.partitions:
        if partition.type == parted.PARTITION_PROTECTED or \
           partition.type == parted.PARTITION_METADATA or \
           partition.type == parted.PARTITION_FREESPACE:
            continue
        partlist.append((partition,
                         partition.path,
                         partition.getFlag(parted.PARTITION_BOOT),
                         partition.geometry.start,
                         partition.geometry.end,
                         partition.geometry.length,
                         partition.type,
                         partition.fileSystem))
    out = []
    for parts in partlist:
        pdict = {}
        (partition, path, bootable, start, end, length, ty, fs) = parts
        bootflag = '*' if bootable else ''
        fs_type = get_type(partition, fs)
        pdict.update(
            system=fs_type, path=path,
            bootable=bootable, start=start, end=end, length=length, ty=ty)
        out.append(pdict)
    return out

def get_type(partition, fs):
    """ """
    if fs is not None:
        return fs.type
    # no filesystem, check flags
    if partition.getFlag(parted.PARTITION_SWAP):
        return "Linux swap"
    elif partition.getFlag(parted.PARTITION_RAID):
        return "RAID"
    elif partition.getFlag(parted.PARTITION_LVM):
        return "Linux LVM"
    elif partition.getFlag(parted.PARTITION_HPSERVICE):
        return "HP Service"
    elif partition.getFlag(parted.PARTITION_PALO):
        return "PALO"
    elif partition.getFlag(parted.PARTITION_PREP):
        return "PREP"
    elif partition.getFlag(parted.MSFT_RESERVED):
        return "MSFT Reserved"
    else:
        return "unknown"
