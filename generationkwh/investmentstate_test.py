# -*- coding: utf-8 -*-

from .investmentstate import (
    InvestmentState,
    InvestmentStateError as StateError,
    forceUnicode,
    GenerationkwhState,
    AportacionsState
    )
import unittest
from yamlns import namespace as ns
from .isodates import isodate
from .testutils import assertNsEqual

class InvestmentState_Test(unittest.TestCase):

    user = "MyUser"
    timestamp = "2000-01-01 00:00:00.123435"
    logprefix = "[{} {}] ".format(timestamp, user)

    assertNsEqual = assertNsEqual

    def assertExceptionMessage(self, e, text):
        self.assertEqual(forceUnicode(e.args[0]), text)

    def setUp(self):
        self.maxDiff = None

    def setupInvestment(self, **kwds):
        if kwds and 'log' not in kwds:
            kwds.update(log = "previous log\n")
        if kwds and 'actions_log' not in kwds:
            kwds.update(actions_log = "actions: []")
        return GenerationkwhState(self.user, self.timestamp, **kwds)

    def assertChangesEqual(self, inv, attr,
            expectedlog=None, noPreviousLog=False):
        changes=ns(inv.changed())
        log = changes.pop('log','')
        actions = changes.pop('actions_log','actions: []')
        self.assertNsEqual(changes, attr)
        if expectedlog is None: return
        self.assertMultiLineEqual(log,
            self.logprefix + expectedlog +
            ("" if noPreviousLog else u"previous log\n")
            )

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

    def assertActionsEqual(self, inv, expected):
        actions = ns.loads(inv.changed().get('actions_log','actions: []'))
        lastAction = actions.actions[-1] if actions and actions.actions else {}
        self.assertNsEqual(lastAction, expected)

    # Infrastructure tests

    def test_changes_by_default_noChange(self):
        inv = self.setupInvestment()
        self.assertNsEqual(inv.changed(), """\
            {}
            """)

    def test_init_withBadParams(self):
        with self.assertRaises(StateError) as ctx:
            self.setupInvestment(
                badParameter = 'value',
                )
        self.assertExceptionMessage(ctx.exception,
            "Investments have no 'badParameter' attribute")

    def test_getattr(self):
        inv = self.setupInvestment(
            nominal_amount = 100,
            )
        self.assertEqual(inv.nominal_amount, 100)


    def test_getattr_badattr(self):
        inv = self.setupInvestment(
            nominal_amount = 100,
            )
        with self.assertRaises(AttributeError) as ctx:
            inv.badattrib
        self.assertExceptionMessage(ctx.exception,
            "badattrib")

    def test_setattr_fails(self):
        inv = self.setupInvestment(
            nominal_amount = 100,
            )
        with self.assertRaises(AttributeError) as ctx:
            inv.nominal_amount = 5
        self.assertExceptionMessage(ctx.exception,
            "nominal_amount")

    def test_values_takesInitialValues(self):
        inv = self.setupInvestment(
            name = "GKWH00069",
            log = 'my log',
            )
        self.assertNsEqual(inv.values(), """
            name: GKWH00069
            log: my log
            actions_log: 'actions: []'
            """)

    def test_values_avoidsAliasing(self):
        inv = self.setupInvestment(
            name = "GKWH00069",
            log = 'my log',
            )
        values = inv.values()
        values.newAttribute = 'value'
        self.assertNsEqual(inv.values(), """
            name: GKWH00069
            log: my log
            actions_log: 'actions: []'
            """)

    def test_values_mergesChanges(self):
        inv = self.setupInvestment(
            name = "GKWH00069",
            nominal_amount = 200.,
            purchase_date = False,
            log = 'my log',
            draft=True,
            )
        inv.correct(
            from_amount= 200.0,
            to_amount = 300.0,
        )
        values = inv.values()
        values.pop('actions_log')
        self.assertNsEqual(values, """
            name: GKWH00069
            nominal_amount: 300.0
            paid_amount: 0.0
            purchase_date: False
            draft: True
            log: '[2000-01-01 00:00:00.123435 MyUser] CORRECTED: Quantitat canviada abans del
              pagament de 200.0 € a 300.0 €

              my log'

            """)

    def test_erpChanges(self):
        inv = self.setupInvestment(log='previous value\n')

        inv.pact(
            date = isodate('2016-05-01'),
            comment = "lo dice el jefe",
            name = 'GKWH00069',
            order_date = isodate('2000-01-01'),
            purchase_date = isodate('2000-01-02'),
            first_effective_date = isodate('2000-01-03'),
            last_effective_date = isodate('2000-01-04'),
            active = False,
        )
        changes=inv.erpChanges()
        log = changes.pop('log')
        actions = changes.pop('actions_log')
        self.assertNsEqual(changes, """\
            name: GKWH00069
            order_date: 2000-01-01
            purchase_date: 2000-01-02
            first_effective_date: 2000-01-03
            last_effective_date: 2000-01-04
            active: False
            """)

        self.assertMultiLineEqual(log,
            self.logprefix + 
            u"PACT: Pacte amb l'inversor. "
            "active: False, first_effective_date: 2000-01-03, last_effective_date: 2000-01-04, name: GKWH00069, order_date: 2000-01-01, purchase_date: 2000-01-02 "
            "Motiu: lo dice el jefe\n"
            u"previous value\n")

    def test_erpChanges_changingAmounts(self):
        inv = self.setupInvestment(
            nominal_amount = 100,
            purchase_date=False,
            draft=True,
            )

        inv.correct(
            from_amount = 100,
            to_amount = 200,
        )
        changes=inv.erpChanges()
        log = changes.pop('log')
        actions = changes.pop('actions_log')
        self.assertNsEqual(changes, """\
            nominal_amount: 200
            nshares: 2
            """)

    def test_erpChanges_clearsPaidAmount(self):
        inv = self.setupInvestment(
            nominal_amount = 100,
            paid_amount = 0,
            draft = False,
            )

        inv.pay(
            date = isodate('2016-05-01'),
            amount = 100,
            move_line_id = 666,
        )
        changes=inv.erpChanges()
        log = changes.pop('log')
        actions = changes.pop('actions_log')
        self.assertNsEqual(changes, """\
            #paid_amount: 100 # Excpect this one to be removed
            purchase_date: 2016-05-01
            first_effective_date: 2017-05-01
            last_effective_date: 2041-05-01
            """)

    def test_addAction_firstAction(self):
        inv = InvestmentState(self.user, self.timestamp)
        actions = inv.addAction(
            param = 'value'
            )
        self.assertNsEqual(actions, """
            actions:
            - timestamp: '{0.timestamp}'
              user: {0.user}
              param: value
            """.format(self))

    def test_addAction_secondAction(self):
        inv = InvestmentState(self.user, self.timestamp,
            actions_log = """
                actions:
                - timestamp: 'asdafs'
                  user: Fulanito
                  param1: value1
                """,
        )
        actions = inv.addAction( param2 = 'value2')
        self.assertNsEqual(actions, """
            actions:
            - timestamp: 'asdafs'
              user: Fulanito
              param1: value1
            - timestamp: '{0.timestamp}'
              user: {0.user}
              param2: value2
            """.format(self))

    def test_addAction_unparseable(self):
        inv = InvestmentState(self.user, self.timestamp,
            actions_log = " : badcontent",
        )
        actions = inv.addAction( param2 = 'value2')
        self.assertNsEqual(actions, """
            actions:
            - content: " : badcontent"
              type: unparseable
            - timestamp: '{0.timestamp}'
              user: {0.user}
              param2: value2
            """.format(self))

    def test_addAction_notADict(self):
        inv = InvestmentState(self.user, self.timestamp,
            actions_log = "badcontent",
        )
        actions = inv.addAction( param2 = 'value2')
        self.assertNsEqual(actions, """
            actions:
            - content: "badcontent"
              type: badcontent
            - timestamp: '{0.timestamp}'
              user: {0.user}
              param2: value2
            """.format(self))

    def test_addAction_badRootKey(self):
        inv = InvestmentState(self.user, self.timestamp,
            actions_log = "badroot: lala",
        )
        actions = inv.addAction( param2 = 'value2')
        self.assertNsEqual(actions, """
            actions:
            - content: "badroot: lala"
              type: badroot
            - timestamp: '{0.timestamp}'
              user: {0.user}
              param2: value2
            """.format(self))

    def test_addAction_notInnerList(self):
        inv = InvestmentState(self.user, self.timestamp,
            actions_log = "actions: notalist",
        )
        actions = inv.addAction( param2 = 'value2')
        self.assertNsEqual(actions, """
            actions:
            - content: "actions: notalist"
              type: badcontent
            - timestamp: '{0.timestamp}'
              user: {0.user}
              param2: value2
            """.format(self))



    # Helper and getter tests

    def test_fistEffectiveDate(self):
        self.assertEqual(isodate('2017-04-28'),
            InvestmentState.firstEffectiveDate(isodate('2016-04-28')))

    def test_fistEffectiveDate_pioners(self):
        self.assertEqual(isodate('2017-03-28'),
            InvestmentState.firstEffectiveDate(isodate('2016-04-27')))

    @unittest.skip("First investment didn't take into account bisixtile year")
    def test_fistEffectiveDate_bisextile(self):
        self.assertEqual(isodate('2021-01-28'),
            InvestmentState.firstEffectiveDate(isodate('2020-01-28')))

    def test_hasEffectivePeriod_whenUnstarted(self):
        result = InvestmentState.hasEffectivePeriod(
            first_date = None,
            last_date = isodate('2018-01-01'),
            )
        self.assertEqual(result, False)

    def test_hasEffectivePeriod_whenUnfinished(self):
        result = InvestmentState.hasEffectivePeriod(
            first_date = isodate('2018-01-01'),
            last_date = None,
            )
        self.assertEqual(result, True)

    def test_hasEffectivePeriod_whenSameDay(self):
        result = InvestmentState.hasEffectivePeriod(
            first_date = isodate('2018-01-01'),
            last_date = isodate('2018-01-01'),
            )
        self.assertEqual(result, True)

    def test_hasEffectivePeriod_whenOrdered(self):
        result = InvestmentState.hasEffectivePeriod(
            first_date = isodate('2018-01-01'),
            last_date = isodate('2018-02-01'),
            )
        self.assertEqual(result, True)

    def test_hasEffectivePeriod_whenCrossed(self):
        result = InvestmentState.hasEffectivePeriod(
            first_date = isodate('2018-01-02'),
            last_date = isodate('2018-01-01'),
            )
        self.assertEqual(result, False)

    def pendingAmortizations(self, purchase_date, current_date, investment_amount, amortized_amount):
        inv = self.setupInvestment(
            purchase_date=purchase_date and isodate(purchase_date),
            nominal_amount=investment_amount,
            amortized_amount=amortized_amount,
        )
        return inv.pendingAmortizations(isodate(current_date))


    def test_pendingAmortizations_unpaid(self):
        self.assertEqual(
            self.pendingAmortizations(
                purchase_date=False,
                current_date='2002-01-01',
                investment_amount=1000,
                amortized_amount=0,
                ), [
            ])

    def test_pendingAmortizations_justFirstAmortization(self):
        self.assertEqual(
            self.pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2002-01-01',
                investment_amount=1000,
                amortized_amount=0,
                ), [
                (1, 24, '2002-01-01', 40),
            ])

    def test_pendingAmortizations_justBeforeFirstOne(self):
        self.assertEqual(
            self.pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2001-12-31',
                investment_amount=1000,
                amortized_amount=0,
                ), [])

    def test_pendingAmortizations_justSecondOne(self):
        self.assertEqual(
            self.pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2003-01-01',
                investment_amount=1000,
                amortized_amount=0,
                ), [
                (1, 24, '2002-01-01', 40),
                (2, 24, '2003-01-01', 40),
            ])

    def test_pendingAmortizations_alreadyAmortized(self):
        self.assertEqual(
            self.pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2003-01-01',
                investment_amount=1000,
                amortized_amount=40,
                ), [
                (2, 24, '2003-01-01', 40),
            ])

    def test_pendingAmortizations_lastDouble(self):
        self.assertEqual(
            self.pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2025-01-01',
                investment_amount=1000,
                amortized_amount=920,
                ), [
                (24, 24, '2025-01-01', 80),
            ])

    def test_pendingAmortizations_allDone(self):
        self.assertEqual(
            self.pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2050-01-01',
                investment_amount=1000,
                amortized_amount=1000,
                ), [
            ])

    def test_pendingAmortizations_allPending(self):
        self.assertEqual(
            self.pendingAmortizations(
                purchase_date='2000-01-01',
                current_date='2040-01-01',
                investment_amount=1000,
                amortized_amount=0,
                ), [
                ( 1, 24, '2002-01-01', 40),
                ( 2, 24, '2003-01-01', 40),
                ( 3, 24, '2004-01-01', 40),
                ( 4, 24, '2005-01-01', 40),
                ( 5, 24, '2006-01-01', 40),
                ( 6, 24, '2007-01-01', 40),
                ( 7, 24, '2008-01-01', 40),
                ( 8, 24, '2009-01-01', 40),
                ( 9, 24, '2010-01-01', 40),
                (10, 24, '2011-01-01', 40),
                (11, 24, '2012-01-01', 40),
                (12, 24, '2013-01-01', 40),
                (13, 24, '2014-01-01', 40),
                (14, 24, '2015-01-01', 40),
                (15, 24, '2016-01-01', 40),
                (16, 24, '2017-01-01', 40),
                (17, 24, '2018-01-01', 40),
                (18, 24, '2019-01-01', 40),
                (19, 24, '2020-01-01', 40),
                (20, 24, '2021-01-01', 40),
                (21, 24, '2022-01-01', 40),
                (22, 24, '2023-01-01', 40),
                (23, 24, '2024-01-01', 40),
                (24, 24, '2025-01-01', 80),
            ])



    # Public actions tests

    def test_order(self):
        inv = self.setupInvestment()

        inv.order(
            name = 'GKWH00069',
            date = isodate('2000-01-01'),
            ip = '8.8.8.8',
            amount = 300.0,
            iban = 'ES7712341234161234567890',
        )
        changes=inv.changed()
        log = changes.pop('log')
        self.assertChangesEqual(inv, """\
            name: GKWH00069
            order_date: 2000-01-01
            purchase_date: null
            first_effective_date: null
            last_effective_date: null
            active: True
            nominal_amount: 300.0
            amortized_amount: 0.0
            paid_amount: 0.0
            draft: True
            """)

        self.assertMultiLineEqual(log,
            self.logprefix + u"ORDER: "
            u"Formulari omplert des de la IP 8.8.8.8, "
            u"Quantitat: 300 €, IBAN: ES7712341234161234567890\n")

        self.assertActionsEqual(inv, u"""
            type: order
            user: {user}
            timestamp: '{timestamp}'
            amount: 300.0
            ip: 8.8.8.8
            iban: ES7712341234161234567890
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))

    def test_order_withNoIban(self):
        inv = self.setupInvestment()

        inv.order(
            name = 'GKWH00069',
            date = isodate('2000-01-01'),
            ip = '8.8.8.8',
            amount = 300.0,
            iban = '', # This changes
        )
        changes=inv.changed()
        log = changes.pop('log','')
        self.assertChangesEqual(inv, """\
            name: GKWH00069
            order_date: 2000-01-01
            purchase_date: null
            first_effective_date: null
            last_effective_date: null
            active: True
            nominal_amount: 300.0
            amortized_amount: 0.0
            paid_amount: 0.0
            draft: True
            """)

        self.assertMultiLineEqual(log,
            self.logprefix + u"ORDER: "
            u"Formulari omplert des de la IP 8.8.8.8, "
            u"Quantitat: 300 €, IBAN: None\n")

        self.assertActionsEqual(inv, u"""
            type: order
            user: {user}
            timestamp: '{timestamp}'
            amount: 300.0
            ip: 8.8.8.8
            iban: null
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))


    def test_invoice(self):
        inv = self.setupInvestment(
            draft = True,
        )

        inv.invoice()
        self.assertChangesEqual(inv, """\
            draft: false
            """,
            u"INVOICED: Facturada i remesada\n"
            )

        self.assertActionsEqual(inv, u"""
            type: invoice
            user: {user}
            timestamp: '{timestamp}'
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))

    def test_invoice_notDraft(self):
        inv = self.setupInvestment(
            draft = False,
        )
        with self.assertRaises(StateError) as ctx:
            inv.invoice()
        self.assertExceptionMessage(ctx.exception,
            "Already invoiced")
        self.assertChangesEqual(inv, """\
            {}
            """
            # TODO: Log Error
            )

    def test_pay(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            purchase_date = False,
            draft = False,
        )

        inv.pay(
            date = isodate('2016-05-01'),
            amount = 300.0,
            move_line_id = 666,
        )
        self.assertChangesEqual(inv, """\
            purchase_date: 2016-05-01
            first_effective_date: 2017-05-01
            last_effective_date: 2041-05-01
            paid_amount: 300.0
            """,
            u"PAID: Pagament de 300 € efectuat "
            u"[666]\n"
            )
        self.assertActionsEqual(inv, u"""
            type: pay
            user: {user}
            timestamp: '{timestamp}'
            amount: 300.0
            move_line_id: 666
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))


    def test_pay_alreadyPaid(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            purchase_date = '2000-01-01',
            draft = False,
        )

        with self.assertRaises(StateError) as ctx:
            inv.pay(
                date = isodate('2016-05-01'),
                amount = 300.0,
                move_line_id = 666,
            )
        self.assertExceptionMessage(ctx.exception,
            "Already paid")
        self.assertChangesEqual(inv, """\
            paid_amount: 600.0
            """,
            # TODO: Log the error!
            u"PAID: Pagament de 300 € efectuat "
            u"[666]\n"
            )

    def test_pay_wrongAmount(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            purchase_date = False,
            draft = False,
        )

        with self.assertRaises(StateError) as ctx:
            inv.pay(
                date = isodate('2016-05-01'),
                amount = 400.0, # Wrong!
                move_line_id = 666,
            )
        self.assertExceptionMessage(ctx.exception,
            "Wrong payment, expected 300.0, given 400.0")
        self.assertChangesEqual(inv, """\
            paid_amount: 400.0
            """,
            # TODO: Log the error!
            u"PAID: Pagament de 400 € efectuat "
            u"[666]\n"
            )

    def test_pay_draft(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            purchase_date = False,
            draft = True, # Wrong!!
        )

        with self.assertRaises(StateError) as ctx:
            inv.pay(
                date = isodate('2016-05-01'),
                amount = 300.0, # Wrong!
                move_line_id = 666,
            )
        self.assertExceptionMessage(ctx.exception,
            "Not invoiced yet")
        self.assertChangesEqual(inv, """\
            {}
            """
            # TODO: Log the error!
            )


    def test_unpay(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            purchase_date = '2000-01-01',
            draft = False,
        )

        inv.unpay(
            amount = 300.0,
            move_line_id = 666,
        )
        self.assertChangesEqual(inv, """\
            purchase_date: null
            first_effective_date: null
            last_effective_date: null
            paid_amount: 0.0
            """,
            u"UNPAID: Devolució del pagament de 300.0 € [666]\n"
            )
        self.assertActionsEqual(inv, u"""
            type: unpay
            user: {user}
            timestamp: '{timestamp}'
            amount: 300.0
            move_line_id: 666
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))

    def test_unpay_unpaid(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            purchase_date = False,
            draft = False,
        )

        with self.assertRaises(StateError) as ctx:
            inv.unpay(
                amount = 300.0,
                move_line_id = 666,
            )
        self.assertExceptionMessage(ctx.exception,
            "No pending amount to unpay")
        self.assertChangesEqual(inv, """\
            {}
            """
            # TODO: Log the error!
            )

    def test_unpay_wrongAmount(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            purchase_date = '2000-01-01',
            draft = False,
        )

        with self.assertRaises(StateError) as ctx:
            inv.unpay(
                amount = 200.0,
                move_line_id = 666,
            )
        self.assertExceptionMessage(ctx.exception,
            "Unpaying wrong amount, was 200.0 expected 300.0")
        self.assertChangesEqual(inv, """\
            {}
            """
            # TODO: Log the error!
            )

    def test_unpay_draft(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            purchase_date = False,
            draft = True,
        )

        with self.assertRaises(StateError) as ctx:
            inv.unpay(
                amount = 300.0,
                move_line_id = 666,
            )
        self.assertExceptionMessage(ctx.exception,
            "Not invoiced yet")
        self.assertChangesEqual(inv, """\
            {}
            """
            # TODO: Log the error!
            )

    # TODO: unpay effective

    def test_divest_effective(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            amortized_amount = 0.0,
            purchase_date = isodate("2000-01-01"),
            first_effective_date = isodate("2000-01-01"),
            last_effective_date = isodate("2024-01-01"),
            draft = False,
        )

        inv.divest(
            date = isodate("2001-08-01"),
            move_line_id = 666,
            amount = 300.,
        )
        self.assertChangesEqual(inv, """\
            last_effective_date: 2001-08-01
            active: True
            paid_amount: 0.0
            amortized_amount: 300.0
            """,
            u'DIVESTED: Desinversió total, tornats 300.0 € [666]\n'
        )
        self.assertActionsEqual(inv, u"""
            type: divest
            user: {user}
            timestamp: '{timestamp}'
            amount: 300.0
            move_line_id: 666
            date: 2001-08-01
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))

    def test_divest_beforeEffectiveDate(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            purchase_date = isodate("2001-01-01"),
            amortized_amount = 0.0,
            first_effective_date = isodate("2001-01-01"),
            last_effective_date = isodate("2025-01-01"),
            draft = False,
        )

        inv.divest(
            date = isodate("2000-08-01"),
            move_line_id = 666,
            amount = 300.,
        )
        self.assertChangesEqual(inv, """\
            last_effective_date: 2000-08-01
            active: False
            paid_amount: 0.0
            amortized_amount: 300.0
            """,
            u'DIVESTED: Desinversió total, tornats 300.0 € [666]\n'
        )
        self.assertActionsEqual(inv, u"""
            type: divest
            user: {user}
            timestamp: '{timestamp}'
            amount: 300.0
            move_line_id: 666
            date: 2000-08-01
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))


    def test_divest_amortized(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            amortized_amount = 12.0,
            purchase_date = isodate("2000-01-01"),
            first_effective_date = isodate("2000-01-01"),
            last_effective_date = isodate("2024-01-01"),
            draft = False,
        )

        inv.divest(
            date = isodate("2001-08-01"),
            move_line_id = 666,
            amount = 288.,
        )
        self.assertChangesEqual(inv, """\
            last_effective_date: 2001-08-01
            active: True
            paid_amount: 0.0
            amortized_amount: 300.0
            """,
            u'DIVESTED: Desinversió total, tornats 288.0 € [666]\n'
        )
        self.assertActionsEqual(inv, u"""
            type: divest
            user: {user}
            timestamp: '{timestamp}'
            amount: 288.0
            move_line_id: 666
            date: 2001-08-01
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))

    def test_divest_amortizedRequiresUnamortizedAmount(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            amortized_amount = 12.0,
            purchase_date = isodate("2000-01-01"),
            first_effective_date = isodate("2001-01-01"),
            last_effective_date = isodate("2025-01-01"),
            draft = False,
        )
        with self.assertRaises(StateError) as ctx:
            inv.divest(
                date = isodate("2000-08-01"),
                amount = 300.,
                move_line_id = 666,
            )
        self.assertExceptionMessage(ctx.exception,
            u"Divesting wrong amount, tried 300.0 €, unamortized 288.0 €")

    def test_divest_unpaid(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            amortized_amount = 0.0,
            purchase_date = False,
            first_effective_date = False,
            last_effective_date = False,
            draft = False,
        )
        with self.assertRaises(StateError) as ctx:
            inv.divest(
                date = isodate("2000-08-01"),
                amount = 300.,
                move_line_id = 666,
            )
        self.assertExceptionMessage(ctx.exception,
            u"Paid amount after divestment should be 0 but was -300.0 €")

    def test_emitTransfer(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            order_date = isodate("2000-01-01"),
            purchase_date = isodate("2000-01-02"),
            first_effective_date = isodate("2001-01-02"),
            last_effective_date = isodate("2025-01-02"),
            draft = False,
        )

        inv.emitTransfer(
            date = isodate("2006-08-01"),
            move_line_id = 666,
            to_name = "GKWH00069",
            to_partner_name = "Palotes, Perico",
            amount = 300.0,
        )

        self.assertChangesEqual(inv, """
            last_effective_date: 2006-08-01
            active: True
            paid_amount: 0.0
            amortized_amount: 300.0
            """,
            u'DIVESTEDBYTRANSFER: Traspas cap a '
            u'Palotes, Perico amb codi GKWH00069 [666]\n'
            )
        self.assertActionsEqual(inv, u"""
            type: transferout
            user: {user}
            timestamp: '{timestamp}'
            amount: 300.0
            move_line_id: 666
            date: 2006-08-01
            toinvestment: GKWH00069
            topartner: Palotes, Perico
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))


    def test_emitTransfer_beforeEffectiveDate(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            order_date = isodate("2000-01-01"),
            purchase_date = isodate("2000-01-02"),
            first_effective_date = isodate("2001-01-02"),
            last_effective_date = isodate("2025-01-02"),
            draft = False,
        )

        inv.emitTransfer(
            date = isodate("2000-08-01"),
            move_line_id = 666,
            to_name = "GKWH00069",
            to_partner_name = "Palotes, Perico",
            amount = 300.0,
        )

        self.assertChangesEqual(inv, """
            last_effective_date: 2000-08-01
            active: False
            paid_amount: 0.0
            amortized_amount: 300.0
            """,
            u'DIVESTEDBYTRANSFER: Traspas cap a '
            u'Palotes, Perico amb codi GKWH00069 [666]\n'
            )
        self.assertActionsEqual(inv, u"""
            type: transferout
            user: {user}
            timestamp: '{timestamp}'
            amount: 300.0
            move_line_id: 666
            date: 2000-08-01
            toinvestment: GKWH00069
            topartner: Palotes, Perico
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))



    def test_emitTransfer_unpaid(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            order_date = isodate("2000-01-01"),
            purchase_date = False,
            first_effective_date = False,
            last_effective_date = False,
            draft = False,
        )

        with self.assertRaises(StateError) as ctx:
            inv.emitTransfer(
                date = isodate("2000-08-01"),
                move_line_id = 666,
                to_name = "GKWH00069",
                to_partner_name = "Palotes, Perico",
                amount = 300.0,
            )
        self.assertExceptionMessage(ctx.exception,
            "Only paid investments can be transferred")

        self.assertChangesEqual(inv, """
            {}
            """
            # TODO: Log the error!
            )

    def test_receiveTransfer(self):
        inv = self.setupInvestment()
        origin = self.setupInvestment(
            name = "GKWH00069",
            order_date = isodate("2000-01-01"),
            purchase_date = isodate("2000-01-02"),
            first_effective_date = isodate("2001-01-02"),
            last_effective_date = isodate("2025-01-02"),
            amortized_amount = 0.0,
            draft = False,
            )
        inv.receiveTransfer(
            name = 'GKWH00666',
            date = isodate("2001-01-02"),
            move_line_id = 666,
            amount = 300.0,
            origin=origin,
            origin_partner_name = "Palotes, Perico",
        )
        
        self.assertChangesEqual(inv, """
            name: GKWH00666
            order_date: 2000-01-01 # Same as origin
            purchase_date: 2000-01-02 # Same as origin
            first_effective_date: 2001-01-03 # Next day of the transaction date
            last_effective_date: 2025-01-02 # Same as origin
            active: True
            paid_amount: 300.0
            nominal_amount: 300.0
            amortized_amount: 0.0
            draft: false
            """,
            u'CREATEDBYTRANSFER: Creada per traspàs de '
            u'GKWH00069 a nom de Palotes, Perico [666]\n',
            noPreviousLog=True,
            )
        self.assertActionsEqual(inv, u"""
            type: transferin
            user: {user}
            timestamp: '{timestamp}'
            date: 2001-01-02
            frominvestment: GKWH00069
            frompartner: Palotes, Perico
            move_line_id: 666
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))

    def test_receiveTransfer_beforeEffectiveDate(self):
        origin = self.setupInvestment(
            name = "GKWH00069",
            order_date = isodate("2000-01-01"),
            purchase_date = isodate("2000-01-02"),
            first_effective_date = isodate("2001-01-02"),
            last_effective_date = isodate("2025-01-02"),
            amortized_amount = 0.0,
            draft = False,
            )
        inv = self.setupInvestment()
        inv.receiveTransfer(
            name = 'GKWH00666',
            date = isodate("2000-08-01"),
            move_line_id = 666,
            amount = 300.0,
            origin = origin,
            origin_partner_name = "Palotes, Perico",
        )
        
        self.assertChangesEqual(inv, """
            name: GKWH00666
            order_date: 2000-01-01
            purchase_date: 2000-01-02
            first_effective_date: 2001-01-02
            last_effective_date: 2025-01-02
            active: True
            paid_amount: 300.0
            nominal_amount: 300.0
            amortized_amount: 0.0
            draft: False
            """,
            u'CREATEDBYTRANSFER: Creada per traspàs de '
            u'GKWH00069 a nom de Palotes, Perico [666]\n',
            noPreviousLog=True,
            )
        self.assertActionsEqual(inv, u"""
            type: transferin
            user: {user}
            timestamp: '{timestamp}'
            date: 2000-08-01
            frominvestment: GKWH00069
            frompartner: Palotes, Perico
            move_line_id: 666
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))


    def test_receiveTransfer_unpaid(self):
        origin = self.setupInvestment(
            name = "GKWH00069",
            order_date = isodate("2000-01-01"),
            purchase_date = False,
            first_effective_date = False,
            last_effective_date = False,
            draft = False,
            )
        inv = self.setupInvestment()
        with self.assertRaises(StateError) as ctx:
            inv.receiveTransfer(
                name = 'GKWH00666',
                date = isodate("2000-08-01"),
                move_line_id = 666,
                amount = 300.0,
                origin = origin,
                origin_partner_name = "Palotes, Perico",
            )
        self.assertExceptionMessage(ctx.exception,
            "Only paid investments can be transferred")

        self.assertChangesEqual(inv, """
            {}
            """,
            # TODO: Log error
            )


    def test_pact_singleParam(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
        )

        inv.pact(
            date = isodate('2016-05-01'),
            comment = "lo dice el jefe",
            first_effective_date = isodate('2001-02-02'),
        )
        self.assertChangesEqual(inv, """\
            first_effective_date: 2001-02-02
            """,
            u"PACT: Pacte amb l'inversor. "
            u"first_effective_date: 2001-02-02"
            u" Motiu: lo dice el jefe\n"
            )
        self.assertActionsEqual(inv, u"""
            type: pact
            user: {user}
            timestamp: '{timestamp}'
            date: 2016-05-01
            comment: lo dice el jefe
            first_effective_date: 2001-02-02
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))


    def test_pact_manyParams(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
        )

        inv.pact(
            date = isodate('2016-05-01'),
            comment = "lo dice el jefe",
            first_effective_date = isodate('2001-02-02'),
            last_effective_date = isodate('2001-02-04'),
        )
        self.assertChangesEqual(inv, """\
            first_effective_date: 2001-02-02
            last_effective_date: 2001-02-04
            """,
            u"PACT: Pacte amb l'inversor. "
            u"first_effective_date: 2001-02-02, last_effective_date: 2001-02-04"
            u" Motiu: lo dice el jefe\n"
            )
        self.assertActionsEqual(inv, u"""
            type: pact
            user: {user}
            timestamp: '{timestamp}'
            date: 2016-05-01
            comment: lo dice el jefe
            first_effective_date: 2001-02-02
            last_effective_date: 2001-02-04
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))


    def test_pact_badParams(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
        )

        with self.assertRaises(StateError) as ctx:
            inv.pact(
                date = isodate('2016-05-01'),
                comment = "lo dice el jefe",
                badparam = 'value',
            )
        self.assertExceptionMessage(ctx.exception,
            "Bad parameter changed in pact 'badparam'")

    # TODO: PORAKI

    def test_correct(self):
        inv = self.setupInvestment(
            nominal_amount = 200.0,
            purchase_date = False,
        )

        inv.correct(
            from_amount= 200.0,
            to_amount = 300.0,
        )
        self.assertChangesEqual(inv, """\
            nominal_amount: 300.0
            """,
            u"CORRECTED: Quantitat canviada abans del pagament de 200.0 € a 300.0 €\n"
            )
        self.assertActionsEqual(inv, u"""
            type: correct
            user: {user}
            timestamp: '{timestamp}'
            oldamount: 200.0
            newamount: 300.0
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))

    def test_correct_badFromAmount(self):
        inv = self.setupInvestment(
            nominal_amount = 200.0,
            purchase_date = False,
        )

        with self.assertRaises(StateError) as ctx:
            inv.correct(
                from_amount= 100.0,
                to_amount = 300.0,
            )
        self.assertExceptionMessage(ctx.exception,
            "Correction not matching the 'from' amount")

    # TODO: Not enough, also if it has unpaid invoices
    def test_correct_alreadyPaid(self):
        inv = self.setupInvestment(
            nominal_amount = 200.0,
            purchase_date = isodate('2000-01-01'),
        )

        with self.assertRaises(StateError) as ctx:
            inv.correct(
                from_amount= 200.0,
                to_amount = 300.0,
            )
        self.assertExceptionMessage(ctx.exception,
            "Correction can not be done with paid investments")

    def test_partial(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            purchase_date = isodate('2000-01-01'),
        )

        inv.partial(
            amount= 100.0,
            move_line_id = 666,
        )
        self.assertChangesEqual(inv, """\
            nominal_amount: 200.0
            paid_amount: 200.0
            """,
            u"PARTIAL: Desinversió parcial de -100.0 €, en queden 200.0 € [666]\n"
            )
        self.assertActionsEqual(inv, u"""
            type: partial
            user: {user}
            timestamp: '{timestamp}'
            amount: 100.0
            move_line_id: 666
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))

    def test_partial_unpaid(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            purchase_date = False,
        )

        with self.assertRaises(StateError) as ctx:
            inv.partial(
                amount= 100.0,
                move_line_id = 666,
            )
        self.assertExceptionMessage(ctx.exception,
            "Partial divestment can be only applied to paid investments, "
            "try 'correct'")

    def test_cancel_unpaid(self):
        inv = self.setupInvestment(
            nominal_amount = 200.0,
            purchase_date = False,
            active = True,
            )
        inv.cancel()
        self.assertChangesEqual(inv, """
            active: False
            purchase_date: null
            first_effective_date: null
            last_effective_date: null
            paid_amount: 0
            """,
            u'CANCEL: La inversió ha estat cancel·lada\n'
            )
        self.assertActionsEqual(inv, u"""
            type: cancel
            user: {user}
            timestamp: '{timestamp}'
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))

    def test_cancel_draft(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            purchase_date = False,
            draft = True,
            active = True,
        )
        inv.cancel()
        self.assertChangesEqual(inv, """
            active: False
            purchase_date: null
            first_effective_date: null
            last_effective_date: null
            paid_amount: 0
            """,
            u'CANCEL: La inversió ha estat cancel·lada\n'
            )
        self.assertActionsEqual(inv, u"""
            type: cancel
            user: {user}
            timestamp: '{timestamp}'
            """.format(
                user=self.user,
                timestamp=self.timestamp,
            ))

    def test_cancel_paid(self):
        inv = self.setupInvestment(
            nominal_amount = 200.0,
            purchase_date = isodate('2001-01-02'),
            active = True,
            )
        with self.assertRaises(StateError) as ctx:
            inv.cancel()
        self.assertExceptionMessage(ctx.exception,
            "Only unpaid investments can be cancelled")

    def test_cancel_inactive(self):
        inv = self.setupInvestment(
            active = False,
            )
        with self.assertRaises(StateError) as ctx:
            inv.cancel()
        self.assertExceptionMessage(ctx.exception,
            "Inactive investments can not be cancelled")

    def test_cancel_invoiced(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            purchase_date = False,
            draft = False,
            active = True,
            )
        inv.cancel()
        self.assertChangesEqual(inv, """
            active: False
            purchase_date: null
            first_effective_date: null
            last_effective_date: null
            paid_amount: 0
            """,
            u'CANCEL: La inversió ha estat cancel·lada\n'
            )
        self.assertActionsEqual(inv, u"""
            type: cancel
            user: {user}
            timestamp: '{timestamp}'
            """.format(
                user=self.user,
                timestamp=self.timestamp,
            ))

    # TODO: amortize should check 

    def test_amortize_noPreviousAmortization(self):
        inv = self.setupInvestment(
            purchase_date=isodate('2016-01-01'),
            amortized_amount = 0.,
        )

        inv.amortize(
            date = isodate('2018-01-01'),
            to_be_amortized=40.,
        )

        self.assertChangesEqual(inv, """\
            amortized_amount: 40.0
            """,
            u"AMORTIZATION: Generada amortització de 40.00 € pel 2018-01-01\n"
            )
        self.assertActionsEqual(inv, u"""
            type: amortize
            user: {user}
            timestamp: '{timestamp}'
            amount: 40.0
            date: 2018-01-01
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))


    def test_amortize_withPreviousAmortization(self):
        inv = self.setupInvestment(
            purchase_date = isodate('2018-01-01'),
            amortized_amount = 40.,
        )

        inv.amortize(
            date = isodate('2018-01-01'),
            to_be_amortized=40.,
        )

        self.assertChangesEqual(inv, """\
            amortized_amount: 80.0
            """,
            u"AMORTIZATION: Generada amortització de 40.00 € pel 2018-01-01\n"
            )


    def test_amortize_unpaid(self):
        inv = self.setupInvestment(
            purchase_date=False,
            amortized_amount = 1000.0,
        )

        with self.assertRaises(StateError) as ctx:
            inv.amortize(
                date=isodate('2018-01-01'),
                to_be_amortized=40.0,
            )
        self.assertExceptionMessage(ctx.exception,
            u"Amortizing an unpaid investment")

    def test_migrate(self):
        inv = self.setupInvestment(
            name = "GENKWH0001",
        )
        inv.migrate(
            oldVersion = "1.0",
            newVersion = "2.0",
        )
        self.assertChangesEqual(inv, """\
            {}
            """,
            u"MIGRATED: "
            u"Migració de la versió 1.0 a 2.0\n"
            )
        self.assertActionsEqual(inv,"""
            type: migrate
            user: {user}
            timestamp: '{timestamp}'
            oldversion: '1.0'
            newversion: '2.0'
            """.format(
                user = self.user,
                timestamp = self.timestamp,
            ))



# vim: ts=4 sw=4 et
