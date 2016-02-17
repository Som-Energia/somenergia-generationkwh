# -*- coding: utf-8 -*-

# TODO:
# - total active shares in a day = 0
# - consider successive remainders
# - caching values

import numpy

class UserRightsPerShare(object):
    """
        Provides the hourly curve of kWh available for a member
        with a given number of shares.
    """
    def __init__(self, production, activeShares, cache=None):
        self._production = production
        self._activeShares = activeShares
        self._cache = cache

    def get(self, nshares, start, end):
        hoursADay = 25
        activeShares = self._activeShares.hourly(None, start, end)
        production = self._production.get(start, end)

        fraction = production*nshares/activeShares
        fraction = numpy.concatenate( ([0],fraction) )
        return numpy.diff(fraction.cumsum()//1000)


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

    def get(self, nshares, start, end):
        return self._curve


def isodate(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()


class UserRightsPerShare_Test(unittest.TestCase):

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
        cache = Cache_Mockup(cache, cacheDate, cacheRemainder)

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

    def test_cache(self):
        self.assertCachedResults(
            cache = [],
            cacheDate = None,
            cacheRemainder = 0.0,
            production = 25*[1000],
            activeShares = 25*[1],
            nShares=1,
            start='2015-01-02',
            end='2015-01-02',
            expected = 12*[0,1]+[0],
            expectedCache = 12*[0,1]+[0],
            expectedCacheDate = '2015-01-02',
            expectedCacheRemainder = 0,
            )





# vim: ts=4 sw=4 et
