# -*- coding:utf8 -*-

import unittest

from amortizations import (
    pendingAmortization,
    pendingAmortizations,
    previousAmortizationDate,
    currentAmortizationNumber,
    totalAmortizationNumber,
    )

class Amortization_Test(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

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

    def test_currentAmortizationNumber_beforeFirstAmortization(self):
        d = currentAmortizationNumber(
            purchase_date='2001-01-01',
            current_date='2002-12-31',
        )
        self.assertEqual(d, None)

    def test_currentAmortizationNumber_afterFirstAmortization(self):
        d = currentAmortizationNumber(
            purchase_date='2001-01-01',
            current_date='2003-01-01',
        )
        self.assertEqual(d, 1)

    def test_currentAmortizationNumber_afterSecondAmortization(self):
        d = currentAmortizationNumber(
            purchase_date='2001-01-01',
            current_date='2004-01-01',
        )
        self.assertEqual(d, 2)

    def test_currentAmortizationNumber_aYearAfterEndAmortization(self):
        d = currentAmortizationNumber(
            purchase_date='2001-01-01',
            current_date='2027-01-01',
        )
        self.assertEqual(d, 24)

    def test_totalAmortizationNumber_its_a_constant(self):
        self.assertEqual(totalAmortizationNumber(),24)

    def test_pendingAmortizations_unpaid(self):
        self.assertEqual(
            pendingAmortizations(
                purchase_date=False,
                current_date='2002-01-01',
                investment_amount=1000,
                amortized_amount=0,
                ), [
            ])

    def test_pendingAmortizations_justFirstAmortization(self):
        self.assertEqual(
            pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2002-01-01',
                investment_amount=1000,
                amortized_amount=0,
                ), [
                (1, 24, '2002-01-01', 40),
            ])

    def test_pendingAmortizations_justBeforeFirstOne(self):
        self.assertEqual(
            pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2001-12-31',
                investment_amount=1000,
                amortized_amount=0,
                ), [])

    def test_pendingAmortizations_justSecondOne(self):
        self.assertEqual(
            pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2003-01-01',
                investment_amount=1000,
                amortized_amount=0,
                ), [
                (1, 24, '2002-01-01', 40),
                (2, 24, '2003-01-01', 40),
            ])

    def test_pendingAmortizations_alreadyAmortized(self):
        self.assertEqual(
            pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2003-01-01',
                investment_amount=1000,
                amortized_amount=40,
                ), [
                (2, 24, '2003-01-01', 40),
            ])

    def test_pendingAmortizations_lastDouble(self):
        self.assertEqual(
            pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2025-01-01',
                investment_amount=1000,
                amortized_amount=920,
                ), [
                (24, 24, '2025-01-01', 80),
            ])

    def test_pendingAmortizations_allDone(self):
        self.assertEqual(
            pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2050-01-01',
                investment_amount=1000,
                amortized_amount=1000,
                ), [
            ])

    def test_pendingAmortizations_allPending(self):
        self.assertEqual(
            pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2040-01-01',
                investment_amount=1000,
                amortized_amount=0,
                ), [
                ( 1, 24, '2002-01-01', 40),
                ( 2, 24, '2003-01-01', 40),
                ( 3, 24, '2004-01-01', 40),
                ( 4, 24, '2005-01-01', 40),
                ( 5, 24, '2006-01-01', 40),
                ( 6, 24, '2007-01-01', 40),
                ( 7, 24, '2008-01-01', 40),
                ( 8, 24, '2009-01-01', 40),
                ( 9, 24, '2010-01-01', 40),
                (10, 24, '2011-01-01', 40),
                (11, 24, '2012-01-01', 40),
                (12, 24, '2013-01-01', 40),
                (13, 24, '2014-01-01', 40),
                (14, 24, '2015-01-01', 40),
                (15, 24, '2016-01-01', 40),
                (16, 24, '2017-01-01', 40),
                (17, 24, '2018-01-01', 40),
                (18, 24, '2019-01-01', 40),
                (19, 24, '2020-01-01', 40),
                (20, 24, '2021-01-01', 40),
                (21, 24, '2022-01-01', 40),
                (22, 24, '2023-01-01', 40),
                (23, 24, '2024-01-01', 40),
                (24, 24, '2025-01-01', 80),
            ])



# vim: et ts=4 sw=4
