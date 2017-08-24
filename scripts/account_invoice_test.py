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


@unittest.skipIf(not dbconfig, "depends on ERP")
class Account_Invoice_Test(unittest.TestCase):
    def setUp(self):
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


    def _test__get_investment_moveline(self):

        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        #create invoice
        invoice_ids, errors = self.Investment.create_initial_invoices([investment_id])
        self.Investment.open_invoices(invoice_ids)
        InvoicePayerWizard = self.erp.FacturacioPayInvoice
        wizid = InvoicePayerWizard.create(dict(
            amount = 4000,
            name = "The wizard",
            date = '2017-01-02',
            journal_id  = False,
            period_id  = False,
            ), context = dict(active_ids = invoice_ids))

        wizard = InvoicePayerWizard.get(wizid)
        wizard.action_pay_and_reconcile(cursor, uid, wizid, dict(
            active_ids = invoice_ids))

        move_line_returned = self.AccountInvoice.get_investment_moveline(invoice_ids[0])

        self.assertMovelineEquals(move_line_id, """
        move_line_returned = self.AccountInvoice.get_investment_moveline(invoice_ids[0])
            move_id: {move_id}
            id: {moveline_id}
            account_id: 1635000{codisoci}
            credit: 4000
            debit: 0
        """)



unittest.TestCase.__str__ = unittest.TestCase.id

if __name__=='__main__':
    unittest.main()

# vim: et ts=4 sw=4
    
