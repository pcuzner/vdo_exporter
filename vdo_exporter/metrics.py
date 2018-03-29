#!/usr/bin/env python2

from .vdo import VDORoot
import time


class Metric(object):
    def __init__(self, vhelp, vtype):
        self.var_help = vhelp
        self.var_type = vtype
        self.data = []

    def add(self, labels=None, value=0):
        if not labels:
            labels = dict()

        _d = dict(labels=labels,
                  value=value)
        self.data.append(_d)
    pass


class VDOStats(object):

    def __init__(self):
        self.metrics = dict()
        self.kvdo = VDORoot()

    def collect(self):

        summary = Metric("time taken to scrape VDO stats (secs)",
                         "gauge")
        stime = time.time()

        self._get_vol_stats()

        etime = time.time()

        # labels = {"host": socket.gethostname().split('.')[0]}
        summary.add(value=(etime - stime))

        self.metrics["vdo_exporter_scrape_duration_seconds"] = summary

    def formatted(self):
        s = ''
        for m_name in sorted(self.metrics.keys()):
            metric = self.metrics[m_name]
            s += "#HELP: {} {}\n".format(m_name,
                                         metric.var_help)
            s += "#TYPE: {} {}\n".format(m_name,
                                         metric.var_type)

            for v in metric.data:
                labels = []
                for n in v['labels'].items():
                    label_name = '{}='.format(n[0])
                    label_value = '"{}"'.format(n[1])

                    labels.append('{}{}'.format(label_name,
                                                label_value))

                s += "{}{{{}}} {}\n".format(m_name,
                                            ','.join(labels),
                                            v["value"])

        return s.rstrip()

    def _get_vol_stats(self):

        bin2bool = {0: "N",
                    1: "Y"
                    }

        savings_percent = Metric("Percentage space savings", "gauge")
        used_percent = Metric("Percentage of physical space consumed", "gauge")
        physical_size = Metric("Physical size (bytes)", "gauge")
        physical_used = Metric("Physical space used (bytes)", "gauge")
        overhead_used = Metric("Meta data overhead (bytes)", "gauge")
        logical_size = Metric("Logical size (bytes)", "gauge")
        logical_used = Metric("Logical space used (bytes)", "gauge")
        memory_used = Metric("Memory used by the volume (bytes)", "gauge")
        cache_hits = Metric("Read cache hits to the volume", "gauge")
        volume_metadata = Metric("Volume meta data", "gauge")
        no_space_count = Metric("Volume no space error count", "gauge")
        volume_errors = Metric("Volume error total (PBN + read-only + "
                               "nospace)", "gauge")
        write_amplification = Metric("Write amplication (user writes vs "
                                     "system writes)", "gauge")

        for vol in self.kvdo.volumes:

            blksz = vol.get_stat('block_size')
            # l_blksz = vol.get_stat('logical_block_size')
            phys_bytes = vol.get_stat('physical_blocks') * blksz
            phys_used = vol.get_stat('data_blocks_used') * blksz
            overhead_bytes = vol.get_stat('overhead_blocks_used') * blksz
            log_bytes = vol.get_stat('logical_blocks') * blksz
            log_used = vol.get_stat('logical_blocks_used') * blksz
            mem_used = vol.get_stat('memory_usage_bytes_used')
            no_space_errors = vol.get_stat('errors_no_space_error_count')
            invalid_PBN = vol.get_stat('errors_invalid_advicePBNCount')
            read_only = vol.get_stat('errors_read_only_error_count')
            error_total = no_space_errors + invalid_PBN + read_only
            write_policy = vol.get_stat('write_policy')
            read_cache_hits = vol.get_stat('read_cache_hits')

            try:
                write_amp = ((vol.get_stat('bios_meta_write') +
                             vol.get_stat('bios_out_write')) /
                             float(vol.get_stat('bios_in_write')))
            except ZeroDivisionError:
                write_amp = 0

            recovery_active = bin2bool[vol.get_stat('in_recovery_mode')]
            journal_full = bin2bool[vol.get_stat('journal_disk_full')]
            mode = vol.get_stat('mode')

            labels = {"vol_name": vol.name}
            metadata_labels = {"vol_name": vol.name,
                               "backing_device": vol.backing_device,
                               "dm_holder": vol.dm_holder,
                               "compression": vol.compression,
                               "dedupe": vol.dedupe,
                               "mode": mode,
                               "recovery_active": recovery_active,
                               "journal_full": journal_full,
                               "write_policy": write_policy}

            # For new volumes logical blocks could be zero, so catch it
            try:
                saving = (100 * (vol.get_stat("logical_blocks_used") -
                                 vol.get_stat("data_blocks_used")) /
                          vol.get_stat("logical_blocks_used"))
            except ZeroDivisionError:
                saving = 0

            used_pct = int((100 * (vol.get_stat("data_blocks_used") +
                                   vol.get_stat("overhead_blocks_used")) /
                           vol.get_stat("physical_blocks")) + 0.5)

            savings_percent.add(labels, saving)
            used_percent.add(labels, used_pct)
            physical_size.add(labels, phys_bytes)
            physical_used.add(labels, phys_used)
            overhead_used.add(labels, overhead_bytes)
            logical_size.add(labels, log_bytes)
            logical_used.add(labels, log_used)
            memory_used.add(labels, mem_used)
            cache_hits.add(labels, read_cache_hits)
            volume_metadata.add(metadata_labels, 0)
            no_space_count.add(labels, no_space_errors)
            volume_errors.add(labels, error_total)
            write_amplification.add(labels, write_amp)

        self.metrics['vdo_exporter_volume_savings_percent'] = savings_percent
        self.metrics['vdo_exporter_volume_physical_bytes'] = physical_size
        self.metrics['vdo_exporter_volume_physical_bytes_used'] = physical_used
        self.metrics['vdo_exporter_volume_overhead_bytes'] = overhead_used
        self.metrics['vdo_exporter_volume_logical_bytes'] = logical_size
        self.metrics['vdo_exporter_volume_logical_bytes_used'] = logical_used
        self.metrics['vdo_exporter_volume_memory_used'] = memory_used
        self.metrics['vdo_exporter_volume_read_cache_hits'] = cache_hits
        self.metrics['vdo_exporter_volume_metadata'] = volume_metadata
        self.metrics['vdo_exporter_volume_error_total'] = volume_errors
        self.metrics['vdo_exporter_volume_no_space_error_total'] = \
            no_space_count
        self.metrics['vdo_exporter_volume_write_amplication'] = \
            write_amplification
        self.metrics['vdo_exporter_volume_used_percent'] = used_percent
