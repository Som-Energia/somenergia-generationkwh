# -*- coding: utf-8 -*-

from generationkwh.investmentstate import InvestmentState
import unittest
from yamlns import namespace as ns
from .isodates import isodate

# Readable verbose testcase listing
unittest.TestCase.__str__ = unittest.TestCase.id


class InvestmentState_Test(unittest.TestCase):

    user = "MyUser"
    timestamp = "2000-01-01 00:00:00.123435"
    logprefix = "[{} {}] ".format(timestamp, user)

    def setUp(self):
        self.maxDiff = None

    def setupInvestment(self, **kwds):
        if kwds and 'log' not in kwds:
            kwds.update(log = "previous log\n")
        return InvestmentState(self.user, self.timestamp, **kwds)

    def assertChangesEqual(self, inv, attr,
            expectedlog=None, noPreviousLog=False):
        changes=ns(inv.changed())
        log = changes.pop('log','')
        actions = changes.pop('actions','[]')
        self.assertNsEqual(changes, attr)
        if expectedlog is None: return
        self.assertMultiLineEqual(log,
            self.logprefix + expectedlog +
            ("" if noPreviousLog else u"previous log\n")
            )

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

    def test_changes_by_default_noChange(self):
        inv = self.setupInvestment()
        self.assertNsEqual(inv.changed(), """\
            {}
            """)

    def test_init_withBadParams(self):
        with self.assertRaises(Exception) as ctx:
            self.setupInvestment(
                badParameter = 'value',
                )
        self.assertEqual(ctx.exception.message,
            "Investments have no 'badParameter' attribute")

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

    def assertActionsEqual(self, inv, expected):
        actions = ns.loads(inv.changed().get('actions','actions: []'))
        lastAction = actions.actions[-1] if actions else None
        self.assertNsEqual(lastAction, expected)

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


    def test_pay(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
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
            last_effective_date: 2041-05-01 # TODO Add this
            paid_amount: 300.0
            """,
            u"PAID: Pagament de 300 € efectuat "
            u"[666]\n"
            )
    
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

    def test_pay_alreadyPaid(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 300.0,
            draft = False,
        )

        with self.assertRaises(Exception) as ctx:
            inv.pay(
                date = isodate('2016-05-01'),
                amount = 300.0,
                move_line_id = 666,
            )
        self.assertEqual(ctx.exception.message,
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
            paid_amount = 0.0,
            draft = False,
        )

        with self.assertRaises(Exception) as ctx:
            inv.pay(
                date = isodate('2016-05-01'),
                amount = 400.0, # Wrong!
                move_line_id = 666,
            )
        self.assertEqual(ctx.exception.message,
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
            paid_amount = 0.0,
            draft = True, # Wrong!!
        )

        with self.assertRaises(Exception) as ctx:
            inv.pay(
                date = isodate('2016-05-01'),
                amount = 300.0, # Wrong!
                move_line_id = 666,
            )
        self.assertEqual(ctx.exception.message,
            "Not invoiced yet")
        self.assertChangesEqual(inv, """\
            {}
            """
            # TODO: Log the error!
            )


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

    def test_unpay(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 300.0,
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

    def test_unpay_unpaid(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
            draft = False,
        )

        with self.assertRaises(Exception) as ctx:
            inv.unpay(
                amount = 300.0,
                move_line_id = 666,
            )
        self.assertEqual(ctx.exception.message,
            "No pending amount to unpay")
        self.assertChangesEqual(inv, """\
            {}
            """
            # TODO: Log the error!
            )

    def test_unpay_wrongAmount(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 300.0,
            draft = False,
        )

        with self.assertRaises(Exception) as ctx:
            inv.unpay(
                amount = 200.0,
                move_line_id = 666,
            )
        self.assertEqual(ctx.exception.message,
            "Unpaying wrong amount, was 200.0 expected 300.0")
        self.assertChangesEqual(inv, """\
            {}
            """
            # TODO: Log the error!
            )

    def test_unpay_draft(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
            draft = True,
        )

        with self.assertRaises(Exception) as ctx:
            inv.unpay(
                amount = 300.0,
                move_line_id = 666,
            )
        self.assertEqual(ctx.exception.message,
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
            paid_amount = 300.0,
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
            """,
            u'DIVESTED: Desinversió total [666]\n'
        )

    def test_divest_beforeEffectiveDate(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 300.0,
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
            """,
            u'DIVESTED: Desinversió total [666]\n'
        )

    def test_divest_unpaid(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
            first_effective_date = None,
            last_effective_date = None,
            draft = False,
        )
        with self.assertRaises(Exception) as ctx:
            inv.divest(
                date = isodate("2000-08-01"),
                amount = 300.,
                move_line_id = 666,
            )
        self.assertEqual(ctx.exception.message,
            u"Paid amount after divestment should be 0 but was -300.0 €")

    def test_emitTransfer(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 300.0,
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
            """,
            u'DIVESTEDBYTRANSFER: Traspas cap a '
            u'Palotes, Perico amb codi GKWH00069 [666]\n'
            )

    def test_emitTransfer_beforeEffectiveDate(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 300.0,
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
            """,
            u'DIVESTEDBYTRANSFER: Traspas cap a '
            u'Palotes, Perico amb codi GKWH00069 [666]\n'
            )


    def test_emitTransfer_unpaid(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
            order_date = isodate("2000-01-01"),
            purchase_date = None,
            first_effective_date = None,
            last_effective_date = None,
            draft = False,
        )

        with self.assertRaises(Exception) as ctx:
            inv.emitTransfer(
                date = isodate("2000-08-01"),
                move_line_id = 666,
                to_name = "GKWH00069",
                to_partner_name = "Palotes, Perico",
                amount = 300.0,
            )
        self.assertEqual(ctx.exception.message,
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
            draft: false
            """,
            u'CREATEDBYTRANSFER: Creada per traspàs de '
            u'GKWH00069 a nom de Palotes, Perico [666]\n',
            noPreviousLog=True,
            )

    def test_receiveTransfer_beforeEffectiveDate(self):
        origin = self.setupInvestment(
            name = "GKWH00069",
            order_date = isodate("2000-01-01"),
            purchase_date = isodate("2000-01-02"),
            first_effective_date = isodate("2001-01-02"),
            last_effective_date = isodate("2025-01-02"),
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
            draft: False
            """,
            u'CREATEDBYTRANSFER: Creada per traspàs de '
            u'GKWH00069 a nom de Palotes, Perico [666]\n',
            noPreviousLog=True,
            )

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
        with self.assertRaises(Exception) as ctx:
            inv.receiveTransfer(
                name = 'GKWH00666',
                date = isodate("2000-08-01"),
                move_line_id = 666,
                amount = 300.0,
                origin = origin,
                origin_partner_name = "Palotes, Perico",
            )
        print ctx.exception
        self.assertEqual(ctx.exception.message,
            "Only paid investments can be transferred")

        self.assertChangesEqual(inv, """
            {}
            """,
            # TODO: Log error
            )


    def test_pact_singleParam(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
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

    def test_pact_manyParams(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
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

    def test_pact_badParams(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
        )

        with self.assertRaises(Exception) as ctx:
            inv.pact(
                date = isodate('2016-05-01'),
                comment = "lo dice el jefe",
                badparam = 'value',
            )
        self.assertEqual(ctx.exception.message,
            "Bad parameter changed in pact 'badparam'")

    # TODO: PORAKI

    def test_repay(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
            draft = False,
        )

        inv.repay(
            date = isodate('2016-05-01'),
            amount = 300,
            move_line_id = 666,
        )
        self.assertChangesEqual(inv, """\
            purchase_date: 2016-05-01
            first_effective_date: 2017-05-01
            last_effective_date: 2041-05-01 # TODO Add this
            paid_amount: 300.0
            active: True
            """,
            u"REPAID: Pagament de 300 € rebut per transferència bancària [666]\n"
            )

    def test_correct(self):
        inv = self.setupInvestment(
            nominal_amount = 200.0,
            paid_amount = 0.0,
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

    def test_correct_badFromAmount(self):
        inv = self.setupInvestment(
            nominal_amount = 200.0,
            paid_amount = 0.0,
        )

        with self.assertRaises(Exception) as ctx:
            inv.correct(
                from_amount= 100.0,
                to_amount = 300.0,
            )
        self.assertEqual(ctx.exception.message,
            "Correction not matching the 'from' amount")

    # TODO: Not enough, also if it has unpaid invoices
    def test_correct_alreadyPaid(self):
        inv = self.setupInvestment(
            nominal_amount = 200.0,
            paid_amount = 200.0,
        )

        with self.assertRaises(Exception) as ctx:
            inv.correct(
                from_amount= 200.0,
                to_amount = 300.0,
            )
        self.assertEqual(ctx.exception.message,
            "Correction can not be done with paid investments")

    def test_partial(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 300.0,
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

    def test_partial_unpaid(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
        )

        with self.assertRaises(Exception) as ctx:
            inv.partial(
                amount= 100.0,
                move_line_id = 666,
            )
        self.assertEqual(ctx.exception.message,
            "Partial divestment can be only applied to paid investments, "
            "try 'correct'")

    def test_values_takesInitialValues(self):
        inv = self.setupInvestment(
            name = "GKWH00069",
            log = 'my log'
            )
        self.assertNsEqual(inv.values(), """
            name: GKWH00069
            log: my log
            """)

    def test_values_avoidsAliasing(self):
        inv = self.setupInvestment(
            name = "GKWH00069",
            log = 'my log'
            )
        values = inv.values()
        values.newAttribute = 'value'
        self.assertNsEqual(inv.values(), """
            name: GKWH00069
            log: my log
            """)

    def test_values_mergesChanges(self):
        inv = self.setupInvestment(
            name = "GKWH00069",
            nominal_amount = 200.,
            paid_amount = 0.,
            log = 'my log'
            )
        inv.correct(
            from_amount= 200.0,
            to_amount = 300.0,
        )
        self.assertNsEqual(inv.values(), """
            name: GKWH00069
            nominal_amount: 300.0
            paid_amount: 0.0
            log: '[2000-01-01 00:00:00.123435 MyUser] CORRECTED: Quantitat canviada abans del
              pagament de 200.0 € a 300.0 €

              my log'

            """)

    def test_cancel(self):
        inv = self.setupInvestment(
            purchase_date = False,
            paid_amount = 0.,
            )
        inv.cancel()
        self.assertChangesEqual(inv, """
            active: False
            """,
            u'CANCEL: La inversió ha estat cancel·lada\n'
            )

    def test_cancel_paid(self):
        inv = self.setupInvestment(
            purchase_date = isodate('2001-01-02'),
            paid_amount = 300.,
            )
        with self.assertRaises(Exception) as ctx:
            inv.cancel()
        self.assertEqual(ctx.exception.message,
            "Only unpaid investments can be cancelled")

    # TODO: cancel invoiced


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

    def test_erpChanges_changinAmounts(self):
        inv = self.setupInvestment(
            nominal_amount = 100,
            paid_amount = 0,
            )

        inv.correct(
            from_amount = 100,
            to_amount = 200,
        )
        changes=inv.erpChanges()
        log = changes.pop('log')
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

        inv.repay(
            date = isodate('2016-05-01'),
            amount = 100,
            move_line_id = 666,
        )
        changes=inv.erpChanges()
        log = changes.pop('log')
        self.assertNsEqual(changes, """\
            active: True
            #paid_amount: 100 # Excpect this one to be removed
            purchase_date: 2016-05-01
            first_effective_date: 2017-05-01
            last_effective_date: 2041-05-01 # TODO Add this
            """)

    def test_amortize_noPreviousAmortization(self):
        inv = self.setupInvestment(
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

    def test_amortize_withPreviousAmortization(self):
        inv = self.setupInvestment(
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

    def test_getattr(self):
        inv = self.setupInvestment(
            nominal_amount = 100,
            paid_amount = 0,
            )
        self.assertEqual(inv.nominal_amount, 100)


    def test_getattr_badattr(self):
        inv = self.setupInvestment(
            nominal_amount = 100,
            paid_amount = 0,
            )
        with self.assertRaises(AttributeError) as ctx:
            inv.badattrib
        self.assertEqual(ctx.exception.message,
            "badattrib")

    def test_setattr_fails(self):
        inv = self.setupInvestment(
            nominal_amount = 100,
            paid_amount = 0,
            )
        with self.assertRaises(AttributeError) as ctx:
            inv.paid_amount = 5
        self.assertEqual(ctx.exception.message,
            "paid_amount")

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

    def test_invoice_notDraft(self):
        inv = self.setupInvestment(
            draft = False,
        )
        with self.assertRaises(Exception) as ctx:
            inv.invoice()
        self.assertEqual(ctx.exception.message,
            "Already invoiced")
        self.assertChangesEqual(inv, """\
            {}
            """
            # TODO: Log Error
            )



# vim: ts=4 sw=4 et
