# -*- coding: utf-8 -*-

# TODO:
# - total active shares in a day = 0
# - non-adjacent cache and production

import numpy

class ProductionToRightsPerShare(object):
    """
        Provides the hourly curve of kWh available for a member
        with a given number of shares.
    """

    def computeRights(self, production, activeShares, nshares=1, remainder_wh=0):

        assert numpy.issubdtype(production.dtype, numpy.dtype(int)), (
            "Production base type is not integer")
        assert numpy.issubdtype(activeShares.dtype, numpy.dtype(int)), (
            "ActiveShares base type is not integer")

        with numpy.errstate(divide='ignore'):
            fraction = production*1000*nshares / activeShares
            fraction[~numpy.isfinite(fraction) ] = 0
        fraction = numpy.concatenate( ([remainder_wh],fraction) )
        integral = fraction.cumsum()

        result = numpy.diff(integral//1000)
        remainder_wh = integral[-1]%1000

        return result, remainder_wh

    def rectifyRights(self, original, wanted):
        class Compensator:
            def __init__(self):
                self.error=0
            def computeBin(self, d, o):
                if d<0:
                    self.error += d
                    return o
                return o+d

        compensator = Compensator()
        diff = wanted - original
        result = [
            compensator.computeBin(d,o)
            for d,o in zip(diff, original)
        ]
        return result, compensator.error



# vim: ts=4 sw=4 et
