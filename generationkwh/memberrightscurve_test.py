# -*- coding: utf-8 -*-

from memberrightscurve import MemberRightsCurve
import unittest
import datetime

def isodate(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()

class CurveProvider_MockUp(object):
    def __init__(self, value):
        self._value = value
    def rightsPerShare(self, n, *args, **kwd):
        return self._value[n]
    def hourly(self, *args, **kwd):
        return self._value

class MemberRightsCurve_Test(unittest.TestCase):
    def assertRightsEqual(self, member, start, end,
            activeShares, rightsPerShare, expected, eager=False
            ):
        curve = MemberRightsCurve(
            activeShares=CurveProvider_MockUp(activeShares),
            rightsPerShare=CurveProvider_MockUp(rightsPerShare),
            eager = eager,
            )
        result = curve.get(member,
            start=isodate(start),
            end=isodate(end),
            )
        self.assertEqual(list(result), expected)

    def test_singleShare(self):
        self.assertRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-21',
            activeShares = 25*[1],
            rightsPerShare = {1: 25*[3]},
            expected = 25*[3]
            )

    def test_severalShares(self):
        self.assertRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-21',
            activeShares = 25*[2],
            rightsPerShare = {1: 25*[3]},
            expected = 25*[6]
            )

    def test_mixedShares(self):
        self.assertRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-22',
            activeShares = 25*[2] + 25*[3],
            rightsPerShare = {1: 50*[3]},
            expected = 25*[6] + 25*[9],
            )

    def test_eager_uniformShares(self):
        self.assertRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-22',
            activeShares = 25*[2],
            rightsPerShare = {
                2: 25*[20],
                },
            expected = 25*[20],
            eager = True
            )

    def test_eager_mixedShares(self):
        self.assertRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-22',
            activeShares = 25*[2] + 25*[3],
            rightsPerShare = {
                2: 50*[20],
                3: 50*[70],
                },
            expected = 25*[20] + 25*[70],
            eager = True
            )


# vim: ts=4 sw=4 et
