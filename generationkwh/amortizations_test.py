# -*- coding:utf8 -*-

import unittest

from amortizations import pendingAmortization


class Amortization_Test(unittest.TestCase):

    def test_pendingAmortization_beforeAnyAmortization(self):
        a = pendingAmortization(
            purchase_date='2001-01-01',
            current_date='2001-01-01',
            investment_amount=10000,
            amortized_amount=0,
            )
        self.assertEqual(a, 0)

    def test_pendingAmortization_atFirstAmortization(self):
        a = pendingAmortization(
            purchase_date='2001-01-01',
            current_date='2003-01-01',
            investment_amount=10000,
            amortized_amount=0,
            )
        self.assertEqual(a, 400)



# vim: et ts=4 sw=4
