# -*- coding: utf-8 -*-
from osv import osv, fields
from yamlns import namespace as ns
import pooler
import datetime
from dateutil.relativedelta import relativedelta

class AccountInvoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def investmentAmortization_notificationData_asDict(self, cursor, uid, ids):
        return dict(self.investmentAmortization_notificationData(cursor, uid, ids))

    def investmentAmortization_notificationData(self, cursor, uid, ids):
        report = ns()
        pool = pooler.get_pool(cursor.dbname)
        Invoice = pool.get('account.invoice')
        Investment = pool.get('generationkwh.investment')
        Partner = pool.get('res.partner')
        InvoiceLine = pool.get('account.invoice.line')


        account_id = ids[0]

        invoice = Invoice.read(cursor, uid, account_id, [
            'date_invoice',
            'partner_id',
            'name',
            'member_id',
            'invoice_line',
            ])

        partner = Partner.read(cursor, uid, invoice['partner_id'][0], [
            'vat',
            'name',
        ])

        # TODO: Find a more reliable way
        investment_id = Investment.search(cursor,uid, [
            ('name','=',invoice['name'].split('-AMOR')[0]),
        ])[0]

        investment = Investment.read(cursor,uid, investment_id, [
            'name',
            'nshares',
            'amortized_amount',
            'purchase_date',
        ])
        invoice_line = InvoiceLine.read(cursor,uid, invoice['invoice_line'][0],['note'])
        mutable_information = ns.loads(invoice_line['note'] or '{}')

        report.receiptDate = invoice['date_invoice']
        # TODO: non spanish vats not covered by tests
        report.ownerNif = partner['vat'][2:] if partner['vat'][:2]=='ES' else partner['vat']
        report.inversionName = investment['name']
        report.ownerName = partner['name']
        report.inversionPendingCapital = float(mutable_information.pendingCapital)
        report.inversionInitialAmount = investment['nshares'] * 100
        report.inversionPurchaseDate = investment['purchase_date']

        purchase_date = datetime.datetime.strptime(investment['purchase_date'], "%Y-%m-%d").date()
        report.inversionExpirationDate = \
            (purchase_date + relativedelta(years=+25)).strftime("%Y-%m-%d")


        return report


        #Pending capital
        gkwhInversionDictPendCapt = Investment.read(cursor, uid, gkwhInversionId, ['amortized_amount'])
        gkwh_inv_amor_amou = [a['amortized_amount'] for a in gkwhInversionDictPendCapt]
        report.inversionPendingCapital = report.inversionInitialAmount - gkwh_inv_amor_amou[0]

        #Bank Account
        inversionDictBankAcco = Invoice.read(cursor, uid, investment_id, ['partner_bank'])
        acc_inv_bank_acco = [a['partner_bank'] for a in inversionDictBankAcco]
        report.report.inversionBankAccount = acc_inv_bank_acco[0]

        #Actual Amortization
        inversionDictActualAmor = Invoice.read(cursor, uid, investment_id, ['number'])
        acc_inv_actu_amor = [a['number'] for a in inversionDictActualAmor]
        report.amortizationName = acc_inv_actu_amor[0]

        #Amortization Amount
        inversionDictAmount = Invoice.read(cursor, uid, investment_id, ['amount_total'])
        acc_inv_amount = [a['amount_total'] for a in inversionDictAmount]
        report.amortizationAmount = acc_inv_amount[0]


        report.amortizationDate = '20-05-2017'
        report.amortizationNumPayment = '7'
        report.amortizationTotalPayments = '24'



        





        return report

AccountInvoice()
# vim: et ts=4 sw=4
