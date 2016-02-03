# -*- coding: utf-8 -*-

class CurveProvider(object):
	""" Provides hourly curves required to track
		generationkwh member usage.
	"""

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
class CurveProvider_Test(unittest.TestCase):

	def test_me(self):
		self.fail("It works!")




