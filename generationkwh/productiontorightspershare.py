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
        diff = wanted - original
        error = sum(d for d in diff if d<0)
        result = [
            o+d if d>0 else o
            for d,o in zip(diff, original)
        ]
        return result, error



# vim: ts=4 sw=4 et
