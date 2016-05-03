#!/usr/bin/env python

import datetime
from generationkwh.isodates import naiveisodate

import unittest

dbconfig = None
try:
    import dbconfig
    import erppeek
except ImportError:
    pass

@unittest.skipIf(not dbconfig, "depends on ERP")
class Holidays_Test(unittest.TestCase):

    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.c = erppeek.Client(**dbconfig.erppeek)
        self.HolidaysHelper = self.c.GenerationkwhHolidaysTesthelper

    def assertEqualDates(self, result, expected):
        self.assertEqual([ naiveisodate(date) for date in expected], result)

    def test_holidays(self):
        self.assertEqualDates(
            self.HolidaysHelper.holidays("2015-12-25", "2015-12-25"),
            [
                '2015-12-25',
            ])

    def test_holidays_severalDays(self):
        self.assertEqualDates(
            self.HolidaysHelper.holidays("2015-12-25", "2016-01-01"),
            [
                '2015-12-25',
                '2016-01-01',
            ])



 
