#!/usr/bin/env python2

from vdo_exporter import VDOStats

stats = VDOStats()
stats.collect()
print stats.formatted()


