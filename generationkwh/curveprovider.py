# -*- coding: utf-8 -*-

class CurveProvider(object):
    """ Provides hourly curves required to track
        generationkwh member usage.
    """

    def __init__(self, shares=None):
        self._shareProvider = shares

    def activeShares(self, member, start, end):
        return +25*[0]

	def production(self, member, start, end):
		""" Returns acquainted productions rights for
			the member
			within start and end dates, included.
		"""

	def usage(self, member, start, end):
		""" Return used production rights for the member
			within start and end dates, included.
		"""

	def periodMask(self, fare, period, start, end):
		""" Returns an array for the set of hours
			the period is active por a given fare
			within start and end days, included.
		"""

import unittest

class SharesProvider_Mockup(object):
    def __init__(self, shareContracts):
        self._contracts = shareContracts

    def shareContracts(self):
        return self._contracts

class CurveProvider_Test(unittest.TestCase):

    def test_shares_singleDay_noShares(self):
        shares = SharesProvider_Mockup([
            ])
        curves = CurveProvider(shares = shares)
        shares = curves.activeShares('member', '2015-02-21', '2015-02-21')
        self.assertEqual(shares,
            +25*[0]
            )
        



# vim: ts=4 sw=4 et
