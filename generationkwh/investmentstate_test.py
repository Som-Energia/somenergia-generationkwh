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

    def setupInvestment(self, **kwds):
        if kwds and 'log' not in kwds:
            kwds.update(log = "previous log\n")
        return InvestmentState(self.user, self.timestamp, **kwds)

    def assertChangesEqual(self, inv, attr, expectedlog=None, noPreviousLog=False):
        changes=inv.changed()
        log = changes.pop('log','')
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

    def test_order(self):
        inv = self.setupInvestment()

        inv.order(
            date = isodate('2000-01-01'),
            ip = '8.8.8.8',
            amount = 300.0,
            iban = 'ES7712341234161234567890',
        )
        changes=inv.changed()
        log = changes.pop('log')
        self.assertNsEqual(inv.changed(), """\
            order_date: 2000-01-01
            purchase_date: null
            first_effective_date: null
            last_effective_date: null
            active: True
            nominal_amount: 300.0
            paid_amount: 0.0
            """)

        self.assertMultiLineEqual(log,
            self.logprefix + u"FORMFILLED: "
            u"Formulari omplert des de la IP 8.8.8.8, "
            u"Quantitat: 300 €, IBAN: ES7712341234161234567890\n")


    def test_order_withNoIban(self):
        inv = self.setupInvestment()

        inv.order(
            date = isodate('2000-01-01'),
            ip = '8.8.8.8',
            amount = 300.0,
            iban = '', # This changes
        )
        changes=inv.changed()
        log = changes.pop('log','')
        self.assertNsEqual(inv.changed(), """\
            order_date: 2000-01-01
            purchase_date: null
            first_effective_date: null
            last_effective_date: null
            active: True
            nominal_amount: 300.0
            paid_amount: 0.0
            """)

        self.assertMultiLineEqual(log,
            self.logprefix + u"FORMFILLED: "
            u"Formulari omplert des de la IP 8.8.8.8, "
            u"Quantitat: 300 €, IBAN: None\n")


    def test_pay(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
        )

        inv.pay(
            date = isodate('2016-05-01'),
            amount = 300.0,
            iban = 'ES7712341234161234567890',
            move_line_id = 666,
        )
        self.assertChangesEqual(inv, """\
            purchase_date: 2016-05-01
            first_effective_date: 2017-05-01
            #last_effective_date: 2041-05-01 # TODO Add this
            paid_amount: 300.0
            """,
            u"PAID: Pagament de 300 € remesat "
            u"al compte ES7712341234161234567890 [666]\n"
            )

    def test_pay_alreadyPaid(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 300.0,
        )

        with self.assertRaises(Exception) as ctx:
            inv.pay(
                date = isodate('2016-05-01'),
                amount = 300.0,
                iban = 'ES7712341234161234567890',
                move_line_id = 666,
            )
        self.assertEqual(ctx.exception.message,
            "Already paid")
        self.assertChangesEqual(inv, """\
            paid_amount: 600.0
            """,
            # TODO: Log the error!
            u"PAID: Pagament de 300 € remesat "
            u"al compte ES7712341234161234567890 [666]\n"
            )

    def test_pay_wrongAmount(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
        )

        with self.assertRaises(Exception) as ctx:
            inv.pay(
                date = isodate('2016-05-01'),
                amount = 400.0, # Wrong!
                iban = 'ES7712341234161234567890',
                move_line_id = 666,
            )
        self.assertEqual(ctx.exception.message,
            "Wrong payment")
        self.assertChangesEqual(inv, """\
            paid_amount: 400.0
            """,
            # TODO: Log the error!
            u"PAID: Pagament de 400 € remesat "
            u"al compte ES7712341234161234567890 [666]\n"
            )


    def test_fistEffectiveDate(self):
        self.assertEqual(isodate('2017-04-28'),
            InvestmentState.firstEffectiveDate(isodate('2016-04-28')))

    def test_fistEffectiveDate_pioners(self):
        self.assertEqual(isodate('2017-03-28'),
            InvestmentState.firstEffectiveDate(isodate('2016-04-27')))

    def test_unpay(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 300.0,
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
            u"REFUNDED: Devolució del pagament remesat [666]\n"
            )

    # TODO: unpay wrong amount
    # TODO: unpay not paid

    def test_divest(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 300.0,
            first_effective_date = isodate("2000-01-01"),
            last_effective_date = isodate("2024-01-01"),
        )

        inv.divest(
            data = isodate("2001-08-01"),
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
        )

        inv.divest(
            data = isodate("2000-08-01"),
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
        # TODO: should be failure case
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
            first_effective_date = None,
            last_effective_date = None,
        )

        inv.divest(
            data = isodate("2000-08-01"),
            amount = 300.,
            move_line_id = 666,
        )
        self.assertChangesEqual(inv, """\
            last_effective_date: 2000-08-01
            active: False
            paid_amount: -300.0
            """,
            u'DIVESTED: Desinversió total [666]\n'
        )


    def test_emitTransfer(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 300.0,
            order_date = isodate("2000-01-01"),
            purchase_date = isodate("2000-01-02"),
            first_effective_date = isodate("2001-01-02"),
            last_effective_date = isodate("2025-01-02"),
        )

        inv.emitTransfer(
            data = isodate("2006-08-01"),
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
        )

        inv.emitTransfer(
            data = isodate("2000-08-01"),
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
        # TODO: Should be a failure case
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
            order_date = isodate("2000-01-01"),
            purchase_date = None,
            first_effective_date = None,
            last_effective_date = None,
        )

        inv.emitTransfer(
            data = isodate("2000-08-01"),
            move_line_id = 666,
            to_name = "GKWH00069",
            to_partner_name = "Palotes, Perico",
            amount = 300.0,
        )

        self.assertChangesEqual(inv, """
            last_effective_date: 2000-08-01
            active: False
            paid_amount: -300.0
            """,
            u'DIVESTEDBYTRANSFER: Traspas cap a '
            u'Palotes, Perico amb codi GKWH00069 [666]\n'
            )

    def test_receiveTransfer(self):
        inv = self.setupInvestment()
        inv.receiveTransfer(
            data = isodate("2001-08-01"),
            move_line_id = 666,
            amount = 300.0,
            from_name = "GKWH00069",
            from_partner_name = "Palotes, Perico",
            from_order_date = isodate("2000-01-01"),
            from_purchase_date = isodate("2000-01-02"),
            from_first_effective_date = isodate("2001-01-02"),
            from_last_effective_date = isodate("2025-01-02"),
        )
        
        self.assertChangesEqual(inv, """
            order_date: 2000-01-01
            purchase_date: 2000-01-02
            first_effective_date: 2001-08-02
            last_effective_date: 2025-01-02
            active: True
            paid_amount: 300.0
            nominal_amount: 300.0
            """,
            u'CREATEDBYTRANSFER: Creada per traspàs de '
            u'GKWH00069 a nom de Palotes, Perico [666]\n',
            noPreviousLog=True,
            )

    def test_receiveTransfer_beforeEffectiveDate(self):
        inv = self.setupInvestment()
        inv.receiveTransfer(
            data = isodate("2000-08-01"),
            move_line_id = 666,
            amount = 300.0,
            from_name = "GKWH00069",
            from_partner_name = "Palotes, Perico",
            from_order_date = isodate("2000-01-01"),
            from_purchase_date = isodate("2000-01-02"),
            from_first_effective_date = isodate("2001-01-02"),
            from_last_effective_date = isodate("2025-01-02"),
        )
        
        self.assertChangesEqual(inv, """
            order_date: 2000-01-01
            purchase_date: 2000-01-02
            first_effective_date: 2001-01-02
            last_effective_date: 2025-01-02
            active: True
            paid_amount: 300.0
            nominal_amount: 300.0
            """,
            u'CREATEDBYTRANSFER: Creada per traspàs de '
            u'GKWH00069 a nom de Palotes, Perico [666]\n',
            noPreviousLog=True,
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

    def test_repay(self):
        inv = self.setupInvestment(
            nominal_amount = 300.0,
            paid_amount = 0.0,
        )

        inv.repay(
            date = isodate('2016-05-01'),
            amount = 300.0,
            move_line_id = 666,
        )
        self.assertChangesEqual(inv, """\
            purchase_date: 2016-05-01
            first_effective_date: 2017-05-01
            #last_effective_date: 2041-05-01 # TODO Add this
            paid_amount: 300.0
            active: True
            """,
            u"REPAID: Pagament efectuat per transferencia bancària [666]\n"
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





# vim: ts=4 sw=4 et
