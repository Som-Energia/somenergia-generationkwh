# -*- coding: utf-8 -*-

from .memberrightscurve import MemberRightsCurve
import unittest
from .isodates import isodate, localisodate
from plantmeter.mongotimecurve import dateToCurveIndex
import numpy

try: xrange
except NameError: xrange=range

class CurveProvider_MockUp(object):
    def __init__(self, value):
        self._value = value
    def rightsPerShare(self, n, start, end):
        nbins = dateToCurveIndex(
                localisodate(str(start)),
                localisodate(str(end))) + 25
        return numpy.array(self._value[n]) if n in self._value else (
            numpy.zeros(nbins, dtype=numpy.int))

    def hourly(self, *args, **kwd):
        return self._value

class Remainder_Mockup(object):
    def __init__(self, date, nshares):
        self._initedNShares = set(nshares)
        nshares = set(nshares)
        nshares.add(1)
        self._remainders = [
            (nsh, date, 0)
            for nsh in nshares
            ]

    def lastRemainders(self):
        return self._remainders

    def filled(self):
        return [nsh for nsh, date, rem in self._remainders]

    def init(self, nshares):
        self._initedNShares |= set(nshares)

    def initedRemainders(self):
        return self._initedNShares



class MemberRightsCurve_Test(unittest.TestCase):
    def assertRightsEqual(self, member, start, end,
            activeShares, rightsPerShare, expected, 
            eager=False, expectedInitedRemainders=None,
            ):
        remainders = Remainder_Mockup(end,rightsPerShare.keys())
        curve = MemberRightsCurve(
            activeShares=CurveProvider_MockUp(activeShares),
            rightsPerShare=CurveProvider_MockUp(rightsPerShare),
            eager = eager,
            remainders = remainders,
            )
        result = curve.rights_kwh(member,
            start=isodate(start),
            end=isodate(end),
            )
        self.assertEqual(list(result), expected)

        if expectedInitedRemainders is None: return
        self.assertEqual(remainders.initedRemainders(), set(expectedInitedRemainders))

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

    def test_eager_noRightsPerShare(self):
        self.assertRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-21',
            activeShares = 25*[2],
            rightsPerShare = {
                1: 25*[10]
                },
            expected = 25*[20],
            expectedInitedRemainders = [1,2],
            eager = True,
            )

    def test_eager_notEvenFor1Share(self):
        self.assertRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-21',
            activeShares = 25*[2],
            rightsPerShare = {
                },
            expected = 25*[0],
            expectedInitedRemainders = [2],
            eager = True,
            )

    def test_eager_withMoreThan31Shares(self):

        # This addresses a but regarding hardcoded limit of 32 in np.choose
        self.assertRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-22',
            activeShares = 50*[33],
            rightsPerShare = {
                33: 50*[20],
                },
            expected = 50*[20],
            eager = True
            )

    def test_eager_withMoreThan31DifferentShares(self):

        # This addresses a but regarding hardcoded limit of 32 in np.choose
        # Not addressed in this case, so we assert
        with self.assertRaises(AssertionError) as ctx:
            self.assertRightsEqual(
                member='member',
                start='2015-01-21',
                end='2015-01-22',
                activeShares = 16*[33]+list(xrange(34)),
                rightsPerShare = dict([
                    (i, 50*[20])
                    for i in xrange(32)
                    ]),
                expected = 50*[20],
                eager = True
                )
        self.assertEqual(ctx.exception.args[0],
            "The member has too many different numbers of shares within the interval")


# vim: ts=4 sw=4 et
