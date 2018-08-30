# -*- coding:utf8 -*-

import unittest

from .amortizations import pendingAmortizations

class Amortization_Test(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None


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
