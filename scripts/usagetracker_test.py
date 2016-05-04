#!/usr/bin/env python

import datetime
from genkwh_investments import (
    clear as investmentClear, 
    create as investmentCreate,
    )
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
        investmentClear()
        self.c.GenerationkwhAssignment.dropAll()
        self.c.GenerationkwhRemainderTesthelper.clean()

    def test_available_kwh_withNoActiveShares(self):
        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                4, '2016-08-01', '2016-09-01', '2.0A', 'P1'),
            0)

    def test_available_kwh_rightsAndInvestments(self):
        investmentCreate(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1'),
            3*2*24)

    def test_available_kwh_noRights(self):
        investmentCreate(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            20, '2015-08-01', [2]*2*binsPerDay)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            69, '2015-08-01', [0]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1'),
            0*2*24)


    def test_available_kwh_rightsForOne(self):
        investmentCreate(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            1, '2015-08-01', [2]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1'),
            50*2*24)

        # TODO: assert remainder has been added

    def test_use_kwh_exhaustingAvailable(self):
        investmentCreate(stop="2015-06-30", waitingDays=0)
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
        investmentCreate(stop="2015-06-30", waitingDays=0)
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
        investmentCreate(stop="2015-06-30", waitingDays=0)
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
        investmentCreate(stop="2015-06-30", waitingDays=0)
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




    def test_dealer(self):
        self.contract = 4
        self.member2 = 469
        investmentCreate(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [0,3,0,0,0])
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            5, '2015-08-01', [0,0,7,0,0])

        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=0))
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member2, priority=0))
    
        self.c.GenerationkwhTesthelper.trace_rigths_compilation(
            self.member2, '2015-08-01', '2015-09-01', '2.0A', 'P1')

        self.assertEqual(
            self.c.GenerationkwhTesthelper.dealer_use_kwh(
                self.contract, '2015-08-01', '2015-09-01', '2.0A', 'P1', 10), [
                dict(member_id=self.member, kwh=3),
                dict(member_id=self.member2, kwh=7),
            ])

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            [0,3,0]+22*[0]
            +25*[0]
            +25*[0]
            )

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member2, '2015-08-01', '2015-08-03'),
            [0,0,7]+22*[0]
            +25*[0]
            +25*[0]
            )

