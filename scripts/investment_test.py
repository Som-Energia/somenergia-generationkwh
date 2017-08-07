#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

dbconfig = None
try:
    import dbconfig
except ImportError:
    pass
import datetime
from dateutil.relativedelta import relativedelta
from yamlns import namespace as ns
import erppeek_wst


@unittest.skipIf(not dbconfig, "depends on ERP")
class Investment_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Soci = self.erp.SomenergiaSoci
        self.Investment = self.erp.GenerationkwhInvestment
        self.PaymentOrder = self.erp.PaymentOrder
        self.Investment.dropAll()

    def tearDown(self):
        self.erp.rollback()
        self.erp.close()

    #TODO: move this in a utils class (copy pasted from Investment_Amortization_Test
    def assertLogEquals(self, log, expected):                                                             
        for x in log.splitlines():
            self.assertRegexpMatches(x,
                u'\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}.\\d+ [^]]+\\] .*',
                u"Linia de log con formato no estandard"
            )

        logContent = ''.join(
                x.split('] ')[1]+'\n'
                for x in log.splitlines()
                if u'] ' in x
                )
        self.assertMultiLineEqual(logContent, expected)

    #TODO: Implemented in Investment_Amortization_Test
    def assertNsEqual(self, dict1, dict2):
        def parseIfString(nsOrString):
            if type(nsOrString) in (dict, ns):
                return nsOrString
            return ns.loads(nsOrString)

        def sorteddict(d):
            if type(d) not in (dict, ns):
                return d
            return ns(sorted(
                (k, sorteddict(v))
                for k,v in d.items()
                ))
        dict1 = sorteddict(parseIfString(dict1))
        dict2 = sorteddict(parseIfString(dict2))

        return self.assertMultiLineEqual(dict1.dump(), dict2.dump())

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

    def test__create_from_accounting__seesUnactivePartner(self):

        self.Soci.write(1, dict(active=False))
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
        return [x[1:-1] for x in sorted(result)] # filter id and log

    def test__pending_amortitzations__noInvestments(self):
        self.assertEqual(self.pendingAmortizations('2017-11-20'), [])

    def test__pending_amortitzations__withDueInvestments(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.assertEqual(
            self.pendingAmortizations('2017-11-20'),[
            [1, '2017-06-30', 0, 60, 1, 24],
            [1, '2017-06-30', 0, 40, 1, 24],
            [1, '2017-07-29', 0, 4,  1, 24],
            ])

    def test__pending_amortitzations__notDue(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.assertEqual(
            self.pendingAmortizations('2017-07-28'),[
            [1, '2017-06-30', 0, 60, 1, 24],
            [1, '2017-06-30', 0, 40, 1, 24],
            ])

    def test__pending_amortitzations__whenPartiallyAmortized(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.amortize('2017-11-20')
        self.assertEqual(
            self.pendingAmortizations('2018-11-20'),[
            [1, '2018-06-30', 60, 60, 2, 24],
            [1, '2018-06-30', 40, 40, 2, 24],
            [1, '2018-07-29', 4,  4,  2, 24],
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
        self.assertLogEquals(investment['log'], 
            u'PAYMENT: Remesa efectuada\n'
            u'ORDER: Formulari emplenat\n'
            )

    def test__migrate_created_from_accounting__keepsPreviousContent(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        investment_id = self.Investment.search([])[0]
        self.Investment.write(investment_id, dict(log='previous content'))

        self.Investment.migrate_created_from_accounting()

        investment = self.Investment.read(investment_id,['log'])
        self.assertEqual(investment['log'], 
            u'previous content')

    def test__migrate_created_from_accounting__explicitIdForces(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        investment_id = self.Investment.search([])[0]
        self.Investment.write(investment_id, dict(log='previous content'))

        self.Investment.migrate_created_from_accounting([investment_id])

        investment = self.Investment.read(investment_id,['log'])
        self.assertEqual(investment['log'], 
            u'[2015-07-29 09:39:07.70812 Mònica Nuell] PAYMENT: Remesa efectuada\n'
            u'[2015-07-29 09:39:07.70812 Webforms] ORDER: Formulari emplenat\n'
            )

    def test__migrate__updatesOrderDate(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)

        investment_id = self.Investment.search([])[0]
        self.Investment.write(investment_id, dict(order_date=False))

        self.Investment.migrate_created_from_accounting([investment_id])

        investment = self.Investment.read(investment_id,['order_date'])
        self.assertEqual(investment['order_date'], '2015-07-29')

    def test__get_or_create_payment_order__badName(self):
        order_id = self.Investment.get_or_create_open_payment_order("BAD MODE")
        self.assertEqual(order_id, False)

    def test__get_or_create_payment_order__calledTwiceReturnsTheSame(self):
        first_order_id = self.Investment.get_or_create_open_payment_order('GENERATION kWh')
        second_order_id = self.Investment.get_or_create_open_payment_order('GENERATION kWh')
        self.assertEqual(first_order_id, second_order_id)

    def test__get_or_create_payment_order__noDraftCreatesANewOne(self):
        first_order_id = self.Investment.get_or_create_open_payment_order('GENERATION kWh')
        self.PaymentOrder.write(first_order_id, dict(
            state='done',
        ))
        second_order_id = self.Investment.get_or_create_open_payment_order('GENERATION kWh')
        self.assertNotEqual(first_order_id, second_order_id)

    def test__get_or_create_payment_order__properFieldsSet(self):
        first_order_id = self.Investment.get_or_create_open_payment_order('GENERATION kWh')
        self.PaymentOrder.write(first_order_id, dict(
            state='done',
        ))
        #TODO: Is necessary a second Investment for this test?
        second_order_id = self.Investment.get_or_create_open_payment_order('GENERATION kWh')
        order = ns(self.PaymentOrder.read(second_order_id,[
            "date_prefered",
            "user_id",
            "state",
            "mode",
            "type",
            "create_account_moves",
        ]))
        order.user_id = order.user_id[0]
        order.mode = order.mode[1]
        self.assertNsEqual(order, ns.loads("""\
             id: {}
             create_account_moves: direct-payment
             date_prefered: fixed
             mode: GENERATION kWh
             state: draft
             type: receivable
             user_id: {}
            """.format(
                second_order_id,
                order.user_id,
            )))


@unittest.skipIf(not dbconfig, "depends on ERP")
class Investment_Amortization_Test(unittest.TestCase):

    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Invoice = self.erp.AccountInvoice
        self.InvoiceLine = self.erp.AccountInvoiceLine
        self.Partner = self.erp.ResPartner
        self.Investment = self.erp.GenerationkwhInvestment

    def tearDown(self):
        self.erp.rollback()
        self.erp.close()


    def assertNsEqual(self, dict1, dict2):
        def parseIfString(nsOrString):
            if type(nsOrString) in (dict, ns):
                return nsOrString
            return ns.loads(nsOrString)

        def sorteddict(d):
            if type(d) not in (dict, ns):
                return d
            return ns(sorted(
                (k, sorteddict(v))
                for k,v in d.items()
                ))
        dict1 = sorteddict(parseIfString(dict1))
        dict2 = sorteddict(parseIfString(dict2))

        return self.assertMultiLineEqual(dict1.dump(), dict2.dump())

    def assertLogEquals(self, log, expected):
        for x in log.splitlines():
            self.assertRegexpMatches(x,
                u'\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}.\\d+ [^]]+\\] .*',
                u"Linia de log con formato no estandard"
            )
            
        logContent = ''.join(
                x.split('] ')[1]+'\n'
                for x in log.splitlines()
                if u'] ' in x
                )
        self.assertMultiLineEqual(logContent, expected)
        
    def test__create_from_form__allOk(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )

        self.assertTrue(id)

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        
        self.Investment.unlink(id)

        self.assertLogEquals(log,
            u'FORMFILLED: Formulari omplert des de la IP 10.10.23.123, Quantitat: 4000 €, IBAN: ES7712341234161234567890\n'
            )
        
        self.assertRegexpMatches(name,r'^GKWH[0-9]{5}$')
        self.assertNsEqual(investment, """
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2017-01-01'
            purchase_date: false
            first_effective_date: false
            last_effective_date: false
            nshares: 40
            amortized_amount: 0.0
            move_line_id: false
            active: true
            """.format(
                id=id,
                **self.personalData
                ))
            

    @unittest.skip('Not implemented')
    def test__create_from_form__whenBadOrderDate(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            'baddate', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.assertFalse(id) # ??

    @unittest.skip('Not implemented')
    def test__create_from_form__whenNotAMember(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.assertFalse(id) # ??

    def test__create_from_form__withNonDivisibleAmount(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4003,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.assertFalse(id)
    
    def test__set_paid__singleInvestment(self):
    
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )

        self.Investment.set_paid([id], '2017-01-03')

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        self.Investment.unlink(id)

        self.assertLogEquals(log,
            u'PAID: Pagament de 2000 € remesat al compte ES7712341234161234567890 [None]\n'
            u'FORMFILLED: Formulari omplert des de la IP 10.10.23.123, Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )
        
        self.assertNsEqual(investment, """
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2017-01-01'
            purchase_date: '2017-01-03' # Changed!
            first_effective_date: false
            last_effective_date: '2042-01-03'
            nshares: 20
            amortized_amount: 0.0
            move_line_id: false
            active: true
            """.format(
                id=id,
                **self.personalData
                ))

    def test__set_paid__samePurchaseDateSetToAll(self):
    
        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )

        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02', # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )

        self.Investment.set_paid([id1,id2], '2017-01-03')
        
        result = self.Investment.read(
            [id1,id2],
            ['purchase_date'],
            order='id')
        
        self.assertNsEqual(ns(data=result), """\
            data:
            - purchase_date: '2017-01-03'
              id: {id1}
            - purchase_date: '2017-01-03'
              id: {id2}
            """.format(id1=id1, id2=id2))

    def test__set_paid__oldLogKept(self):
    
        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02', # order_date
            2000,
            '10.10.23.2',
            'ES7712341234161234567890',
            )

        self.Investment.set_paid([id1,id2], '2017-01-03')
        
        result = self.Investment.read([id1,id2], ['log'], order='id')
        
        self.assertLogEquals(result[0]['log'],
            u'PAID: Pagament de 2000 € remesat al compte ES7712341234161234567890 [None]\n'
            u'FORMFILLED: Formulari omplert des de la IP 10.10.23.1, Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )
        
        self.assertLogEquals(result[1]['log'],
            u'PAID: Pagament de 2000 € remesat al compte ES7712341234161234567890 [None]\n'
            u'FORMFILLED: Formulari omplert des de la IP 10.10.23.2, Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

    def assertInvoiceInfoEqual(self, invoice_id, expected):
        def proccesLine(line):
            line = ns(line)
            line.product_id = line.product_id[1]
            line.account_id = line.account_id[1]
            line.uos_id = line.uos_id[1]
            line.note = ns.loads(line.note) if line.note else line.note
            del line.id
            return line

        invoice = ns(self.Invoice.read(invoice_id, [
            'amount_total',
            'amount_untaxed',
            'partner_id',
            'type',
            'name',
            'journal_id',
            'account_id',
            'partner_bank',
            'payment_type',
            'date_invoice',
            'invoice_line',
            'check_total',
            'origin',
        ]))
        invoice.journal_id = invoice.journal_id[1]
        invoice.partner_bank = invoice.partner_bank[1] if invoice.partner_bank else "None"
        invoice.account_id = invoice.account_id[1]
        invoice.invoice_line = [
            proccesLine(line)
            for line in self.InvoiceLine.read(invoice.invoice_line, [])
            ]
        self.assertNsEqual(invoice, expected)

    def test__create_initial_invoice(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        invoice_id =  self.Investment.create_initial_invoice(id)

        self.assertTrue(invoice_id)

        investment = self.Investment.browse(id)

        self.assertInvoiceInfoEqual(invoice_id, """\
            account_id: 410000{p.nsoci:0>6s} {p.surname}, {p.name}
            amount_total: 2000.0
            amount_untaxed: 2000.0
            check_total: 2000.0
            date_invoice: '{invoice_date}'
            id: {id}
            invoice_line:
            - origin: false
              uos_id: PCE
              account_id: 163500{p.nsoci:0>6s} {p.surname}, {p.name}
              name: 'Inversió {investment_name} '
              invoice_id:
              - {id}
              - 'CI:  {investment_name}-FACT'
              price_unit: 100.0
              price_subtotal: 2000.0
              invoice_line_tax_id: []
              note: false
              discount: 0.0
              account_analytic_id: false
              quantity: 20.0
              product_id: '[GENKWH_AE] Accions Energètiques Generation kWh'
            journal_id: Factures GenerationkWh
            name: {investment_name}-FACT
            origin: {investment_name}
            partner_bank: {iban}
            partner_id:
            - {p.partnerid}
            - {p.surname}, {p.name}
            payment_type:
            - 1 # TODO
            - Recibo domiciliado
            type: out_invoice
            """.format(
            invoice_date=datetime.date.today(),
            id=invoice_id,
            iban='ES77 1234 1234 1612 3456 7890',
            year=2018,
            investment_name=investment.name,
            p=self.personalData,
            investment_id=id
            ))

    def test__create_amortization_invoice(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        self.Investment.set_paid([id], '2017-01-03')
        invoice_id = self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80, 1, 24)
        self.assertTrue(invoice_id)

        investment = self.Investment.browse(id)

        self.assertInvoiceInfoEqual(invoice_id, """\
            account_id: 410000{p.nsoci:0>6s} {p.surname}, {p.name}
            amount_total: 80.0
            amount_untaxed: 80.0
            check_total: 80.0
            date_invoice: '{invoice_date}'
            id: {id}
            invoice_line:
            - origin: false
              uos_id: PCE
              account_id: 163500{p.nsoci:0>6s} {p.surname}, {p.name}
              name: 'Amortització fins a 30/01/2018 de {investment_name} '
              invoice_id:
              - {id}
              - 'SI:  {investment_name}-AMOR{year}'
              price_unit: 80.0
              price_subtotal: 80.0
              invoice_line_tax_id: []
              note:
                pendingCapital: 1920.0
                amortizationDate: '2018-01-30'
                amortizationNumber: 1
                amortizationTotalNumber: 24
                investmentId: {investment_id}
                investmentName: {investment_name}
                investmentPurchaseDate: '2017-01-03'
                investmentLastEffectiveDate: '2042-01-03'
                investmentInitialAmount: 2000
              discount: 0.0
              account_analytic_id: false
              quantity: 1.0
              product_id: '[GENKWH_AMOR] Amortització Generation kWh'
            journal_id: Factures GenerationkWh
            name: {investment_name}-AMOR{year}
            origin: {investment_name}
            partner_bank: {iban}
            partner_id:
            - {p.partnerid}
            - {p.surname}, {p.name}
            payment_type:
            - 2
            - Transferencia
            type: in_invoice
            """.format(
                invoice_date = datetime.date.today(),
                id = invoice_id,
                iban = 'ES77 1234 1234 1612 3456 7890',
                year = 2018,
                investment_name = investment.name,
                p = self.personalData,
                investment_id = id
            ))

    def test__create_amortization_invoice__twice(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        inv = self.Investment.read(id, ['name'])

        self.Investment.set_paid([id], '2017-01-03')
        invoice_id = self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80, 1, 24)

        with self.assertRaises(Exception) as ctx:
            self.Investment.create_amortization_invoice(
                id, '2018-01-30', 80, 1, 24)

        self.assertIn(
            "Amortization notification {name}-AMOR2018 already exist".format(**inv),
            unicode(ctx.exception),
            )
    
    def test__create_amortization_invoice__errorWhenNoBank(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )       
        self.Partner.write(self.personalData.partnerid,dict(bank_inversions = False))
        try:
            self.Investment.create_amortization_invoice(id, '2018-01-30' , 80, 1, 24)
        except:
            return

        self.fail("Hauria de sortir un error quan no hi ha Partner.bank_inversions")

    def test__amortization_invoice_report(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000, # amount_in_euros
            '10.10.23.1', # ip
            'ES7712341234161234567890', # iban
            )

        self.Investment.set_paid([id], '2017-01-03')
        invoice_id = self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80, 1, 24)

        inv = ns(self.Investment.read(id, [
            'name',
        ]))

        result = self.Invoice.investmentAmortization_notificationData_asDict([invoice_id])
        self.assertNsEqual(ns(result), """\
            inversionName: {inv.name}
            ownerName: {surname}, {name}
            ownerNif: {nif}
            receiptDate: '{today}'
            inversionInitialAmount: 2.000,00
            inversionPendingCapital: 1.920,00
            inversionPurchaseDate: '03/01/2017'
            inversionExpirationDate: '03/01/2042'
            amortizationAmount: 80,00
            amortizationName: {inv.name}-AMOR2018
            amortizationTotalPayments: 24
            inversionBankAccount: ES77 1234 1234 1612 3456 7890
            amortizationDate: '30/01/2018'
            amortizationNumPayment: 1
            """.format(
                today = datetime.date.today().strftime("%d/%m/%Y"),
                nif = self.personalData.nif,
                name = self.personalData.name,
                surname = self.personalData.surname,
                inv = inv,
        ))

    def test__create_from_form__ibanIsSet(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        partner = self.Partner.browse(self.personalData.partnerid)
        self.assertTrue(partner.bank_inversions)

    def test__create_amortization_invoice__withUnnamedInvestment(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2016-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        self.Investment.write(id, dict(
            name=None)
            )

        self.Investment.set_paid([id], '2016-01-03')

        invoice_id = self.Investment.create_amortization_invoice(
            id, '2018-01-03', 80, 1, 24)

        invoice = self.Invoice.browse(invoice_id)
        self.assertEqual(invoice.name,
            "GENKWHID{}-AMOR2018".format(id))

    def test__amortize__writes_log(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01',  # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
        )
        self.Investment.set_paid([investment_id], '2000-01-05')
        self.Investment.amortize('2002-01-06', [investment_id])

        investment = self.Investment.read(investment_id, ['log'])
        self.assertLogEquals(investment['log'],
            u'AMORTIZATION: Generada amortització de 80.00 € pel 2002-01-05\n'
            u'PAID: Pagament de 2000 € remesat al compte ES7712341234161234567890 [None]\n'
            u'FORMFILLED: Formulari omplert des de la IP 10.10.23.1, Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

    def test__open_invoice__allOk(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
        )

        self.Investment.set_paid([id], '2017-01-03')
        invoice_id = self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80, 1, 24)
        self.assertTrue(invoice_id)

        self.Investment.open_invoice(invoice_id)

        from datetime import datetime, timedelta
        date_due_dt = datetime.today() + timedelta(7)
        date_due = date_due_dt.strftime('%Y-%m-%d')
        invoices_changes = self.Invoice.read(invoice_id,
            ['state',
             'date_due',
             ])

        self.assertEqual(invoices_changes, dict(
            id = invoice_id,
            state = 'open',
            date_due = date_due,
            ))

@unittest.skipIf(not dbconfig, "depends on ERP")
class InvestmentPartner_Test(unittest.TestCase):

    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Partner = self.erp.ResPartner
        self.Investment = self.erp.GenerationkwhInvestment
        self.Country = self.erp.ResCountry

    def tearDown(self):
        self.erp.rollback()
        self.erp.close()


    def assertNsEqual(self, dict1, dict2):
        def parseIfString(nsOrString):
            if type(nsOrString) in (dict, ns):
                return nsOrString
            return ns.loads(nsOrString)

        def sorteddict(d):
            if type(d) not in (dict, ns):
                return d
            return ns(sorted(
                (k, sorteddict(v))
                for k,v in d.items()
                ))
        dict1 = sorteddict(parseIfString(dict1))
        dict2 = sorteddict(parseIfString(dict2))

        return self.assertMultiLineEqual(dict1.dump(), dict2.dump())

    def test__get_or_create_partner_bank__whenExists(self):

        partner_id = self.personalData.partnerid
        expected = self.erp.ResPartnerBank.search([
            ('partner_id','=', partner_id),
            ])[0]
        iban = self.erp.ResPartnerBank.read(expected, [
            'iban',
            ])['iban']
        result = self.Investment.get_or_create_partner_bank(
            partner_id, iban)
        self.assertEqual(expected, result)

    def test__get_or_create_partner_bank__whenNew(self):

        partner_id = self.personalData.partnerid
        iban = 'ES8901825726580208779553'
        country_id = self.Country.search([('code', '=', 'ES')])[0]
        
        shouldBeNone = self.erp.ResPartnerBank.search([
            ('iban', '=', iban),
            ('partner_id','=',partner_id),
            ])
        self.assertFalse(shouldBeNone,
            "Partner already has such iban")

        result = self.Investment.get_or_create_partner_bank(
            partner_id, iban)

        self.assertTrue(result,
            "Should have been created")

        bank_id = self.erp.ResPartnerBank.search([
            ('iban', '=', iban),
            ('partner_id','=',partner_id),
            ])[0]
        self.assertEqual(bank_id, result)

        bank = ns(self.erp.ResPartnerBank.read(
            bank_id, [
            'name',
            'state',
            'iban',
            'partner_id',
            'country_id',
            'acc_country_id',
            'state_id',
            ]))
        for a in 'partner_id country_id acc_country_id state_id'.split():
            bank[a] = bank[a] and bank[a][0]

        self.assertNsEqual(bank, ns(
            id = bank_id,
            name = '',
            state = 'iban',
            iban = iban,
            partner_id = partner_id,
            country_id = country_id,
            acc_country_id = country_id,
            state_id = False,
            ))

    def test__check_spanish_account__lenghtNot20(self):
        self.assertEqual(
            self.Investment.check_spanish_account('1234161234567890'),
            False)

    def test__check_spanish_account__invalid(self):
        self.assertEqual(
            self.Investment.check_spanish_account('00001234061234567890'),
            False)

    def test__check_spanish_account__knownBank(self):
        self.assertEqual(
            self.Investment.check_spanish_account(
                '14911234761234567890'),
            dict(
                acc_number = '1491 1234 76 1234567890',
                bank_name = 'TRIODOS BANK',
            ))

    def test__check_spanish_account__unknownBank(self):
        self.assertEqual(
            self.Investment.check_spanish_account(
                '00001234161234567890'),
            dict(acc_number= "0000 1234 16 1234567890",))

    def test__check_spanish_account__nonDigitsIgnored(self):
        self.assertEqual(
            self.Investment.check_spanish_account(
                'E000F0-12:34161234567890'),
            dict(acc_number= "0000 1234 16 1234567890",))

    def test__clean_iban__beingCanonical(self):
        self.assertEqual(
            self.Investment.clean_iban("ABZ12345"),
            "ABZ12345")

    def test__clean_iban__havingLower(self):
        self.assertEqual(
            self.Investment.clean_iban("abc123456"),
            "ABC123456")

    def test__clean_iban__weirdSymbols(self):
        self.assertEqual(
            self.Investment.clean_iban("ABC:12.3 4-5+6"),
            "ABC123456")

    def test__check_iban__valid(self):
        self.assertEqual(
            self.Investment.check_iban('ES7712341234161234567890'),
            'ES7712341234161234567890')

    def test__check_iban__notNormalized(self):
        self.assertEqual(
            self.Investment.check_iban('ES77 1234-1234.16 1234567890'),
            'ES7712341234161234567890')

    def test__check_iban__badIbanCrc(self):
        self.assertEqual(
            self.Investment.check_iban('ES8812341234161234567890'),
            False)

    def test__check_iban__goodIbanCrc_badCCCCrc(self):
        self.assertEqual(
            self.Investment.check_iban('ES0212341234001234567890'),
            False)

    def test__check_iban__fromForeignCountry_notAcceptedYet(self):
        self.assertEqual(
            # Arabian example from wikipedia
            self.Investment.check_iban('SA03 8000 0000 6080 1016 7519'),
            False)
    
unittest.TestCase.__str__ = unittest.TestCase.id


if __name__=='__main__':
    unittest.main()

# vim: et ts=4 sw=4
