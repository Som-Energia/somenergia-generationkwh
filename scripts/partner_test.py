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
import generationkwh.investmentmodel as gkwh


@unittest.skipIf(not dbconfig, "depends on ERP")
class Partner_Test(unittest.TestCase):

    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Investment = self.erp.GenerationkwhInvestment
        self.Country = self.erp.ResCountry
        self.PaymentOrder = self.erp.PaymentOrder
        self.receiveMode = gkwh.investmentPaymentMode
        self.payMode = gkwh.amortizationPaymentMode

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

    def test__get_or_create_payment_order__badName(self):
        order_id = self.Investment.get_or_create_open_payment_order("BAD MODE")
        self.assertEqual(order_id, False)

    def test__get_or_create_payment_order__calledTwiceReturnsTheSame(self):
        first_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
        second_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
        self.assertEqual(first_order_id, second_order_id)

    def test__get_or_create_payment_order__noDraftCreatesANewOne(self):
        first_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
        self.PaymentOrder.write(first_order_id, dict(
            state='done',
        ))
        second_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
        self.assertNotEqual(first_order_id, second_order_id)

    def test__get_or_create_payment_order__properFieldsSet(self):
        first_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
        self.PaymentOrder.write(first_order_id, dict(
            state='done',
        ))

        second_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
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


    def test__get_or_create_payment_order__receivableInvoice(self):

        previous_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
        self.PaymentOrder.write(previous_order_id, dict(
            state='done',
        ))

        order_id = self.Investment.get_or_create_open_payment_order(
            self.receiveMode,
            True, #use_invoice
            )

        order = (self.PaymentOrder.read(order_id, ['create_account_moves','type']))
        order.pop('id')
        self.assertNsEqual(order, ns.loads("""\
                create_account_moves: bank-statement
                type: receivable
                """))

    def test__get_or_create_payment_order__payableInvoice(self):
        previous_order_id = self.Investment.get_or_create_open_payment_order(self.payMode)
        self.PaymentOrder.write(previous_order_id, dict(
            state='done',
        ))

        order_id = self.Investment.get_or_create_open_payment_order(
            self.payMode,
            True, #use_invoice
            )

        order = (self.PaymentOrder.read(order_id, ['create_account_moves','type']))
        order.pop('id')
        self.assertNsEqual(order, ns.loads("""\
                create_account_moves: bank-statement
                type: payable
                """))


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
