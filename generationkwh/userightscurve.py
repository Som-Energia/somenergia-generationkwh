# -*- coding: utf-8 -*-

import numpy

class UseRightsCurve(object):
    """
        Provides the hourly curve of kWh available for a given
        member in a given time interval.

        Naive and eager versions are provided:

        - Naive version just multiplies the kWh discretized curve
        for one action by the number of active shares.

        - Eager version takes a different profile for each number
        of shares and members with N shares get a kWh with N times
        earlier.

        kWh remainder are accommulated to the next hour so if the
        next hour implies a change of period, that energy is wrongly
        assigned, to be purist.

        That error is bigger for the naive approximation, as the
        error in every period change is up to N kWh if you have N shares.
        The eager version limits the error a 1 kWh.
    """
    def __init__(self, activeShares, rightsPerShare, eager=False):
        self._activeShares = activeShares
        self._rightsPerAction = rightsPerShare
        self._eager = eager

    def get(self, member, start, end):
        if not self._eager:
            nshares=1
            return (
                numpy.array(self._rightsPerAction.rightsPerShare(
                    nshares, start, end)) *
                numpy.array(self._activeShares.hourly(member, start, end))
                )

        shares = self._activeShares.hourly(member, start, end)
        choiceset = list(sorted(set(shares)))
        choices = [
            self._rightsPerAction.rightsPerShare(nshares, start, end)
            if nshares in choiceset
            else None
            for nshares in xrange(max(choiceset)+1)
            ]
        return numpy.choose(shares, choices)
 

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

class UseRightsCurve_Test(unittest.TestCase):
    def asserUseRightsEqual(self, member, start, end,
            activeShares, rightsPerShare, expected, eager=False
            ):
        curve = UseRightsCurve(
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
        self.asserUseRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-21',
            activeShares = 25*[1],
            rightsPerShare = {1: 25*[3]},
            expected = 25*[3]
            )

    def test_severalShares(self):
        self.asserUseRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-21',
            activeShares = 25*[2],
            rightsPerShare = {1: 25*[3]},
            expected = 25*[6]
            )

    def test_mixedShares(self):
        self.asserUseRightsEqual(
            member='member',
            start='2015-01-21',
            end='2015-01-22',
            activeShares = 25*[2] + 25*[3],
            rightsPerShare = {1: 50*[3]},
            expected = 25*[6] + 25*[9],
            )

    def test_eager_uniformShares(self):
        self.asserUseRightsEqual(
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
        self.asserUseRightsEqual(
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
