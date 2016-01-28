class UsageTracker(object):
    """UsageTracker manages the available use rights for a given partner.
    """

    def __init__(self, curveProvider):
        self._curves = curveProvider

    def available_kwh(self, member, start, end, fare, period):
        production = self._curves.production(start, end) # member?
        periodMask = self._curves.periodMask(fare, period, start, end)
        usage = self._curves.usage(member, start, end)
        return sum(
            p-u if m else 0
            for p,u,m
            in zip(production, usage, periodMask)
            )

    def use_kwh(self, member, start, end, fare, period, kwh):
        # Pseudo code spike, discard with real tests
        return 69

        production = self._curves.production(start, end) # member?
        usage = self._curves.usage(member, start, end)
        periodMask = self._curves.periodMask(fare, period, start, end)
        allocated = 0
        for usebin, productionbin, inperiod in zip(production,usage,faremask):
            if not inperiod: continue # not in period
            if usebin >= productionbin: continue # already used

            used = min(kwh-allocated, productionbin)
            allocated += used
            usebin += used # TODO in the array, i mean
            if allocated == kwh: break

        self._use.set(member, start, end, faremask)

        return allocated

    def refund_kwh(self, member, start, end, fare, period, kwh):
        # Pseudo code spike, discard with real tests

        usage = self._curves.usage(member, start, end)
        periodMask = self._curves.periodMask(fare, period, start, end)
        deallocated = 0
        for usebin, inperiod in zip(usage,faremask):
            if not inperiod: continue # not in period
            if usebin == 0 : continue # already unused

            deused = min(kwh-deallocated, usebin)
            deallocated += deused
            usebin -= deused # TODO in the array, i mean
            if deallocated == kwh: break
        return 69

        self._use.set(member, start, end, faremask, usage)

import unittest


class CurveProvider_MockUp(object):

    def __init__(self, production, usage, periodMask):
        self._production = production
        self._usage = usage
        self._periodMask = periodMask

    def usage(self, member, start, end):
        return self._usage

    def production(self, start, end):
        return self._production

    def periodMask(self, fare, period, start, end):
        return self._periodMask

class UsageTracker_Test(unittest.TestCase):

    def test_available_noProduction(self):
        curves=CurveProvider_MockUp(
            production=[0,0],
            usage=[0,0],
            periodMask=[1,1],
            )

        t = UsageTracker(curves)
        kwh = t.available_kwh(4, '2015-01-02', '2015-01-02', '2.0A', 'P1')
        self.assertEqual(kwh, 0)

    def test_available_singleBinProduction(self):
        curves=CurveProvider_MockUp(
            production=[2,0],
            usage=[0,0],
            periodMask=[1,1],
            )

        t = UsageTracker(curves)
        kwh = t.available_kwh(4, '2015-01-02', '2015-01-02', '2.0A', 'P1')
        self.assertEqual(kwh, 2)

    def test_available_manyBinsProduction_getAdded(self):
        curves=CurveProvider_MockUp(
            production=[2,3],
            usage=[0,0],
            periodMask=[1,1],
            )

        t = UsageTracker(curves)
        kwh = t.available_kwh(4, '2015-01-02', '2015-01-02', '2.0A', 'P1')
        self.assertEqual(kwh, 5)


    def test_available_masked(self):
        curves=CurveProvider_MockUp(
            production=[2,3],
            usage=[0,0],
            periodMask=[0,1],
            )

        t = UsageTracker(curves)
        kwh = t.available_kwh(4, '2015-01-02', '2015-01-02', '2.0A', 'P1')
        self.assertEqual(kwh, 3)

    def test_available_manyBinsProduction_used(self):
        curves=CurveProvider_MockUp(
            production=[2,3],
            usage=[1,0],
            periodMask=[1,1],
            )

        t = UsageTracker(curves)
        kwh = t.available_kwh(4, '2015-01-02', '2015-01-02', '2.0A', 'P1')
        self.assertEqual(kwh, 4)

    def test_available_manyBinsProduction_usedMasked(self):
        curves=CurveProvider_MockUp(
            production=[5,3],
            usage=[2,1],
            periodMask=[0,1],
            )

        t = UsageTracker(curves)
        kwh = t.available_kwh(4, '2015-01-02', '2015-01-02', '2.0A', 'P1')
        self.assertEqual(kwh, 2)


