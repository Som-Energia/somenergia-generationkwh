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

        assert production.dtype == 'int64', (
            "Production base type is not integer")
        assert activeShares.dtype == 'int64', (
            "ActiveShares base type is not integer")

        with numpy.errstate(divide='ignore'):
            fraction = production*nshares/activeShares
        fraction = numpy.concatenate( ([remainder],fraction) )
        integral = fraction.cumsum()

        result = numpy.diff(integral//1000)
        remainder = integral[-1]%1000

        return result, remainder

import unittest
import datetime

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



# vim: ts=4 sw=4 et
