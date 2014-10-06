import unittest
from nose import tools
import raid_health
import os

ME = os.path.dirname(__file__)
FIXTURES = os.path.join(ME, 'fixtures')


class Base(unittest.TestCase):

    mdstat = None

    def setUp(self):
        self.PARTITIONS = raid_health.PARTITIONS
        raid_health.PARTITIONS = os.path.join(FIXTURES, 'partitions')
        self.MDSTAT = raid_health.MDSTAT
        raid_health.MDSTAT = os.path.join(FIXTURES, 'mdstat_' + self.mdstat)

    def tearDown(self):
        raid_health.PARTITIONS = self.PARTITIONS
        raid_health.MDSTAT = self.MDSTAT


class TestNormalState(Base):

    mdstat = 'normal'

    def test_get_arrays(self):
        arrs = raid_health.get_arrays()
        tools.eq_(len(arrs), 2)
        tools.eq_(arrs[0], 'md0')
        tools.eq_(arrs[1], 'md1')

    def test_get_used_hdds(self):
        hdds = raid_health.get_used_hdds()
        tools.eq_(len(hdds), 4)
        tools.eq_(hdds[0], 'sda1')

    def test_find_hotspare_hdd(self):
        tools.eq_(raid_health.find_hotspare_hdd(), 'sda3')

    def test_has_partitions(self):
        tools.eq_(raid_health.has_partitions('sdc'), False)
        tools.eq_(raid_health.has_partitions('sda'), True)


class TestNoHotspareState(Base):

    mdstat = 'full'

    def test_find_hotspare_hdd(self):
        tools.eq_(raid_health.find_hotspare_hdd(), None)


class TestFailedState(Base):

    mdstat = 'failed'

    def test_find_failed_hdd(self):
        tools.eq_(raid_health.find_failed_hdd(), ('md0', 'sdb1'))

    def test_find_hotspare_hdd(self):
        tools.eq_(raid_health.find_hotspare_hdd(), 'sda3')
