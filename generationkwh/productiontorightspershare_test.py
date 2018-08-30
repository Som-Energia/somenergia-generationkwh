# -*- coding: utf-8 -*-

# TODO:
# - total active shares in a day = 0
# - non-adjacent cache and production

from .productiontorightspershare import ProductionToRightsPerShare

import numpy
import unittest
import datetime
from .isodates import isodate

class ProductionToRightsPerShare_Test(unittest.TestCase):

    def assertComputeEquals(self,
        production,
        activeShares,
        nShares,
        expected,
        expectedRemainder=0,
        remainder_wh = 0,
        ):

        curve = ProductionToRightsPerShare()
        result, resultingRemainder = curve.computeRights(
            production=numpy.array(production),
            activeShares = numpy.array(activeShares),
            nshares=nShares,
            remainder_wh = remainder_wh,
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
            expected = 25*[2000],
            )

    def test_computeRights_sharedProduction(self):
        self.assertComputeEquals(
            production = 25*[2000],
            activeShares = 25*[2],
            nShares=1,
            expected = 25*[1000],
            )

    def test_computeRights_withManyShares(self):
        self.assertComputeEquals(
            production = 25*[2000],
            activeShares = 25*[2],
            nShares=2,
            expected = 25*[2000],
            )

    def test_computeRights_withInnerRemainder(self):
        self.assertComputeEquals(
            production = 24*[1000]+[0],
            activeShares = 25*[2000],
            nShares=1,
            expected = 12*[0,1]+[0],
            )

    def test_computeRights_withNoShare(self):
        self.assertComputeEquals(
            production = 25*[1000],
            activeShares = 10*[0] + 15*[1],
            nShares=1,
            expected = 10*[0]+15*[1000],
            )

    def test_computeRights_creatingRemainder(self):
        self.assertComputeEquals(
            production = 25*[500],
            activeShares = 25*[8],
            nShares=1,
            expected = 12*[62,63]+[62],
            expectedRemainder = 500,
            )

    def test_computeRights_takingRemainder(self):
        self.assertComputeEquals(
            remainder_wh = 500.0,
            production = 25*[500],
            activeShares = 25*[8],
            nShares=1,
            expected = 12*[63,62]+[63],
            expectedRemainder = 0,
            )

    def test_get_floatProductionFailsAssertion(self):
        curve = ProductionToRightsPerShare()
        with self.assertRaises(AssertionError) as failure:
            curve.computeRights(
                production = numpy.array([3.2]),
                activeShares  = numpy.array([3]),
                nshares=1,
                remainder_wh = 0,
                )
        self.assertEqual(failure.exception.args[0],
            "Production base type is not integer")

    def test_get_floatSharesFailsAssertion(self):
        curve = ProductionToRightsPerShare()
        with self.assertRaises(AssertionError) as failure:
            curve.computeRights(
                production = numpy.array([3]),
                activeShares  = numpy.array([3.2]),
                nshares = 1,
                remainder_wh = 0,
                )
        self.assertEqual(failure.exception.args[0],
            "ActiveShares base type is not integer")



# vim: ts=4 sw=4 et