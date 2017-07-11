#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

dbconfig = None
try:
    import dbconfig
except ImportError:
    pass
import datetime
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
        self.Investment = self.erp.GenerationkwhInvestment
        self.Investment.dropAll()

    def tearDown(self):
        self.erp.rollback()

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

    def test__migrate__updatesOrderDate(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)

        investment_id = self.Investment.search([])[0]
        self.Investment.write(investment_id, dict(order_date=False))

        self.Investment.migrate_created_from_accounting([investment_id])

        investment = self.Investment.read(investment_id,['order_date'])
        self.assertEqual(investment['order_date'], '2015-07-29')


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
        self.Investment = self.erp.GenerationkwhInvestment
        self.Investment.dropAll()

    def tearDown(self):
        self.erp.rollback()


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
            2000,
            '10.10.23.123',
            )

        self.assertTrue(id)

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')

        self.Investment.unlink(id)

        self.assertLogEquals(log,
            u'ORDER: Formulari emplenat des de 10.10.23.123\n'
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
            nshares: 20
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
            2001,
            '10.10.23.123',
            )
        self.assertFalse(id) # ??

    @unittest.skip('Not implemented')
    def test__create_from_form__whenNotAMember(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.123',
            )
        self.assertFalse(id) # ??

    @unittest.skip('Not implemented')
    def test__create_from_form__withNonDivisibleAmount(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2003,
            '10.10.23.123',
            )
        self.assertFalse(id) # ??

    def test__charge__singleInvestment(self):
    
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.123',
            )

        self.Investment.charge([id], '2017-01-03')

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')

        self.Investment.unlink(id)

        self.assertLogEquals(log,
            u'PAYED: Remesada al compte\n'
            u'ORDER: Formulari emplenat des de 10.10.23.123\n'
            )
        
        self.assertNsEqual(investment, """
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2017-01-01'
            purchase_date: '2017-01-03' # Changed!
            first_effective_date: false
            last_effective_date: false
            nshares: 20
            amortized_amount: 0.0
            move_line_id: false
            active: true
            """.format(
                id=id,
                **self.personalData
                ))

    def test__charge__samePurchaseDateSetToAll(self):
    
        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.123',
            )

        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02', # order_date
            2000,
            '10.10.23.123',
            )

        self.Investment.charge([id1,id2], '2017-01-03')
        
        result = self.Investment.read([id1,id2], ['purchase_date'])
        
        self.assertNsEqual(ns(data=result), """\
            data:
            - 
              purchase_date: '2017-01-03'
              id: {id1}
            -
              purchase_date: '2017-01-03'
              id: {id2}
            """.format(id1=id1, id2=id2))


    def test__charge__oldLogKept(self):
    
        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            )

        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02', # order_date
            2000,
            '10.10.23.2',
            )

        self.Investment.charge([id1,id2], '2017-01-03')
        
        result = self.Investment.read([id1,id2], ['log'])
        
        self.assertLogEquals(result[0]['log'],
            u'PAYED: Remesada al compte\n'
            u'ORDER: Formulari emplenat des de 10.10.23.1\n'
            )
        
        self.assertLogEquals(result[1]['log'],
            u'PAYED: Remesada al compte\n'
            u'ORDER: Formulari emplenat des de 10.10.23.2\n'
            )

    def assertInvoiceInfoEqual(self, invoice_id, expected):
        def proccesLine(line):
            line = ns(line)
            line.product_id = line.product_id[1]
            line.account_id = line.account_id[1]
            line.uos_id = line.uos_id[1]
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
        ]))
        invoice.journal_id = invoice.journal_id[1]
        invoice.partner_bank = invoice.partner_bank[1] if invoice.partner_bank else "None"
        invoice.invoice_line = [
            proccesLine(line)
            for line in self.InvoiceLine.read(invoice.invoice_line, [])
            ]
        self.assertNsEqual(invoice, expected)


    def test__create_amortization_invoice(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            )

        self.Investment.charge([id], '2017-01-03')
        invoice_id = self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80)
        self.assertTrue(invoice_id)

        investment = self.Investment.browse(id)

        self.assertInvoiceInfoEqual(invoice_id, """\
            account_id:
            - 2307
            - 410000{nsoci:0>6s} {surname}, {name}
            amount_total: 80.0
            amount_untaxed: 80.0
            date_invoice: '{invoice_date}'
            id: {id}
            invoice_line:
            - origin: false
              uos_id: PCE
              account_id: 163500000000 Otras deudas, con otras partes vinculadas
              name: 'Amortització fins a 30/01/2018 de {investment_name} '
              invoice_id:
              - {id}
              - 'SI:  {investment_name}-AMOR{year}'
              price_unit: 80.0
              price_subtotal: 80.0
              invoice_line_tax_id: []
              note: false
              discount: 0.0
              account_analytic_id: false
              quantity: 1.0
              product_id: '[GENKWH_AMOR] Amortització Generation kWh'
            journal_id: Factures Amortitzacions GenerationkWh
            name: {investment_name}-AMOR{year}
            partner_bank: {iban}
            partner_id:
            - {partnerid}
            - {surname}, {name}
            payment_type:
            - 2
            - Transferencia
            type: in_invoice
            """.format(
                invoice_date = datetime.date.today(),
                id = invoice_id,
                iban = None, # 'ES77 1234 1234 1612 3456 7890', # TODO: Should be set
                year = 2018,
                investment_name = investment.name,
                ** self.personalData
            ))


if __name__=='__main__':
    unittest.main()

# vim: et ts=4 sw=4
