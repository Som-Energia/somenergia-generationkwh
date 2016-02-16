# -*- coding: utf-8 -*-

class UseRightsCurve(object):
    """
    """
    def __init__(self, activeShares, rightsPerAction, eager=False):
        self._activeShares = activeShares
        self._rightsPerAction = rightsPerAction
        self._eager = eager

    def get(self, member, start, end):
        if not self._eager:
            nshares=1
            return (
                numpy.array(self._rightsPerAction.rightsPerShare(
                    nshares, start, end)) *
                numpy.array(self._activeShares.hourly(member, start, end))
                )
 

import unittest
from activesharescurve import ActiveSharesCurve, UnconfiguredDataProvider
import datetime
import numpy

def isodate(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()

class CurveProvider_MockUp(object):
    def __init__(self, value):
        self._value = value
    def rightsPerShare(self, n, *args, **kwd):
        return self._value[n]
    def hourly(self, *args, **kwd):
        return self._value

class UseRightsCurve_Test(unittest.TestCase):
    def asserUseRightsEqual(self, member, start, end,
            activeShares, rightsPerAction, expected
            ):
        curve = UseRightsCurve(
            activeShares=CurveProvider_MockUp(activeShares),
            rightsPerAction=CurveProvider_MockUp(rightsPerAction),
            )
        result = curve.get(member,
            start=isodate(start),
            end=isodate(end),
            )
        self.assertEqual(list(result), expected)
            

    def test_(self):
        self.asserUseRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-21',
            activeShares = 25*[1],
            rightsPerAction = {1: 25*[3]},
            expected = 25*[3]
            )

    def test_severalShares(self):
        self.asserUseRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-21',
            activeShares = 25*[2],
            rightsPerAction = {1: 25*[3]},
            expected = 25*[6]
            )

    def test_mixedShares(self):
        self.asserUseRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-22',
            activeShares = 25*[2] + 25*[3],
            rightsPerAction = {1: 50*[3]},
            expected = 25*[6] + 25*[9],
            )

    def assertEagerRightsEqual(self, member, start, end,
            activeShares, rightsPerAction, expected
            ):
        curve = UseRightsCurve(
            activeShares=CurveProvider_MockUp(activeShares),
            rightsPerAction=CurveProvider_MockUp(rightsPerAction),
            )
        result = curve.get(member,
            start=isodate(start),
            end=isodate(end),
            )
        self.assertEqual(list(result), expected)



# vim: ts=4 sw=4 et
