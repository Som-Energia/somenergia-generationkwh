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

    def computeRights(self, production, activeShares, nshares=1, remainder=0):

        assert numpy.issubdtype(production.dtype, int), (
            "Production base type is not integer")
        assert numpy.issubdtype(activeShares.dtype,int), (
            "ActiveShares base type is not integer")

        with numpy.errstate(divide='ignore'):
            fraction = production*nshares/activeShares
        fraction = numpy.concatenate( ([remainder],fraction) )
        integral = fraction.cumsum()

        result = numpy.diff(integral//1000)
        remainder = integral[-1]%1000

        return result, remainder



# vim: ts=4 sw=4 et
