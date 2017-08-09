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
        self.Investment.dropAll()

    def tearDown(self):
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

unittest.TestCase.__str__ = unittest.TestCase.id

if __name__=='__main__':
    unittest.main()

# vim: et ts=4 sw=4
    
