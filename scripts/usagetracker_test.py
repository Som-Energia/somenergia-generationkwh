#!/usr/bin/env python

import datetime
from genkwh_investments_from_accounting import *
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

    def test_available_kwh_whenNoRights(self):
        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                '4', '2016-08-01', '2016-09-01', '2.0A', 'P1'),
            0)

    def test_available_kwh_rightsAndInvestments(self):
        clear()
        create(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*50)

#        self.c.GenerationkwhTesthelper.trace_rigths_compilation(
#            2, '2015-08-01', '2015-09-01', '2.0A', 'P1')
    
        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                2, '2015-08-01', '2015-09-01', '2.0A', 'P1'),
            2*3*24)


 
