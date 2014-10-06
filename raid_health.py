#!/usr/bin/env python
# Consider running under root user

from __future__ import print_function
import re
import sys
import subprocess

MDSTAT = '/proc/mdstat'
PARTITIONS = '/proc/partitions'

MDADM_CMD = 'mdadm {args} /dev/{arr} /dev/{hdd}'

DISK =  r'[a-z]+'
DEV = r'{0}[\d]*'.format(DISK)
ARR_LEG_DEV = r'({0})\[\d\]'.format(DEV)

failed_dev_re = re.compile(r'{0}\(F\)'.format(ARR_LEG_DEV))
arr_dev_re = re.compile(r'^(md[\d])')
arr_leg_re = re.compile(ARR_LEG_DEV)
partition_re = re.compile(r'({0})$'.format(DEV))

def mdadm(op, arr, hdd):
    args = []
    if op == 'remove':
        args.append('-r')
    elif op == 'add':
        args.append('-a')

    return subprocess.call(MDADM_CMD.format(
        args=' '.join(args), arr=arr, hdd=hdd), shell=True)

def mdstat_iter():
    with open(MDSTAT, 'r') as f:
        for line in f:
            yield line.strip()

def partitions_iter():
    with open(PARTITIONS, 'r') as f:
        for line_num, line in enumerate(f):
            # Skip first "header" line
            if line_num == 0:
                continue

            m = partition_re.search(line.strip())
            if m:
                yield m.group()

def get_arrays():
    arrays = []
    for line in mdstat_iter():
        arrays.extend(re.findall(arr_dev_re, line))

    return arrays

def get_used_hdds():
    used_hdds = []
    for line in mdstat_iter():
        if arr_dev_re.match(line):
            used_hdds.extend(re.findall(arr_leg_re, line))
    return used_hdds

def find_failed_hdd():
    for line in mdstat_iter():
        m = failed_dev_re.search(line)
        if m:
            # (arr, hdd)
            return (arr_dev_re.match(line).groups()[0], m.groups()[0])
    return None

def has_partitions(disk):
    for hdd in partitions_iter():
        if hdd.startswith(disk) and len(disk) != len(hdd):
            return True
    return False

def find_hotspare_hdd():
    used_hdds = get_used_hdds()
    arrays = get_arrays()
    for item in partitions_iter():
        if re.match(DISK, item):
            # Do not use disk with partitions
            if has_partitions(item):
                continue

        # Skip md arrays
        if item in arrays:
            continue

        if item not in used_hdds:
            return item

    return None

if __name__ == '__main__':
    failed = find_failed_hdd()
    if failed is None:
        sys.exit(1)

    failed_arr, failed_hdd = failed
    print('Found failed hdd(`{0}`) in array(`{1}`)'.format(
        failed_hdd, failed_arr), file=sys.stderr)

    hotspare_hdd = find_hotspare_hdd()
    if hotspare_hdd is None:
        raise RuntimeError('No hotspare hdd available!')

    mdadm('remove', arr=failed_arr, hdd=failed_hdd)
    mdadm('add', arr=failed_arr, hdd=hotspare_hdd)
    print('Replaced failed hdd(`{0}`) in array(`{1}`) with available hotspare device(`{2}`)'.format(
        failed_hdd, failed_arr, hotspare_hdd))
