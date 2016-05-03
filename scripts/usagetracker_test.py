#!/usr/bin/env python

import datetime
from genkwh_investments import clear, create

import unittest

binsPerDay = 25

class UsageTracker_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        import erppeek
        import dbconfig
        self.c = erppeek.Client(**dbconfig.erppeek)
        self.clearData()
        self.member = 1 # has 25 shares at the first investment wave
        
    def tearDown(self):
        self.clearData()

    def clearData(self):
        self.c.GenerationkwhTesthelper.clear_mongo_collections([
            'rightspershare',
            'memberrightusage',
            ])
        clear()
        self.c.GenerationkwhRemainderTesthelper.clean()

    def test_available_kwh_withNoActiveShares(self):
        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                4, '2016-08-01', '2016-09-01', '2.0A', 'P1'),
            0)

    def test_available_kwh_rightsAndInvestments(self):
        create(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

#        self.c.GenerationkwhTesthelper.trace_rigths_compilation(
#            self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1')
    
        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1'),
            3*2*24)

    def test_available_kwh_noRights(self):
        create(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            20, '2015-08-01', [2]*2*binsPerDay)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            69, '2015-08-01', [0]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1'),
            0*2*24)


    def test_available_kwh_rightsForOne(self):
        create(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            1, '2015-08-01', [2]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1'),
            50*2*24)

    def test_use_kwh_exhaustingAvailable(self):
        create(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_use_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1', 3*2*24+100),
            3*2*24)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            +24*[3]+1*[0]
            +24*[3]+1*[0]
            +25*[0]
            )


    def test_use_kwh_notExhaustingAvailable(self):
        create(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_use_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1', 10),
            10)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            +3*[3]+[1]+21*[0]
            +25*[0]
            +25*[0]
            )

    def test_use_kwh_consumingOnConsumedDays(self):
        create(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_use_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1', 10),
            10)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_use_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1', 3*2*24+100),
            3*2*24-10)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            +24*[3]+[0]
            +24*[3]+[0]
            +25*[0]
            )

    def test_refund_kwh(self):
        create(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_use_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1', 10),
            10)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_refund_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1', 2),
            2)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            [3,3,2]+22*[0]
            +25*[0]
            +25*[0]
            )


 
