# -*- coding:utf8 -*-

import unittest

from amortizations import pendingAmortization, previousAmortizationDate


class Amortization_Test(unittest.TestCase):

    def test_pendingAmortization_beforeAnyAmortization(self):
        a = pendingAmortization(
            purchase_date='2001-01-01',
            current_date='2001-01-01',
            investment_amount=10000,
            amortized_amount=0,
            )
        self.assertEqual(a, 0)

    def test_pendingAmortization_DayBeforeAnyAmortization(self):
        a = pendingAmortization(
            purchase_date='2001-01-01',
            current_date='2002-12-31',
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

    def test_pendingAmortization_secondAmortitzationPending(self):
        a = pendingAmortization(
            purchase_date='2001-01-01',
            current_date='2004-01-01',
            investment_amount=10000,
            amortized_amount=0,
            )
        self.assertEqual(a, 800)


    def test_pendingAmortization_lastAmortitzationPending(self):
        a = pendingAmortization(
            purchase_date='2001-01-01',
            current_date='2026-01-01',
            investment_amount=10000,
            amortized_amount=0,
            )
        self.assertEqual(a, 10000)

    def test_pendingAmortization_whenExpiredAndAllPending(self):
        a = pendingAmortization(
            purchase_date='2001-01-01',
            current_date='2028-01-01',
            investment_amount=10000,
            amortized_amount=0,
            )
        self.assertEqual(a, 10000)

    def test_pendingAmortization_atFirstAmortizationAlreadyPaid(self):
        a = pendingAmortization(
            purchase_date='2001-01-01',
            current_date='2003-01-01',
            investment_amount=10000,
            amortized_amount=400,
            )
        self.assertEqual(a, 0)

    def test_pendingAmortization_allAmortizationAlreadyPaid(self):
        a = pendingAmortization(
            purchase_date='2001-01-01',
            current_date='2026-01-01',
            investment_amount=10000,
            amortized_amount=10000,
            )
        self.assertEqual(a, 0)

    def test_pendingAmortization_differentAmount(self):
        a = pendingAmortization(
            purchase_date='2001-01-01',
            current_date='2003-01-01',
            investment_amount=100000,
            amortized_amount=0,
            )
        self.assertEqual(a, 4000)

    def test_pendingAmortization_advancedAmortizationPaid(self):
        a = pendingAmortization(
            purchase_date='2001-01-01',
            current_date='2003-12-31',
            investment_amount=10000,
            amortized_amount=800,
            )
        self.assertEqual(a, 0)



    def test_previousAmortizationDate_beforeFirstAmortization(self):
        d = previousAmortizationDate(
            purchase_date='2001-01-01',
            current_date='2002-12-31',
            )
        self.assertEqual(d, None)

    def test_previousAmortizationDate_atFirstAmortization(self):
        d = previousAmortizationDate(
            purchase_date='2001-01-01',
            current_date='2003-01-01',
            )
        self.assertEqual(d, '2003-01-01')

    def test_previousAmortizationDate_afterFirstAmortization(self):
        d = previousAmortizationDate(
            purchase_date='2001-01-01',
            current_date='2003-01-02',
            )
        self.assertEqual(d, '2003-01-01')

    def test_previousAmortizationDate_afterSecondAmortization(self):
        d = previousAmortizationDate(
            purchase_date='2001-01-01',
            current_date='2004-01-01',
            )
        self.assertEqual(d, '2004-01-01')

    def test_previousAmortizationDate_afterExpiration(self):
        d = previousAmortizationDate(
            purchase_date='2001-01-01',
            current_date='2027-01-01',
            )
        self.assertEqual(d, '2026-01-01')
# vim: et ts=4 sw=4
