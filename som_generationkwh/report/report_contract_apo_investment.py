# -*- coding: utf-8 -*-
from osv import osv, fields
from yamlns import namespace as ns
import pooler
from generationkwh.isodates import isodate
from dateutil.relativedelta import relativedelta
from datetime import datetime

class GenerationkWhInvestment(osv.osv):
    _name = 'generationkwh.investment'
    _inherit = 'generationkwh.investment'

    def generation_contract_from_investment_data(self, cursor, uid, ids):
        def dateFormat(dateIso):
            return isodate(dateIso).strftime("%d/%m/%Y")
        def moneyFormat(amount):
            return "{:,.2f}".format(amount).replace(',','X').replace('.',',').replace('X','.')

        report = ns()
        pool = pooler.get_pool(cursor.dbname)
        Invoice = pool.get('account.invoice')
        Partner = pool.get('res.partner')
        PartnerAddress = pool.get('res.partner.address')
        InvoiceLine = pool.get('account.invoice.line')
        Investment = pool.get('generationkwh.investment')

        inv_id = ids[0]

        if not ids: raise Exception("No investment provided")

        invoice = Invoice.read(cursor, uid, account_id, [
            'date_invoice',
            'partner_id',
            'name',
            'member_id',
            'invoice_line',
            'amount_total',
            'name',
            'partner_bank',
            'address_invoice_id',
            ])

        partner = Partner.read(cursor, uid, invoice['partner_id'][0], [
            'vat',
            'name',
        ])

        #partner_address = PartnerAddress.read(cursor, uid, invoice['address_invoice_id'][0], ['email', 'street'])
        partner_address_id = Partner.address_get(cursor, uid,[partner_id], ['contact', 'invoice'])['invoice']
        invoice_line = InvoiceLine.read(cursor,uid, invoice['invoice_line'][0],['note'])
        mutable_information = ns.loads(invoice_line['note'] or '{}')

        investment = Investment.read(cursor, uid, mutable_information.investmentId, ['order_date'])
        report.invoiceDate = dateFormat(invoice['date_invoice'])
        # TODO: non spanish vats not covered by tests
        report.ownerNif = partner['vat'][2:] if partner['vat'][:2]=='ES' else partner['vat']

        report.inversionName = mutable_information.investmentName
        report.ownerName = partner['name']
        report.inversionPendingCapital = moneyFormat(float(mutable_information.pendingCapital))
        report.inversionInitialAmount = moneyFormat(mutable_information.investmentInitialAmount)
        report.inversionOrderDate = datetime.strftime(datetime.strptime(investment['order_date'],'%Y-%m-%d'),'%d/%m/%Y')
        report.inversionBankAccount = invoice['partner_bank'][1]
        report.partnerAddress = partner_address['street']
        report.partnerEmail = partner_address['email']

        return report

GenerationkWhInvestment()
# vim: et ts=4 sw=4

#address_get(cr, uid, [partner_id], ['contact', 'invoice'])