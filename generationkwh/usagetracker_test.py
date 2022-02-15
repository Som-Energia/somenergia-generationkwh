# -*- coding: utf-8 -*-

from .usagetracker import UsageTracker
from .isodates import isodate, utcisodatetime
import unittest


class CurveProvider_MockUp(object):

    def __init__(self, data):
        self._data = data

    def usage(self, member, start, end):
        return self._data[:]

    def updateUsage(self, member, start, data):
        self._data[:] = data

    def rights_kwh(self, member, start, end):
        return self._data

    def periodMask(self, fare, period, start, end):
        return self._data



# Readable verbose testcase listing
unittest.TestCase.__str__ = unittest.TestCase.id


class UsageTracker_Test(unittest.TestCase):

    def setupUsageTracker(self, rights, usage, periodMask):
        self.today = isodate('2015-01-02')
        self.today_str = self.today.strftime('%Y-%m-%d %H:%M:%S')
        self.today_1h = utcisodatetime('2015-01-02 01:00:00')
        self.today_1h_str = self.today_1h.strftime('%Y-%m-%d %H:%M:%S')
        return UsageTracker(
            rights=CurveProvider_MockUp(rights),
            usage=CurveProvider_MockUp(usage),
            periodMask=CurveProvider_MockUp(periodMask),
            )

    def test_available_noProduction(self):
        t = self.setupUsageTracker(
            rights=[0,0],
            usage=[0,0],
            periodMask=[1,1],
            )
        kwh = t.available_kwh('soci', self.today, self.today, '2.0A', 'P1')
        self.assertEqual(kwh, 0)

    def test_available_singleBinProduction(self):
        t = self.setupUsageTracker(
            rights=[2,0],
            usage=[0,0],
            periodMask=[1,1],
            )

        kwh = t.available_kwh('soci', self.today, self.today, '2.0A', 'P1')
        self.assertEqual(kwh, 2)

    def test_available_manyBinsProduction_getAdded(self):
        t = self.setupUsageTracker(
            rights=[2,3],
            usage=[0,0],
            periodMask=[1,1],
            )

        kwh = t.available_kwh('soci', self.today, self.today, '2.0A', 'P1')
        self.assertEqual(kwh, 5)


    def test_available_masked(self):
        t = self.setupUsageTracker(
            rights=[2,3],
            usage=[0,0],
            periodMask=[0,1],
            )

        kwh = t.available_kwh('soci', self.today, self.today, '2.0A', 'P1')
        self.assertEqual(kwh, 3)

    def test_available_manyBinsProduction_used(self):
        t = self.setupUsageTracker(
            rights=[2,3],
            usage=[1,0],
            periodMask=[1,1],
            )

        kwh = t.available_kwh('soci', self.today, self.today, '2.0A', 'P1')
        self.assertEqual(kwh, 4)

    def test_available_manyBinsProduction_usedMasked(self):
        t = self.setupUsageTracker(
            rights=[5,3],
            usage=[2,1],
            periodMask=[0,1],
            )

        kwh = t.available_kwh('soci', self.today, self.today, '2.0A', 'P1')
        self.assertEqual(kwh, 2)

    def test_use_halfBin(self):
        t = self.setupUsageTracker(
            rights=[5,3],
            usage=[0,0],
            periodMask=[1,1],
            )

        real, data  = t.use_kwh_with_dates_dict('soci', self.today, self.today, '2.0A', 'P1', 4)
        self.assertEqual(
            [4,0], t.usage('soci', self.today, self.today))
        self.assertEqual(real, 4)
        self.assertEqual(data, {self.today_str: 4})

    def test_use_fullBin(self):
        t = self.setupUsageTracker(
            rights=[5,3],
            usage=[0,0],
            periodMask=[1,1],
            )

        real, data = t.use_kwh_with_dates_dict('soci', self.today, self.today, '2.0A', 'P1', 5)
        self.assertEqual(
            [5,0], t.usage('soci', self.today, self.today))
        self.assertEqual(data, {self.today_str: 5})
        self.assertEqual(5, real)

    def test_use_pastBin(self):
        t = self.setupUsageTracker(
            rights=[5,3],
            usage=[0,0],
            periodMask=[1,1],
            )

        real, data  = t.use_kwh_with_dates_dict('soci', self.today, self.today, '2.0A', 'P1', 6)
        self.assertEqual(
            [5,1], t.usage('soci', self.today, self.today))
        self.assertEqual(data, {self.today_str: 5, self.today_1h_str: 1 })
        self.assertEqual(6, real)

    def test_use_beyondAvailable(self):
        t = self.setupUsageTracker(
            rights=[5,3],
            usage=[0,0],
            periodMask=[1,1],
            )

        real, data  = t.use_kwh_with_dates_dict('soci', self.today, self.today, '2.0A', 'P1', 9)
        self.assertEqual(
             [5,3], t.usage('soci', self.today, self.today))
        self.assertEqual(data, {self.today_str: 5, self.today_1h_str: 3 })
        self.assertEqual(8, real)

    def test_use_previouslyUsed(self):
        t = self.setupUsageTracker(
            rights=[5,3],
            usage=[1,0],
            periodMask=[1,1],
            )

        real, data  = t.use_kwh_with_dates_dict('soci', self.today, self.today, '2.0A', 'P1', 2)
        self.assertEqual(
             [3,0], t.usage('soci', self.today, self.today))
        self.assertEqual(data, {self.today_str: 2})
        self.assertEqual(2, real)

    def test_use_previouslyUsedDifferentMask(self):
        t = self.setupUsageTracker(
            rights=[5,3],
            usage=[1,0],
            periodMask=[0,1],
            )

        real, data  = t.use_kwh_with_dates_dict('soci', self.today, self.today, '2.0A', 'P1', 2)
        self.assertEqual(
             [1,2], t.usage('soci', self.today, self.today))
        self.assertEqual(data, {self.today_1h_str: 2})
        self.assertEqual(2, real)

    def test_refund_singleBin(self):
        t = self.setupUsageTracker(
            rights=[5,3],
            usage=[3,0],
            periodMask=[1,1],
            )

        real, data = t.refund_kwh_with_dates_dict('soci', self.today, self.today, '2.0A', 'P1', 2)
        self.assertEqual(
             [1,0], t.usage('soci', self.today, self.today))
        self.assertEqual(2, real)
        self.assertEqual(data, {self.today_str: -2})

    def test_refund_severalBins_refundsBackward(self):
        t = self.setupUsageTracker(
            rights=[3,5],
            usage=[2,2],
            periodMask=[1,1],
            )

        real, data = t.refund_kwh_with_dates_dict('soci', self.today, self.today, '2.0A', 'P1', 3)
        self.assertEqual(
             [1,0], t.usage('soci', self.today, self.today))
        self.assertEqual(3, real)
        self.assertEqual(data, {self.today_str: -1, self.today_1h_str: -2})

    def test_refund_beyondUsed(self):
        t = self.setupUsageTracker(
            rights=[5,3],
            usage=[2,2],
            periodMask=[1,1],
            )

        real, data = t.refund_kwh_with_dates_dict('soci', self.today, self.today, '2.0A', 'P1', 5)
        self.assertEqual(
             [0,0], t.usage('soci', self.today, self.today))
        self.assertEqual(4, real)
        self.assertEqual(data, {self.today_str: -2, self.today_1h_str: -2})

    def test_refund_masked(self):
        t = self.setupUsageTracker(
            rights=[5,3],
            usage=[2,2],
            periodMask=[0,1],
            )

        real, data = t.refund_kwh_with_dates_dict('soci', self.today, self.today, '2.0A', 'P1', 2)
        self.assertEqual(
             [2,0], t.usage('soci', self.today, self.today))
        self.assertEqual(data, {self.today_1h_str: -2})
        self.assertEqual(2, real)


# vim: ts=4 sw=4 et
