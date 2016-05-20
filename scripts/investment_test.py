#!/usr/bin/env python

from genkwh_investments import *

import unittest

dbconfig = None
try:
    import dbconfig
    import erppeek
except ImportError:
    pass

@unittest.skipIf(not dbconfig, "depends on ERP")
class InvestmentCommand_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"

    def test_clean(self):
        clear()
        data = listactive(csv=True)
        self.assertEqual(data,'')

    def test_create_toEarly(self):
        clear()
        create(stop="2015-06-29")
        data = listactive(csv=True)
        self.assertEqual(data,'')

    def test_create_onlyFirstBatch(self):
        clear()
        create(stop="2015-06-30")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_firstBatch_twice(self):
        clear()
        create(stop="2015-06-30")
        create(stop="2015-06-30")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_firstAndSecondBatch(self):
        clear()
        create(stop="2015-07-03")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_justSecondBatch(self):
        clear()
        create(start='2015-07-02', stop="2015-07-03")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_waitTwoDays(self):
        clear()
        create(stop="2015-06-30", waitingDays=2)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_expireOneYear(self):
        clear()
        create(stop="2015-06-30", waitingDays=2, expirationYears=1)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_inTwoBatches(self):
        clear()
        create(stop="2015-06-30", waitingDays=0, expirationYears=1)
        create(stop="2015-07-03")
        data = listactive(csv=True)

    def test_listactive_withMember(self):
        clear()
        create(stop="2015-06-30")
        data = listactive(csv=True, member=469)
        self.assertMultiLineEqual(data,
            '469\tFalse\tFalse\t3\n'
            '469\tFalse\tFalse\t2\n'
        )

    def test_listactive_withStop_shouldBeFirstBatch(self):
        clear()
        create(stop="2015-07-03", waitingDays=0, expirationYears=1)
        data = listactive(csv=True, stop="2015-06-30")
        self.assertB2BEqual(data)

    def test_listactive_withStopAndNoActivatedInvestments_shouldBeFirstBatch(self):
        # Second batch is not activated, and is not shown even if we extend stop
        clear()
        create(stop="2015-06-30", waitingDays=0, expirationYears=1)
        create(start="2015-07-03", stop="2015-07-03")
        data = listactive(csv=True, stop="2020-07-03")
        self.assertB2BEqual(data)

    def test_listactive_withStart_excludeExpired_shouldBeSecondBatch(self):
        # Expired contracts do not show if start is specified and it is earlier
        clear()
        create(stop="2015-07-03", waitingDays=0, expirationYears=1)
        data = listactive(csv=True, start="2016-07-01")
        self.assertB2BEqual(data)

    def test_listactive_withStartAndNoActivatedInvestments_shouldBeFirstBatch(self):
        # Unactivated contracts are not listed if start is specified
        clear()
        create(stop="2015-06-30", waitingDays=0, expirationYears=1) # listed
        create(start="2015-07-03", stop="2015-07-03") # unlisted
        data = listactive(csv=True, start="2016-06-30")
        self.assertB2BEqual(data)

    def test_listactive_withStartAndNoExpirationRunForEver_shouldBeSecondBatch(self):
        # Active with no deactivation keeps being active for ever
        clear()
        create(stop="2015-06-30", waitingDays=0, expirationYears=1) # unlisted
        create(start="2015-07-03", stop="2015-07-03", waitingDays=0) # listed
        data = listactive(csv=True, start="2036-06-30")
        self.assertB2BEqual(data)


    def test_activate_withStop(self):
        clear()
        create(stop="2015-07-03")
        activate(stop="2015-06-30", waitingDays=0)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_activate_withStart(self):
        clear()
        create(stop="2015-07-03")
        activate(start="2015-07-02", waitingDays=0)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_activate_withExpiration(self):
        clear()
        create(stop="2015-07-03")
        activate(stop="2015-06-30", waitingDays=0, expirationYears=1)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

class Investment_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.Investments = c.GenerationkwhInvestment
        clear()

    def tearDown(self):
        clear()

    def test__effective_investments_tuple__noInvestments(self):
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, None),
            [])

    def test__create_from_accounting__all(self):
        # Should fail whenever Gijsbert makes further investments
        self.Investments.create_from_accounting(1, None, None, 0, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__create_from_accounting__restrictingFirst(self):
        self.Investments.create_from_accounting(1, '2015-07-01', '2015-11-20', 0, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__create_from_accounting__restrictingLast(self):
        self.Investments.create_from_accounting(1, None, '2015-11-19', 0, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
            ])

    def test__create_from_accounting__noWaitingDays(self):
        self.Investments.create_from_accounting(1, None, '2015-11-20', None, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, None),
            [
                [1, False, False, 15],
                [1, False, False, 10],
                [1, False, False,  1],
                [1, False, False, 30],
                [1, False, False, 30],
            ])

    def test__create_from_accounting__nonZeroWaitingDays(self):
        self.Investments.create_from_accounting(1, None, '2015-11-20', 1, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', False, 15],
                [1, '2015-07-01', False, 10],
                [1, '2015-07-30', False,  1],
                [1, '2015-11-21', False, 30],
                [1, '2015-11-21', False, 30],
            ])

    def test__create_from_accounting__nonZeroExpireYears(self):
        self.Investments.create_from_accounting(1, None, '2015-11-20', 1, 2)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', '2017-07-01', 15],
                [1, '2015-07-01', '2017-07-01', 10],
                [1, '2015-07-30', '2017-07-30',  1],
                [1, '2015-11-21', '2017-11-21', 30],
                [1, '2015-11-21', '2017-11-21', 30],
            ])

    def test__create_from_accounting__severalMembers(self):
        self.Investments.create_from_accounting(1, None, '2015-11-20', 0, None)
        self.Investments.create_from_accounting(38, None, '2015-11-20', 0, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
                [38, '2015-06-30', False, 3],
                [38, '2015-10-13', False, 1],
                [38, '2015-10-20', False, -1],
            ])

    def test__create_from_accounting__severalMembersArray_reorderbyPurchase(self):
        self.Investments.create_from_accounting([1,38], None, '2015-11-20', 0, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, None),
            [
                [38, '2015-06-30', False, 3],
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [38, '2015-10-13', False, 1],
                [38, '2015-10-20', False, -1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__create_from_accounting__noMemberTakesAll(self):
        self.Investments.create_from_accounting(None, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(1, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
            ])
        self.assertEqual(
            self.Investments.effective_investments_tuple(38, None, None),
            [
                [38, '2015-06-30', False, 3],
            ])

    def test__create_from_accounting__ignoresExisting(self):
        self.Investments.create_from_accounting(1, None, '2015-06-30', None, None)
        self.Investments.create_from_accounting(1, None, '2015-07-29', 0, None)
        self.Investments.create_from_accounting(1, None, '2015-11-20', 0, 2)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, None),
            [
                [1, False, False, 15],
                [1, False, False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', '2017-11-20', 30],
                [1, '2015-11-20', '2017-11-20', 30],
            ])

    def test__effective_investments_tuple__filtersByMember(self):
        self.Investments.create_from_accounting(1, None, '2015-11-20', 0, None)
        self.Investments.create_from_accounting(38, None, '2015-11-20', 0, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(1, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__effective_investments_tuple__filtersByFirst_removesUnstarted(self):
        self.Investments.create_from_accounting(1, None, '2015-06-30', None, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, '2017-07-20', None),
            [
                #[1, False, False, 15], # Unstarted
                #[1, False, False, 10], # Unstarted
            ])

    def test__effective_investments_tuple__filtersByFirst_keepsUnexpiredWhicheverTheDate(self):
        self.Investments.create_from_accounting(1, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, '4017-07-20', None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
            ])

    def test__effective_investments_tuple__filtersByFirst_passesNotYetExpired(self):
        self.Investments.create_from_accounting(1, None, '2015-06-30', 0, 2)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, '2017-06-30', None),
            [
                [1, '2015-06-30', '2017-06-30', 15],
                [1, '2015-06-30', '2017-06-30', 10],

            ])

    def test__effective_investments_tuple__filtersByFirst_removesExpired(self):
        self.Investments.create_from_accounting(1, None, '2015-06-30', 0, 2)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, '2017-07-01', None),
            [
                #[1, '2015-06-30', '2017-06-30', 15],
                #[1, '2015-06-30', '2017-06-30', 10],

            ])

    def test__effective_investments_tuple__filtersByLast_removesUnstarted(self):
        self.Investments.create_from_accounting(1, None, '2015-06-30', None, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, '2015-11-19'),
            [
                #[1, False, False, 15], # Unstarted
                #[1, False, False, 10], # Unstarted
            ])

    def test__effective_investments_tuple__filtersByLast_includesStarted(self):
        self.Investments.create_from_accounting(1, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, '2015-06-30'),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
            ])

    def test__effective_investments_tuple__filtersByLast_excludesStartedLater(self):
        self.Investments.create_from_accounting(1, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, '2015-06-29'),
            [
                #[1, '2015-06-30', False, 15], # Not yet started
                #[1, '2015-06-30', False, 10], # Not yet started
            ])

    def test__effective_investments_tuple__deactivatedNotShown(self):
        self.Investments.create_from_accounting(1, None, '2015-11-19', 0, None)
        toBeDeactivated=self.Investments.search([
            ('member_id','=',1),
            ('nshares','=',10),
            ])[0]
        self.Investments.write(toBeDeactivated, dict(active=False))
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                #[1, '2015-06-30', False, 10], # deactivated
                [1, '2015-07-29', False,  1],
            ])

    def test__create_from_accounting__unactiveNotRecreated(self):
        self.Investments.create_from_accounting(1, None, '2015-11-19', 0, None)
        toBeDeactivated=self.Investments.search([
            ('member_id','=',1),
            ('nshares','=',10),
            ])[0]
        self.Investments.write(toBeDeactivated, dict(active=False))
        self.Investments.create_from_accounting(1, None, '2015-11-19', 0, None)
        self.assertEqual(
            self.Investments.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                #[1, '2015-06-30', False, 10], # still deactivated
                [1, '2015-07-29', False,  1],
            ])
        


    # TODO test__setEffective
    # TODO test__setExpiration

    def test__effective_for_member__noInvestments(self):
        self.assertFalse(
            self.Investments.effective_for_member(None, None, None))


    def test__effectiveForMember__insideDates(self):
        self.Investments.create_from_accounting(1,'2010-01-01', '2015-07-03',
            1, None)
        self.assertTrue(
            self.Investments.effective_for_member(1,'2015-07-01','2015-07-01'))





