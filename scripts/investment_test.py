#!/usr/bin/env python
# -*- coding: utf-8 -*-

from genkwh_investments import *

import unittest

dbconfig = None
try:
    import dbconfig
    import erppeek
except ImportError:
    pass


@unittest.skipIf(not dbconfig, "depends on ERP")
class Investment_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.Investment = erp().GenerationkwhInvestment
        self.Investment.dropAll()

    def tearDown(self):
        self.Investment.dropAll()

    def test__effective_investments_tuple__noInvestments(self):
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [])

    def test__create_from_accounting__all(self):
        # Should fail whenever Gijsbert makes further investments
        # Update: We add the fiscal year closing investments

        self.Investment.create_from_accounting(1, None, None, 0, None)

        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
                #[1, '2016-05-19', False, -86], #Fiscal year closing
                #[1, '2016-05-19', False, 86]  #Fiscal year closing
            ])

    def test__create_from_accounting__restrictingFirst(self):
        self.Investment.create_from_accounting(1, '2015-07-01', '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__create_from_accounting__restrictingLast(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
            ])

    def test__create_from_accounting__noWaitingDays(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', None, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, False, False, 15],
                [1, False, False, 10],
                [1, False, False,  1],
                [1, False, False, 30],
                [1, False, False, 30],
            ])

    def test__create_from_accounting__nonZeroWaitingDays(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', 1, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', False, 15],
                [1, '2015-07-01', False, 10],
                [1, '2015-07-30', False,  1],
                [1, '2015-11-21', False, 30],
                [1, '2015-11-21', False, 30],
            ])

    def test__create_from_accounting__nonZeroExpireYears(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', 1, 2)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', '2017-07-01', 15],
                [1, '2015-07-01', '2017-07-01', 10],
                [1, '2015-07-30', '2017-07-30',  1],
                [1, '2015-11-21', '2017-11-21', 30],
                [1, '2015-11-21', '2017-11-21', 30],
            ])

    def test__create_from_accounting__severalMembers(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', 0, None)
        self.Investment.create_from_accounting(38, None, '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
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
        self.Investment.create_from_accounting([1,38], None, '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
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
        self.Investment.create_from_accounting(None, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(1, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
            ])
        self.assertEqual(
            self.Investment.effective_investments_tuple(38, None, None),
            [
                [38, '2015-06-30', False, 3],
            ])

    def test__create_from_accounting__ignoresExisting(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', None, None)
        self.Investment.create_from_accounting(1, None, '2015-07-29', 0, None)
        self.Investment.create_from_accounting(1, None, '2015-11-20', 0, 2)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, False, False, 15],
                [1, False, False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', '2017-11-20', 30],
                [1, '2015-11-20', '2017-11-20', 30],
            ])

    def test__effective_investments_tuple__filtersByMember(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', 0, None)
        self.Investment.create_from_accounting(38, None, '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(1, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__effective_investments_tuple__filtersByFirst_removesUnstarted(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', None, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, '2017-07-20', None),
            [
                #[1, False, False, 15], # Unstarted
                #[1, False, False, 10], # Unstarted
            ])

    def test__effective_investments_tuple__filtersByFirst_keepsUnexpiredWhicheverTheDate(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, '4017-07-20', None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
            ])

    def test__effective_investments_tuple__filtersByFirst_passesNotYetExpired(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, 2)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, '2017-06-30', None),
            [
                [1, '2015-06-30', '2017-06-30', 15],
                [1, '2015-06-30', '2017-06-30', 10],

            ])

    def test__effective_investments_tuple__filtersByFirst_removesExpired(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, 2)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, '2017-07-01', None),
            [
                #[1, '2015-06-30', '2017-06-30', 15],
                #[1, '2015-06-30', '2017-06-30', 10],

            ])

    def test__effective_investments_tuple__filtersByLast_removesUnstarted(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', None, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, '2015-11-19'),
            [
                #[1, False, False, 15], # Unstarted
                #[1, False, False, 10], # Unstarted
            ])

    def test__effective_investments_tuple__filtersByLast_includesStarted(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, '2015-06-30'),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
            ])

    def test__effective_investments_tuple__filtersByLast_excludesStartedLater(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, '2015-06-29'),
            [
                #[1, '2015-06-30', False, 15], # Not yet started
                #[1, '2015-06-30', False, 10], # Not yet started
            ])

    def test__effective_investments_tuple__deactivatedNotShown(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', 0, None)
        toBeDeactivated=self.Investment.search([
            ('member_id','=',1),
            ('nshares','=',10),
            ])[0]
        self.Investment.deactivate(toBeDeactivated)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                #[1, '2015-06-30', False, 10], # deactivated
                [1, '2015-07-29', False,  1],
            ])

    def test__create_from_accounting__unactiveNotRecreated(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', 0, None)
        toBeDeactivated=self.Investment.search([
            ('member_id','=',1),
            ('nshares','=',10),
            ])[0]
        self.Investment.deactivate(toBeDeactivated)
        self.Investment.create_from_accounting(1, None, '2015-11-19', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                #[1, '2015-06-30', False, 10], # still deactivated
                [1, '2015-07-29', False,  1],
            ])

    def test__set_effective__wait(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, None, 1, None, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', False, 15],
                [1, '2015-07-01', False, 10],
                [1, '2015-07-30', False,  1],
            ])

    def test__set_effective__waitAndExpire(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, None, 1, 2, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', '2017-07-01', 15],
                [1, '2015-07-01', '2017-07-01', 10],
                [1, '2015-07-30', '2017-07-30',  1],
            ])

    def test__set_effective__purchasedEarlierIgnored(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective('2015-07-01', None, 1, 2, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, False, False, 15],
                [1, False, False, 10],
                [1, '2015-07-30', '2017-07-30',  1],
            ])

    def test__set_effective__purchasedLaterIgnored(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, '2015-06-30', 1, 2, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', '2017-07-01', 15],
                [1, '2015-07-01', '2017-07-01', 10],
                [1, False, False,  1],
            ])

    def test__set_effective__alreadySetIgnored(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, '2015-06-30', 1, 2, False)
        self.Investment.set_effective(None, None, 10, 4, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', '2017-07-01', 15],
                [1, '2015-07-01', '2017-07-01', 10],
                [1, '2015-08-08', '2019-08-08',  1],
            ])

    def test__set_effective__alreadySetForced(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, '2015-06-30', 1, 2, False)
        self.Investment.set_effective(None, None, 10, 4, True)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-10', '2019-07-10', 15],
                [1, '2015-07-10', '2019-07-10', 10],
                [1, '2015-08-08', '2019-08-08',  1],
            ])

    # TODO: extent to move expire


    def test__member_has_effective__noInvestments(self):
        self.assertFalse(
            self.Investment.member_has_effective(None, None, None))

    def test__member_has_effective__insideDates(self):
        self.Investment.create_from_accounting(1,'2010-01-01', '2015-07-03',
            1, None)
        self.assertTrue(
            self.Investment.member_has_effective(1,'2015-07-01','2015-07-01'))
    
    # Amortizations

    def pendingAmortizations(self, currentDate):
        result = self.Investment.pending_amortizations(currentDate)
        return [x[1:-1] for x in result] # filter id and log

    
    def test__pending_amortitzations__noInvestments(self):
        self.assertEqual(self.pendingAmortizations('2017-11-20'), [])
        
    def test__pending_amortitzations__withDueInvestments(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.assertEqual(
            self.pendingAmortizations('2017-11-20'),[
            [1, '2017-07-29', 0, 4 ],
            [1, '2017-06-30', 0, 60],
            [1, '2017-06-30', 0, 40],
            ])

    def test__pending_amortitzations__notDue(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.assertEqual(
            self.pendingAmortizations('2017-07-28'),[
            [1, '2017-06-30', 0, 60],
            [1, '2017-06-30', 0, 40],
            ])

    def test__pending_amortitzations__whenPartiallyAmortized(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.amortize('2017-11-20')
        self.assertEqual(
            self.pendingAmortizations('2018-11-20'),[
            [1, '2018-07-29', 4,  4 ],
            [1, '2018-06-30', 60, 60],
            [1, '2018-06-30', 40, 40],
            ])


    def test__amortized_amount__zeroByDefault(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        investment_ids = self.Investment.search([])
        investments = self.Investment.read(investment_ids,['amortized_amount'])
        amortized_amounts = [
            inv['amortized_amount'] 
            for inv in investments
            ]
        self.assertEqual(amortized_amounts, [0.0,0.0,0.0])

    def test__amortized_amount__afterAmortization(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.amortize('2017-11-20')
        investment_ids = self.Investment.search([])
        investments = self.Investment.read(investment_ids,['amortized_amount'])
        amortized_amounts = [
            inv['amortized_amount'] 
            for inv in investments
            ]
        self.assertEqual(amortized_amounts, [4.0,60.0,40.0])

    def test__amortized_amount__afterAmortizationLimited(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.amortize('2017-07-28')
        investment_ids = self.Investment.search([])
        investments = self.Investment.read(investment_ids,['amortized_amount'])
        amortized_amounts = [
            inv['amortized_amount'] 
            for inv in investments
            ]
        self.assertEqual(amortized_amounts, [0.0,60.0,40.0])

    def test__amortized_amount__secondAmortization(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.amortize('2017-11-20')
        self.Investment.amortize('2018-11-20')
        investment_ids = self.Investment.search([])
        investments = self.Investment.read(investment_ids,['amortized_amount'])
        amortized_amounts = [
            inv['amortized_amount'] 
            for inv in investments
            ]
        self.assertEqual(amortized_amounts, [8.0,120.0,80.0])



    def test__migrate_created_from_accounting__whenLogEmpty(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        investment_id = self.Investment.search([])[0]
        self.Investment.write(investment_id, dict(log=''))

        self.Investment.migrate_created_from_accounting()

        investment = self.Investment.read(investment_id,['log'])
        self.assertEqual(investment['log'], 
            u'[2015-07-29 09:39:07.70812 Mònica Nuell] PAYMENT: Remesa efectuada\n'
            u'[2015-07-29 09:39:07.70812 Webforms] ORDER: Formulari emplenat\n'
            )

    def test__migrate_created_from_accounting__keepsPreviousContent(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        investment_id = self.Investment.search([])[0]
        self.Investment.write(investment_id, dict(log='previous content'))

        self.Investment.migrate_created_from_accounting()

        investment = self.Investment.read(investment_id,['log'])
        self.assertEqual(investment['log'], 
            u'previous content')

    def test__create_from_accounting__writes_log(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        investment_id = self.Investment.search([])[0]
        investment = self.Investment.read(investment_id,['log'])
        self.assertEqual(investment['log'], 
            u'[2015-07-29 09:39:07.70812 Mònica Nuell] PAYMENT: Remesa efectuada\n'
            u'[2015-07-29 09:39:07.70812 Webforms] ORDER: Formulari emplenat\n'
            )

    def test__amortize__writes_log(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.amortize('2017-11-20')

        investment_id = self.Investment.search([])[0]
        investment = self.Investment.read(investment_id,['log'])
        self.assertRegexpMatches(investment['log'].split('\n')[0],
            u'\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}.\\d{5} '
                u'David García Garzón\\] '
                u'AMORTIZATION: Generada amortització de 4.00 € pel 2017-07-29'
            )
        self.assertEqual('\n'.join(investment['log'].split('\n')[1:]),
            u'[2015-07-29 09:39:07.70812 Mònica Nuell] PAYMENT: Remesa efectuada\n'
            u'[2015-07-29 09:39:07.70812 Webforms] ORDER: Formulari emplenat\n'
            )





@unittest.skipIf(not dbconfig, "depends on ERP")
class InvestmentCommand_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        clear()

    def tearDown(self):
        clear()

    def test_clean(self):
        data = listactive(csv=True)
        self.assertEqual(data,'')

    def test_create_toEarly(self):
        create(stop="2015-06-29")
        data = listactive(csv=True)
        self.assertEqual(data,'')

    def test_create_onlyFirstBatch(self):
        create(stop="2015-06-30")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_firstBatch_twice(self):
        create(stop="2015-06-30")
        create(stop="2015-06-30")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_firstAndSecondBatch(self):
        create(stop="2015-07-03")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_justSecondBatch(self):
        create(start='2015-07-02', stop="2015-07-03")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_waitTwoDays(self):
        create(stop="2015-06-30", waitingDays=2)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_expireOneYear(self):
        create(stop="2015-06-30", waitingDays=2, expirationYears=1)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_inTwoBatches(self):
        create(stop="2015-06-30", waitingDays=0, expirationYears=1)
        create(stop="2015-07-03")
        data = listactive(csv=True)

    def test_listactive_withMember(self):
        create(stop="2015-06-30")
        data = listactive(csv=True, member=469)
        self.assertMultiLineEqual(data,
            '469\tFalse\tFalse\t3\n'
            '469\tFalse\tFalse\t2\n'
        )

    def test_listactive_withStop_shouldBeFirstBatch(self):
        create(stop="2015-07-03", waitingDays=0, expirationYears=1)
        data = listactive(csv=True, stop="2015-06-30")
        self.assertB2BEqual(data)

    def test_listactive_withStopAndNoActivatedInvestments_shouldBeFirstBatch(self):
        # Second batch is not activated, and is not shown even if we extend stop
        create(stop="2015-06-30", waitingDays=0, expirationYears=1)
        create(start="2015-07-03", stop="2015-07-03")
        data = listactive(csv=True, stop="2020-07-03")
        self.assertB2BEqual(data)

    def test_listactive_withStart_excludeExpired_shouldBeSecondBatch(self):
        # Expired contracts do not show if start is specified and it is earlier
        create(stop="2015-07-03", waitingDays=0, expirationYears=1)
        data = listactive(csv=True, start="2016-07-01")
        self.assertB2BEqual(data)

    def test_listactive_withStartAndNoActivatedInvestments_shouldBeFirstBatch(self):
        # Unactivated contracts are not listed if start is specified
        create(stop="2015-06-30", waitingDays=0, expirationYears=1) # listed
        create(start="2015-07-03", stop="2015-07-03") # unlisted
        data = listactive(csv=True, start="2016-06-30")
        self.assertB2BEqual(data)

    def test_listactive_withStartAndNoExpirationRunForEver_shouldBeSecondBatch(self):
        # Active with no deactivation keeps being active for ever
        create(stop="2015-06-30", waitingDays=0, expirationYears=1) # unlisted
        create(start="2015-07-03", stop="2015-07-03", waitingDays=0) # listed
        data = listactive(csv=True, start="2036-06-30")
        self.assertB2BEqual(data)


    def test_activate_withStop(self):
        create(stop="2015-07-03")
        effective(stop="2015-06-30", waitingDays=0)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_activate_withStart(self):
        create(stop="2015-07-03")
        effective(start="2015-07-02", waitingDays=0)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_activate_withExpiration(self):
        create(stop="2015-07-03")
        effective(stop="2015-06-30", waitingDays=0, expirationYears=1)
        data = listactive(csv=True)
        self.assertB2BEqual(data)


