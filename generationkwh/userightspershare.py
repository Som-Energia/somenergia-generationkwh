# -*- coding: utf-8 -*-

# TODO:
# - total active shares in a day = 0
# - non-adjacent cache and production

import numpy

class UserRightsPerShare(object):
    """
        Provides the hourly curve of kWh available for a member
        with a given number of shares.
    """
    def __init__(self, production=None, activeShares=None, cache=None):
        self._production = production
        self._activeShares = activeShares
        self._cache = cache

    def computeRights(self, production, activeShares, nshares=1, remainder=0):

        assert production.dtype == 'int64', "Production base type is not integer"
        assert activeShares.dtype == 'int64', "ActiveShares base type is not integer"

        with numpy.errstate(divide='ignore'):
            fraction = production*nshares/activeShares
        fraction = numpy.concatenate( ([remainder],fraction) )
        integral = fraction.cumsum()

        result = numpy.diff(integral//1000)
        remainder = integral[-1]%1000

        return result, remainder

    def get(self, nshares, start, end):
        cacheDate, cacheRemainder = self._cache.lastRemainder(nshares) if self._cache else (None, 0)

        productionStart = start if cacheDate is None else max(start, cacheDate+datetime.timedelta(days=1))

        production = self._production.get(productionStart, end)
        activeShares = self._activeShares.hourly(None, start, end)

        result, remainder = self.computeRights(
            production = production,
            activeShares = activeShares,
            nshares = nshares,
            remainder = cacheRemainder,
            )

        if self._cache is None:
            return result

        self._cache.update(nshares, result, end, remainder)
        return self._cache.get(nshares, start, end)


import unittest
import datetime

class Curve_MockUp(object):
    def __init__(self, value):
        self._value = numpy.array(value)

    def get(self, *args, **kwd):
        return self._value

    def hourly(self, *args, **kwd):
        return self._value

class Cache_Mockup(object):
    def __init__(self, curve, date, remainder):
        self._curve = curve
        self._date = date
        self._remainder = remainder

    def lastRemainder(self, nShares):
        return self._date, self._remainder

    def get(self, nShares, start=None, end=None):
        return self._curve

    def update(self, nShares, curve, end, remainder):
        self._curve = numpy.concatenate((self._curve, curve))
        self._date = end
        self._remainder = remainder


def isodate(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()


class UserRightsPerShare_Test(unittest.TestCase):

    def assertComputeEquals(self,
        production,
        activeShares,
        nShares,
        expected,
        expectedRemainder=0,
        remainder = 0,
        ):

        curve = UserRightsPerShare()
        result, resultingRemainder = curve.computeRights(
            production=numpy.array(production),
            activeShares = numpy.array(activeShares),
            nshares=nShares,
            remainder = remainder,
            )
        self.assertEqual(list(result), expected)
        self.assertEqual(resultingRemainder, expectedRemainder)

    def test_computeRights_noProduction(self):
        self.assertComputeEquals(
            production = 25*[0],
            activeShares = 25*[1],
            nShares=1,
            expected = 25*[0],
            )

    def test_computeRights_uniformProduction(self):
        self.assertComputeEquals(
            production = 25*[2000],
            activeShares = 25*[1],
            nShares=1,
            expected = 25*[2],
            )

    def test_computeRights_sharedProduction(self):
        self.assertComputeEquals(
            production = 25*[2000],
            activeShares = 25*[2],
            nShares=1,
            expected = 25*[1],
            )

    def test_computeRights_withManyShares(self):
        self.assertComputeEquals(
            production = 25*[2000],
            activeShares = 25*[2],
            nShares=2,
            expected = 25*[2],
            )

    def test_computeRights_withInnerRemainder(self):
        self.assertComputeEquals(
            production = 24*[1000]+[0],
            activeShares = 25*[2],
            nShares=1,
            expected = 12*[0,1]+[0],
            )

    def test_computeRights_withNoShare(self):
        self.assertComputeEquals(
            production = 25*[1000],
            activeShares = 10*[0] + 15*[1],
            nShares=1,
            expected = 10*[0]+15*[1],
            )

    def test_computeRights_creatingRemainder(self):
        self.assertComputeEquals(
            production = 25*[500],
            activeShares = 25*[1],
            nShares=1,
            expected = 12*[0,1]+[0],
            expectedRemainder = 500,
            )

    def test_computeRights_takingRemainder(self):
        self.assertComputeEquals(
            remainder = 500.0,
            production = 25*[500],
            activeShares = 25*[1],
            nShares=1,
            expected = 12*[1,0]+[1],
            expectedRemainder = 0,
            )

    def test_get_floatProductionFailsAssertion(self):
        curve = UserRightsPerShare()
        with self.assertRaises(AssertionError) as failure:
            curve.computeRights(
                production = numpy.array([3.2]),
                activeShares  = numpy.array([3]),
                nshares=1,
                remainder = 0,
                )
        self.assertEqual(failure.exception.args[0],
            "Production base type is not integer")

    def test_get_floatSharesFailsAssertion(self):
        curve = UserRightsPerShare()
        with self.assertRaises(AssertionError) as failure:
            curve.computeRights(
                production = numpy.array([3]),
                activeShares  = numpy.array([3.2]),
                nshares = 1,
                remainder = 0,
                )
        self.assertEqual(failure.exception.args[0],
            "ActiveShares base type is not integer")


    def assertUserRightsPerShareEquals(self,
        production,
        activeShares,
        nShares,
        start,
        end,
        expected
        ):

        curve = UserRightsPerShare(
            production = Curve_MockUp(production),
            activeShares = Curve_MockUp(activeShares),
            )
        result = curve.get(
            nshares=nShares,
            start=isodate(start),
            end=isodate(end),
            )
        self.assertEqual(list(result), expected)

    def test_get_noProduction(self):
        self.assertUserRightsPerShareEquals(
            production = 25*[0],
            activeShares = 25*[1],
            nShares=1,
            start='2015-01-02',
            end='2015-01-02',
            expected = 25*[0],
            )

    def test_get_uniformProduction(self):
        self.assertUserRightsPerShareEquals(
            production = 25*[2000],
            activeShares = 25*[1],
            nShares=1,
            start='2015-01-02',
            end='2015-01-02',
            expected = 25*[2],
            )

    def test_get_sharedProduction(self):
        self.assertUserRightsPerShareEquals(
            production = 25*[2000],
            activeShares = 25*[2],
            nShares=1,
            start='2015-01-02',
            end='2015-01-02',
            expected = 25*[1],
            )

    def test_get_withManyShares(self):
        self.assertUserRightsPerShareEquals(
            production = 25*[2000],
            activeShares = 25*[2],
            nShares=2,
            start='2015-01-02',
            end='2015-01-02',
            expected = 25*[2],
            )

    def test_get_withRemainder(self):
        self.assertUserRightsPerShareEquals(
            production = 25*[1000],
            activeShares = 25*[2],
            nShares=1,
            start='2015-01-02',
            end='2015-01-02',
            expected = 12*[0,1]+[0],
            )

    def test_get_withNoShare(self):
        self.assertUserRightsPerShareEquals(
            production = 25*[1000],
            activeShares = 10*[0] + 15*[1],
            nShares=1,
            start='2015-01-02',
            end='2015-01-02',
            expected = 10*[0]+15*[1],
            )


    def assertCachedResults(self,
        cache,
        cacheDate,
        cacheRemainder,
        production,
        activeShares,
        nShares,
        start,
        end,
        expected,
        expectedCache,
        expectedCacheDate,
        expectedCacheRemainder,
        ):

        cache = Cache_Mockup(numpy.array(cache), cacheDate and isodate(cacheDate), cacheRemainder)

        curve = UserRightsPerShare(
            production = Curve_MockUp(production),
            activeShares = Curve_MockUp(activeShares),
            cache = cache,
            )
        result = curve.get(
            nshares=nShares,
            start=isodate(start),
            end=isodate(end),
            )
        self.assertEqual(list(result), expected)
        self.assertEqual(list(cache.get(nShares)), expectedCache)
        self.assertEqual(cache.lastRemainder(nShares),
            (isodate(expectedCacheDate), expectedCacheRemainder))


    def test_cache_with_nocache(self):
        self.assertCachedResults(
            cache = [],
            cacheDate = None,
            cacheRemainder = 0.0,
            production = 25*[1000],
            activeShares = 25*[1],
            nShares=1,
            start='2015-01-02',
            end='2015-01-02',
            expected = 25*[1],
            expectedCache = 25*[1],
            expectedCacheDate = '2015-01-02',
            expectedCacheRemainder = 0,
            )

    def test_cache_creatingRemainder(self):
        self.assertCachedResults(
            cache = [],
            cacheDate = None,
            cacheRemainder = 0.0,
            production = 25*[500],
            activeShares = 25*[1],
            nShares=1,
            start='2015-01-02',
            end='2015-01-02',
            expected = 12*[0,1]+[0],
            expectedCache = 12*[0,1]+[0],
            expectedCacheDate = '2015-01-02',
            expectedCacheRemainder = 500,
            )

    def test_cache_takingRemainder(self):
        self.assertCachedResults(
            cache = [],
            cacheDate = '2015-01-01',
            cacheRemainder = 500.0,
            production = 25*[500],
            activeShares = 25*[1],
            nShares=1,
            start='2015-01-02',
            end='2015-01-02',
            expected = 12*[1,0]+[1],
            expectedCache = 12*[1,0]+[1],
            expectedCacheDate = '2015-01-02',
            expectedCacheRemainder = 0,
            )

    def test_cache_usingCacheData(self):
        self.assertCachedResults(
            cache = 25*[8],
            cacheDate = '2015-01-01',
            cacheRemainder = 0,
            production = 25*[1000],
            activeShares = 25*[1],
            nShares=1,
            start='2015-01-01',
            end='2015-01-02',
            expected = 25*[8] + 25*[1],
            expectedCache = 25*[8] + 25*[1],
            expectedCacheDate = '2015-01-02',
            expectedCacheRemainder = 0,
            )




# vim: ts=4 sw=4 et
