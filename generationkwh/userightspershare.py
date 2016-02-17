# -*- coding: utf-8 -*-

# TODO:
# - total active shares in a day = 0

import numpy

class UserRightsPerShare(object):
    """
        Provides the hourly curve of kWh available for a member
        with a given number of shares.
    """
    def __init__(self, production, activeShares):
        self._production = production
        self._activeShares = activeShares

    def get(self, nshares, start, end):
        hoursADay = 25
        return self._production.get(start, end)/self._activeShares.hourly(None, start, end)*nshares//1000


import unittest
import datetime

class Curve_MockUp(object):
    def __init__(self, value):
        self._value = numpy.array(value)

    def get(self, *args, **kwd):
        return self._value

    def hourly(self, *args, **kwd):
        return self._value


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

    def _test_get_withRemainder(self):
        self.assertUserRightsPerShareEquals(
            production = 25*[500],
            activeShares = 25*[1],
            nShares=1,
            start='2015-01-02',
            end='2015-01-02',
            expected = 12*[0,1]+[0],
            )



# vim: ts=4 sw=4 et
