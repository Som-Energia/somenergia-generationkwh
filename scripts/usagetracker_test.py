#!/usr/bin/env python

import datetime
from genkwh_investments_from_accounting import *

def isodatetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d")

import unittest

class UsageTracker_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        import erppeek
        import dbconfig
        self.c = erppeek.Client(**dbconfig.erppeek)

    def test_available_kwh(self):
        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                '4', '2016-08-01', '2015-09-01', '2.0A', 'P1'),
            0)


 
