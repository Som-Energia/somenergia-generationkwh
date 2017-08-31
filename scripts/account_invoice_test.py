#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

dbconfig = None
try:
    import dbconfig
except ImportError:
    pass
from datetime import date
from yamlns import namespace as ns
import erppeek_wst
import generationkwh.investmentmodel as gkwh


@unittest.skipIf(not dbconfig, "depends on ERP")
class Account_Invoice_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Investment = self.erp.GenerationkwhInvestment
        self.AccountInvoice = self.erp.AccountInvoice
        self.MailMockup = self.erp.GenerationkwhMailmockup
        self.Investment.dropAll()
        self.MailMockup.activate()

    def tearDown(self):
        self.MailMockup.deactivate()
        self.erp.rollback()
        self.erp.close()


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

    def test__get_investment__found(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        #create invoice
        invoice_ids, errs = self.Investment.create_initial_invoices([investment_id])

        investment_from_invoice = self.AccountInvoice.get_investment(invoice_ids[0])

        self.assertEqual(investment_id, investment_from_invoice)

    def test__get_investment__otherJournalsIgnored(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        #create invoice
        invoice_ids,errs = self.Investment.create_initial_invoices([investment_id])
        invoice = self.AccountInvoice.write(invoice_ids[0], dict(
            journal_id = 2 # random
            ))
        investment_from_invoice = self.AccountInvoice.get_investment(invoice_ids[0])

        self.assertFalse(investment_from_invoice)


    def test__get_investment__notFound(self):
        invoice_id = 23132 # random
        investment_id = self.AccountInvoice.get_investment(invoice_id)
        self.assertFalse(investment_id)

    def test__is_investment_payment_invoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        #create invoice
        invoice_ids,errs = self.Investment.create_initial_invoices([investment_id])

        self.assertTrue(self.AccountInvoice.is_investment_payment(invoice_ids[0]))

    def test__is_investment_payment_null_invoice(self):
        invoice_id = 999999999 # does not exists
        self.assertFalse(self.AccountInvoice.is_investment_payment(invoice_id))

    def test__is_investment_payment_unamed_invoice(self):
        invoice_id = 325569 # name null
        self.assertFalse(self.AccountInvoice.is_investment_payment(invoice_id))

    def test__is_investment_payment_amortization_invoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2014-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        #create invoice
        self.Investment.mark_as_paid([investment_id], '2014-01-01')
        amortinv_ids,errs = self.Investment.amortize('2017-01-02',[investment_id])
        self.assertFalse(self.AccountInvoice.is_investment_payment(amortinv_ids[0]))

    def test__paymentWizard(self):

        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        invoice_ids, errors = self.Investment.create_initial_invoices([investment_id])
        self.Investment.open_invoices(invoice_ids)

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(invoice_ids[0], 'movement description')

        invoice = self.AccountInvoice.read(invoice_ids[0], ['residual'])
        self.assertEqual(invoice['residual'], 0.0)

    def test__paymentWizard__remesa(self):

        investment_id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.121',
            'ES7712341234161234567890',
        )
        investment_id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02', # order_date
            2000,
            '10.10.23.122',
            'ES7712341234161234567890',
        )
        investment_ids = [investment_id1, investment_id2]
        invoice_ids, errors = self.Investment.create_initial_invoices(investment_ids)
        self.Investment.open_invoices(invoice_ids)
        self.Investment.invoices_to_payment_order(invoice_ids, gkwh.investmentPaymentMode)

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(invoice_ids[0], 'movement description')

        invoice = self.AccountInvoice.read(invoice_ids[0], ['residual'])
        self.assertEqual(invoice['residual'], 0.0)


    def test__get_investment_moveline(self):

        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        investment = self.Investment.read(investment_id, ['name'])
        invoice_ids, errors = self.Investment.create_initial_invoices([investment_id])
        self.Investment.open_invoices(invoice_ids)

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(invoice_ids[0], 'my movement')

        move_line_id = self.AccountInvoice.get_investment_moveline(invoice_ids[0])

        move_line = ns(self.erp.AccountMoveLine.read(move_line_id, [
            'name',
            'account_id',
            'debit',
            'credit',
            ]))
        move_line.account_id = move_line.account_id[1]

        self.assertNsEqual(move_line, """
            name: 'Inversió {investment_name} '
            id: {moveline_id}
            account_id: 1635000{nsoci:>05} {surname}, {name}
            credit: 4000.0
            debit: 0.0
        """.format(
            investment_name = investment['name'],
            moveline_id = move_line_id,
            **self.personalData
        ))

    def test__accounting__openInvestmentInvoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
 
        invoice_ids, errors = self.Investment.investment_payment([investment_id])

        investment_name = self.Investment.read(investment_id,['name'])['name']
        invoice_number = self.AccountInvoice.read(invoice_ids[0], ['number'])['number']
        invoice_ref = invoice_number.replace("/","")

        self.assertInvoiceAccountingEqual(invoice_ids[0], """
        movelines:
        - account_id: 1635000{nsoci:>05} {surname}, {name}
          amount_to_pay: 4000.0
          credit: 4000.0
          debit: 0.0
          invoice: 'CI: {invoice_number} {investment_name}-FACT'
          journal_id: Factures GenerationkWh
          name: 'Inversió {investment_name} '
          payment_type: Recibo domiciliado
          product_id: '[GENKWH_AE] Accions Energètiques Generation kWh'
          quantity: 40.0
          ref: '{invoice_ref}'
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: -4000.0
          credit: 0.0
          debit: 4000.0
          invoice: 'CI: {invoice_number} {investment_name}-FACT'
          journal_id: Factures GenerationkWh
          name: {investment_name}-FACT
          payment_type: Recibo domiciliado
          product_id: false
          quantity: 1.0
          ref: '{invoice_ref}'
        """.format(
            investment_name = investment_name,
            invoice_number = invoice_number,
            invoice_ref = invoice_ref,
            **self.personalData
        ))

    def test__accounting__paidInvestmentInvoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        invoice_ids, errors = self.Investment.investment_payment([investment_id])

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(invoice_ids[0], 'movement description')

        investment_name = self.Investment.read(investment_id,['name'])['name']
        invoice_number = self.AccountInvoice.read(invoice_ids[0], ['number'])['number']
        invoice_ref = invoice_number.replace("/","")
        self.assertAccountingByInvoiceNumberRefEqual(invoice_ids[0], """
        movelines:
        - account_id: 1635000{nsoci:>05} {surname}, {name}
          amount_to_pay: 4000.0
          credit: 4000.0
          debit: 0.0
          invoice: 'CI: {invoice_number} {investment_name}-FACT'
          journal_id: Factures GenerationkWh
          name: 'Inversió {investment_name} '
          payment_type: Recibo domiciliado
          product_id: '[GENKWH_AE] Accions Energètiques Generation kWh'
          quantity: 40.0
          ref: '{invoice_ref}'
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: 0.0 # TURNED ZERO
          credit: 0.0
          debit: 4000.0
          invoice: 'CI: {invoice_number} {investment_name}-FACT'
          journal_id: Factures GenerationkWh
          name: {investment_name}-FACT
          payment_type: Recibo domiciliado
          product_id: false
          quantity: 1.0
          ref: '{invoice_ref}'
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: 0.0
          credit: 4000.0
          debit: 0.0
          invoice: false
          journal_id: BANC INVERSIONS
          name: movement description
          payment_type: []
          product_id: false
          quantity: false
          ref: '{invoice_ref}'
        - account_id: 572000000003 CAIXA ARQUITECTES (inversio)
          amount_to_pay: -4000.0
          credit: 0.0
          debit: 4000.0
          invoice: false
          journal_id: BANC INVERSIONS
          name: movement description
          payment_type: []
          product_id: false
          quantity: false
          ref: '{invoice_ref}'
        """.format(
            investment_name = investment_name,
            invoice_number = invoice_number,
            invoice_ref = invoice_ref,
            **self.personalData
        ))

    def test__accounting__openAmortizationInvoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
 
        self.Investment.mark_as_paid([investment_id], '2017-01-02')
        amortization_ids, errors = self.Investment.amortize(
            '2019-01-02', [investment_id])

        investment_name = self.Investment.read(investment_id,['name'])['name']
        invoice_number = self.AccountInvoice.read(amortization_ids[0], ['number'])['number']
        invoice_ref = invoice_number.replace("/","")

        self.assertInvoiceAccountingEqual(amortization_ids[0], """
        movelines:
        - account_id: 1635000{nsoci:>05} {surname}, {name}
          amount_to_pay: -160.0
          credit: 0.0
          debit: 160.0
          invoice: 'SI: {invoice_number} {investment_name}-AMOR2019'
          journal_id: Factures GenerationkWh
          name: 'Amortització fins a 02/01/2019 de {investment_name} '
          payment_type: Transferencia
          product_id: '[GENKWH_AMOR] Amortització Generation kWh'
          quantity: 1.0
          ref: {investment_name}-AMOR2019
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: 160.0
          credit: 160.0
          debit: 0.0
          invoice: 'SI: {invoice_number} {investment_name}-AMOR2019'
          journal_id: Factures GenerationkWh
          name: {investment_name}-AMOR2019
          payment_type: Transferencia
          product_id: false
          quantity: 1.0
          ref: {investment_name}-AMOR2019
        """.format(
            investment_name = investment_name,
            invoice_number = invoice_number,
            invoice_ref = invoice_ref,
            **self.personalData
        ))

    def test__accounting__paidAmortizationInvoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
 
        self.Investment.mark_as_paid([investment_id], '2017-01-02')
        amortization_ids, errors = self.Investment.amortize(
            '2019-01-02', [investment_id])

        investment_name = self.Investment.read(investment_id,['name'])['name']
        invoice_number = "2017/5218" # TODO: ask
        invoice_ref = invoice_number.replace("/","")

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(amortization_ids[0], 'movement description')
        self.assertAccountingByInvoiceNameRefEqual(amortization_ids[0], """
        movelines:
        - account_id: 1635000{nsoci:>05} {surname}, {name}
          amount_to_pay: -160.0
          credit: 0.0
          debit: 160.0
          invoice: 'SI: {invoice_number} {investment_name}-AMOR2019'
          journal_id: Factures GenerationkWh
          name: 'Amortització fins a 02/01/2019 de {investment_name} '
          payment_type: Transferencia
          product_id: '[GENKWH_AMOR] Amortització Generation kWh'
          quantity: 1.0
          ref: {investment_name}-AMOR2019
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: 0.0 # CHANGED!!
          credit: 160.0
          debit: 0.0
          invoice: 'SI: {invoice_number} {investment_name}-AMOR2019'
          journal_id: Factures GenerationkWh
          name: {investment_name}-AMOR2019
          payment_type: Transferencia
          product_id: false
          quantity: 1.0
          ref: {investment_name}-AMOR2019
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: 0.0
          credit: 0.0
          debit: 160.0
          invoice: false
          journal_id: BANC INVERSIONS
          name: movement description
          payment_type: []
          product_id: false
          quantity: false
          ref: {investment_name}-AMOR2019
        - account_id: 572000000003 CAIXA ARQUITECTES (inversio)
          amount_to_pay: 160.0
          credit: 160.0
          debit: 0.0
          invoice: false
          journal_id: BANC INVERSIONS
          name: movement description
          payment_type: []
          product_id: false
          quantity: false
          ref: {investment_name}-AMOR2019

        """.format(
            investment_name = investment_name,
            invoice_number = invoice_number,
            invoice_ref = invoice_ref,
            **self.personalData
        ))

    def assertInvoiceAccountingEqual(self, invoice_id, expected):
        invoice = self.erp.AccountInvoice.read(invoice_id, [
            'move_id',
        ])

        result = self.movelines([
            ('move_id','=',invoice['move_id'] and invoice['move_id'][0]),
        ])
        self.assertNsEqual(result, expected)

    def assertAccountingByInvoiceNumberRefEqual(self, invoice_id, expected):
        invoice = self.erp.AccountInvoice.read(invoice_id, [
            'number',
        ])

        result = self.movelines([
            # TODO: Cap altra cosa mes?? amb el ref es prou??
            #('journal_id','=',invoice['journal_id'][0]),
            ('ref','=',invoice.get('number','caca').replace('/','')),
        ])
        self.assertNsEqual(result, expected)

    def assertAccountingByInvoiceNameRefEqual(self, invoice_id, expected):
        invoice = self.erp.AccountInvoice.read(invoice_id, [
            'name',
            'journal_id',
        ])

        result = self.movelines([
            # TODO: Cap altra cosa mes?? amb el ref es prou??
            #('journal_id','=',invoice['journal_id'][0]),
            ('ref','=',invoice.get('name','caca')),
        ])
        self.assertNsEqual(result, expected)


    def movelines(self, conditions):
        fields = [
            "account_id",
            "amount_to_pay",
            "invoice",
            "journal_id",
            "debit",
            "name",
            "credit",
            "payment_type",
            "product_id",
            "quantity",
            "ref",
            ]
        fks = [
            "invoice",
            "journal_id",
            "account_id",
            "product_id",
            "payment_type",
            ]
        line_ids = self.erp.AccountMoveLine.search(conditions)
        result = ns(movelines=[])
        movelines = result.movelines
        lines = self.erp.AccountMoveLine.read(
            sorted(line_ids),fields,order='id')
        for line in lines:
            moveline = ns(sorted(line.items()))
            del moveline.id
            for field in fks:
                moveline[field]=moveline[field] and moveline[field][1]
            movelines.append(moveline)
        return result


unittest.TestCase.__str__ = unittest.TestCase.id

if __name__=='__main__':
    unittest.main()

# vim: et ts=4 sw=4
