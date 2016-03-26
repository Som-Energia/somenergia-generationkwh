# -*- coding: utf-8 -*-

from generationkwh.usagetracker import UsageTracker
import unittest


class CurveProvider_MockUp(object):

    def __init__(self, production, usage, periodMask):
        self._production = production
        self._usage = usage
        self._periodMask = periodMask

    def usage(self, member, start, end):
        return self._usage

    def production(self, member, start, end):
        return self._production

    def periodMask(self, fare, period, start, end):
        return self._periodMask


# Readable verbose testcase listing
unittest.TestCase.__str__ = unittest.TestCase.id


class UsageTracker_Test(unittest.TestCase):

    def setupUsageTracker(self, production, usage, periodMask):
        curves=CurveProvider_MockUp(
            production=production,
            usage=usage,
            periodMask=periodMask,
            )
        return UsageTracker(curves)

    def test_available_noProduction(self):
        t = self.setupUsageTracker(
            production=[0,0],
            usage=[0,0],
            periodMask=[1,1],
            )
        kwh = t.available_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1')
        self.assertEqual(kwh, 0)

    def test_available_singleBinProduction(self):
        t = self.setupUsageTracker(
            production=[2,0],
            usage=[0,0],
            periodMask=[1,1],
            )

        kwh = t.available_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1')
        self.assertEqual(kwh, 2)

    def test_available_manyBinsProduction_getAdded(self):
        t = self.setupUsageTracker(
            production=[2,3],
            usage=[0,0],
            periodMask=[1,1],
            )

        kwh = t.available_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1')
        self.assertEqual(kwh, 5)


    def test_available_masked(self):
        t = self.setupUsageTracker(
            production=[2,3],
            usage=[0,0],
            periodMask=[0,1],
            )

        kwh = t.available_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1')
        self.assertEqual(kwh, 3)

    def test_available_manyBinsProduction_used(self):
        t = self.setupUsageTracker(
            production=[2,3],
            usage=[1,0],
            periodMask=[1,1],
            )

        kwh = t.available_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1')
        self.assertEqual(kwh, 4)

    def test_available_manyBinsProduction_usedMasked(self):
        t = self.setupUsageTracker(
            production=[5,3],
            usage=[2,1],
            periodMask=[0,1],
            )

        kwh = t.available_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1')
        self.assertEqual(kwh, 2)

    def test_use_halfBin(self):
        t = self.setupUsageTracker(
            production=[5,3],
            usage=[0,0],
            periodMask=[1,1],
            )

        real = t.use_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1', 4)
        self.assertEqual(
            [4,0], t.usage('soci', '2015-01-02', '2015-01-02'))

    def test_use_fullBin(self):
        t = self.setupUsageTracker(
            production=[5,3],
            usage=[0,0],
            periodMask=[1,1],
            )

        real = t.use_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1', 5)
        self.assertEqual(
            [5,0], t.usage('soci', '2015-01-02', '2015-01-02'))
        self.assertEqual(5, real)

    def test_use_pastBin(self):
        t = self.setupUsageTracker(
            production=[5,3],
            usage=[0,0],
            periodMask=[1,1],
            )

        real = t.use_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1', 6)
        self.assertEqual(
            [5,1], t.usage('soci', '2015-01-02', '2015-01-02'))
        self.assertEqual(6, real)

    def test_use_beyondAvailable(self):
        t = self.setupUsageTracker(
            production=[5,3],
            usage=[0,0],
            periodMask=[1,1],
            )

        real = t.use_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1', 9)
        self.assertEqual(
             [5,3], t.usage('soci', '2015-01-02', '2015-01-02'))
        self.assertEqual(8, real)

    def test_use_previouslyUsed(self):
        t = self.setupUsageTracker(
            production=[5,3],
            usage=[1,0],
            periodMask=[1,1],
            )

        real = t.use_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1', 2)
        self.assertEqual(
             [3,0], t.usage('soci', '2015-01-02', '2015-01-02'))
        self.assertEqual(2, real)

    def test_use_previouslyUsed(self):
        t = self.setupUsageTracker(
            production=[5,3],
            usage=[1,0],
            periodMask=[0,1],
            )

        real = t.use_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1', 2)
        self.assertEqual(
             [1,2], t.usage('soci', '2015-01-02', '2015-01-02'))
        self.assertEqual(2, real)

    def test_refund_singleBin(self):
        t = self.setupUsageTracker(
            production=[5,3],
            usage=[3,0],
            periodMask=[1,1],
            )

        real = t.refund_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1', 2)
        self.assertEqual(
             [1,0], t.usage('soci', '2015-01-02', '2015-01-02'))
        self.assertEqual(2, real)

    def test_refund_severalBins_refundsBackward(self):
        t = self.setupUsageTracker(
            production=[3,5],
            usage=[2,2],
            periodMask=[1,1],
            )

        real = t.refund_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1', 3)
        self.assertEqual(
             [1,0], t.usage('soci', '2015-01-02', '2015-01-02'))
        self.assertEqual(3, real)

    def test_refund_beyondUsed(self):
        t = self.setupUsageTracker(
            production=[5,3],
            usage=[2,2],
            periodMask=[1,1],
            )

        real = t.refund_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1', 5)
        self.assertEqual(
             [0,0], t.usage('soci', '2015-01-02', '2015-01-02'))
        self.assertEqual(4, real)

    def test_refund_masked(self):
        t = self.setupUsageTracker(
            production=[5,3],
            usage=[2,2],
            periodMask=[0,1],
            )

        real = t.refund_kwh('soci', '2015-01-02', '2015-01-02', '2.0A', 'P1', 2)
        self.assertEqual(
             [2,0], t.usage('soci', '2015-01-02', '2015-01-02'))
        self.assertEqual(2, real)


# vim: ts=4 sw=4 et
