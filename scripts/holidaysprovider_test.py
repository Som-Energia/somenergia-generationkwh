#!/usr/bin/env python

import datetime
from genkwh_investments_from_accounting import *

def isodatetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d")

import unittest

class Holidays_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"

    def assertEqualDates(self, result, expected):
        self.assertEqual([ isodatetime(date) for date in expected], result)

    def test_holidays(self):
        self.assertEqualDates(
            c.GenerationkwhTesthelper.holidays("2015-12-25", "2015-12-25"),
            [
                '2015-12-25',
            ])

    def test_holidays_severalDays(self):
        self.assertEqualDates(
            c.GenerationkwhTesthelper.holidays("2015-12-25", "2016-01-01"),
            [
                '2015-12-25',
                '2016-01-01',
            ])


import erppeek
import dbconfig
c = erppeek.Client(**dbconfig.erppeek)

 
