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
            remainder_wh = 500,
            production = 25*[500],
            activeShares = 25*[8],
            nShares=1,
            expected = 12*[63,62]+[63],
            expectedRemainder = 0,
            )

    def test_computeRights_negativeRemainder(self):
        nshares = 1
        totalShares = 100
        self.assertComputeEquals(
            remainder_wh = -1200*1000*nshares/totalShares,
            production = 25*[500],
            activeShares = 25*[totalShares],
            nShares=nshares,
            expected = [0,0,3]+22*[5],
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

    def assertRectified(self, original, wanted, rectified, error):
        curve = ProductionToRightsPerShare()
        original = numpy.array(original)
        wanted   = numpy.array(wanted)

        result, resultError = curve.rectifyRights(original, wanted)

        self.assertEqual(list(result), rectified)
        self.assertEqual(resultError, error)


    def test_rectifyRights_wantedAlwaysHigher(self):
        self.assertRectified(
            original  = [0,0,0,0],
            wanted    = [1,2,3,4],
            rectified = [1,2,3,4],
            error     = 0,
        )

    def test_rectifyRights_wantedAlwaysZero(self):
        self.assertRectified(
            original  = [1,2,3,4],
            wanted    = [0,0,0,0],
            rectified = [1,2,3,4],
            error     = sum([1,2,3,4]),
        )

    def test_rectifyRights_wantedAlwaysLower_wantedSubstractedFromError(self):
        self.assertRectified(
            original  = [1,2,3,4],
            wanted    = [0,0,2,0],
            rectified = [1,2,3,4],
            error     = sum([1,2,3-2,4]),
        )

    def test_rectifyRights_compensatedErrorBigger(self):
        self.assertRectified(
            original  = [1,2,3,4],
            wanted    = [0,0,0,8],
            rectified = [1,2,3,4],
            error     = 2,
        )

    def test_rectifyRights_compensatedBinBigger(self):
        self.assertRectified(
            original  = [1,2,3,4],
            wanted    = [0,0,0,12],
            rectified = [1,2,3,6],
            error     = 0,
        )









# vim: ts=4 sw=4 et
