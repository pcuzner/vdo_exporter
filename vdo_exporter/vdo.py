#!/usr/bin/env
import glob
import os


def fread(path):
    with open(path, 'r') as f:
        data = f.read().strip()

    if data.isdigit():
        data = int(data)

    return data


class VDORoot(object):

    def __init__(self, root='/sys/kvdo'):
        self.root = root

    @property
    def volumes(self):
        for _f in glob.iglob(os.path.join(self.root, '*')):
            if os.path.isdir(_f):
                volume = VDOVolume(_f)
                yield volume

    def get_attrib(self, attrib):
        assert attrib is not None, \
            "get_attrib called without an attrib"
        assert os.path.exists(os.path.join(self.root, attrib)), \
            "attrib requested does not exist"

        return fread(os.path.join(self.root, attrib))

    @property
    def list_attrib(self):
        attribs = list()
        for attr in glob.iglob(os.path.join(self.root, '*')):
            if os.path.isfile(attr):
                attribs.append(attr)
        return attribs

    def __repr__(self):
        return '<VDORoot {}>'.format(self.root)


class VDOVolume(object):
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)

    @property
    def list_stats(self):
        stats = list()
        for attr in glob.iglob(os.path.join(self.path, 'statistics', '*')):
            if os.path.isfile(attr):
                stats.append(os.path.basename(attr))
        return stats

    def get_stat(self, stat):
        assert stat is not None
        assert os.path.exists(os.path.join(self.path, 'statistics', stat))

        return fread(os.path.join(self.path, 'statistics', stat))

    @property
    def compression(self):
        _c = fread(os.path.join(self.path, 'compressing'))
        return 'Y' if _c == 1 else 'N'

    @property
    def dedupe(self):
        return fread(os.path.join(self.path, 'dedupe', 'status'))

    @property
    def backing_device(self):
        vdo_dev_path = '/dev/mapper/{}'.format(self.name)
        dm_device = os.path.basename(os.path.realpath(vdo_dev_path))
        slave_path = '/sys/block/{}/slaves/*'.format(dm_device)
        links = glob.glob(slave_path)
        assert len(links) == 1, "{} links found for {}".format(len(links),
                                                               dm_device)

        # something like this ../pci0000:00/0000:00:09.0/virtio4/block/vdb/vdb2
        real_dev = os.path.realpath(links[0]).split('/')[-2]
        return real_dev

    @property
    def dm_holder(self):
        vdo_dev_path = '/dev/mapper/{}'.format(self.name)
        dm_device = os.path.basename(os.path.realpath(vdo_dev_path))
        holders = glob.glob('/sys/block/{}/holders/*'.format(dm_device))
        if len(holders) == 1:
            return os.path.basename(holders[0])
        else:
            return ''

    def __repr__(self):
        return '<VDOVolume {}>'.format(self.name)
