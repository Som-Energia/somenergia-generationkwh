# -*- coding: utf-8 -*-

class UseRightsCurve(object):
    """
    """
    def __init__(self, activeShares, rightsPerAction):
        self._activeShares = activeShares
        self._rightsPerAction = rightsPerAction

    def get(self, member, start, end):
        return (
            numpy.array(self._rightsPerAction.get(start, end))*
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
    def get(self, *args, **kwd):
        return self._value
    def hourly(self, *args, **kwd):
        return self._value

class UseRightsCurve_Test(unittest.TestCase):

    def test_(self):
        curve = UseRightsCurve(
            activeShares=CurveProvider_MockUp(25*[1]),
            rightsPerAction=CurveProvider_MockUp(25*[3]),
            )
        result = curve.get(
            'member',
            start=isodate('2015-01-21'),
            end=isodate('2015-01-21'),
            )

        self.assertEqual(list(result),
            25*[3]
            )

    def test_severalShares(self):
        curve = UseRightsCurve(
            activeShares=CurveProvider_MockUp(25*[2]),
            rightsPerAction=CurveProvider_MockUp(25*[3]),
            )
        result = curve.get(
            'member',
            start=isodate('2015-01-21'),
            end=isodate('2015-01-21'),
            )

        self.assertEqual(list(result),
            25*[6]
            )




# vim: ts=4 sw=4 et
