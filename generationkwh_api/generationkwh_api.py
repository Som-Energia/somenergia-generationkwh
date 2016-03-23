# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields

from generationkwh.dealer import Dealer

import datetime
from dateutil.relativedelta import relativedelta

def isodatetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
def isodate(date):
    return date and datetime.datetime.strptime(date, '%Y-%m-%d')

# Data providers

class ErpWrapper(object):

    def __init__(self, erp, cursor, uid, context=None):
        self.erp = erp
        self.cursor = cursor
        self.uid = uid
        self.context = context

class InvestmentProvider(ErpWrapper):

    def shareContracts(self, member=None, start=None, end=None):
        """
            List active investments between start and end, both included,
            for the member of for any member if member is None.
            If start is not specified, it lists activated before end.
            If end is not specified, it list activated and not deactivated
            before start.
            If neither start or end are specified all investments are listed
            active or not.
        """
        filters = []
        if member: filters.append( ('member_id','=',member) )
        if end: filters += [
            ('activation_date','<=',end), # No activation also filtered
            ]
        if start: filters += [
            '&', 
            ('activation_date','!=',False),
            '|', 
            ('deactivation_date','>=',start),
            ('deactivation_date','=',False),
            ]

        Investments = self.erp.pool.get('generationkwh.investments')
        ids = Investments.search(self.cursor, self.uid, filters)
        contracts = Investments.read(self.cursor, self.uid, ids)

        return [
            (
                c['member_id'][0],
                isodate(c['activation_date']),
                isodate(c['deactivation_date']),
                c['nshares'],
            )
            for c in sorted(contracts, key=lambda x: x['id'] )
        ]

class HolidaysProvider(ErpWrapper):

    def get(self, start, stop):
        Holidays = self.erp.pool.get('giscedata.dfestius')
        ids = Holidays.search(self.cursor, self.uid, [
            ('name', '>=', start),
            ('name', '<=', stop),
            ], 0,None,'name desc',self.context)
        return [
            isodate(h['name'])
            for h in Holidays.read(self.cursor, self.uid,
                ids, ['name'], self.context)
            ]

# Models

class GenerationkWhTestHelper(osv.osv):
    """
        Helper model that enables accessing data providers 
        from tests written with erppeek.
    """

    _name = 'generationkwh.testhelper'
    _auto = False

    def holidays(self, cursor, uid,
            start, stop,
            context=None):
        holidaysProvider = HolidaysProvider(self, cursor, uid, context)
        return holidaysProvider.get(start, stop)

GenerationkWhTestHelper()

class GenerationkWhRemainders(osv.osv):
    """
    Remainders, in Wh, after dividing the aggregated
    production of the plants into a hourly curve of
    available kWh for a member with a given number of
    shares.
    """

    _name = "generationkwh.remainders"
    _columns = dict(
        n_shares=fields.integer(
            required=True,
            help="Number of shares"
        ),
        last_day_computed=fields.date(
            required=True,
            help="Last day computed"
        ),
        remainder_wh=fields.integer(
            required=True,
            help="Remainder in Wh"
        )
    )

    def last(self, cr, uid, context=None):
        cr.execute("""SELECT o.n_shares,o.last_day_computed,o.remainder_wh 
                      FROM generationkwh_remainders o
                        LEFT JOIN generationkwh_remainders b
                            ON o.n_shares=b.n_shares AND o.last_day_computed < b.last_day_computed
                      WHERE b.last_day_computed IS NULL
                      """)
        result = [
            (
                r[0],
                r[1],
                r[2]
            ) for r in cr.fetchall()
        ]
        return result

    def add(self, cr, uid, remainders, context=None):
        for n,pointsDate,remainder in remainders:
            cr.execute("""INSERT INTO generationkwh_remainders 
                          (n_shares,last_day_computed,remainder_wh)
                          VALUES (%d,'%s',%d)""" % (n,pointsDate,remainder))
            
    def clean(self,cr,uid,context=None):
        ids=self.search(cr,uid, [], context=context)
        self.unlink(cr,uid,ids)
        
GenerationkWhRemainders()

"""
class GenerationkWhRightsPerShare(osv.osv):
    _name = 'generationkwh.rightspershare'

    _columns = dict(
        nshares=fields.integer(
            "Number of shares",
            required=True,
            help="Number of shares purchased",
            ),
        date=fields.date(
            "Production Date",
            required=True,
            help="Date at which rights were generated",
            ),
        )
    _columns.update((
        ('kwh_{:02d}'.format(i), fields.integer(
            "Consolidated rigths hour {:02d}",
            required=True,
            help="Consolidated rights for hour {}/25".format(i+1),
        ))
        for i in xrange(25)
        ))

GenerationkWhRightsPerShare()
"""

class GenerationkWhInvestments(osv.osv):

    _name = 'generationkwh.investments'

    _columns = dict(
        member_id=fields.many2one(
            'res.partner',
            'gkwh_investment',
            required=True,
            help="Member who purchased the shares",
            ),
        nshares=fields.integer(
            required=True,
            help="Number of shares purchased",
            ),
        purchase_date=fields.date(
            "Purchase Date",
            required=True,
            help="When the shares where bought",
            ),
        activation_date=fields.date(
            "Activation Date",
            help="When the shares start to provide electricity use rigths",
            ),
        deactivation_date=fields.date(
            "Deactivation Date",
            help="When the shares stop to provide electricity use rights",
            ),
        )

    def active_investments(self, cursor, uid,
            member, start, end,
            context=None):

        provider = InvestmentProvider(self, cursor, uid, context)
        return provider.shareContracts(member, start, end)


    def create_investments_from_accounting(self, cursor, uid,
            start, stop, waitingDays, expirationYears,
            context=None):
        """
            Takes accounting information and generates GenkWh investments
            purchased among start and stop dates.
            If waitingDays is not None, activation date is set those
            days after the purchase date.
            If expirationYears is not None, expiration date is set, those
            years after the activation date.
            TODO: Confirm that the expiration is relative to the activation
            instead the purchase.
        """

        Account = self.pool.get('account.account')
        MoveLine = self.pool.get('account.move.line')
        Partner = self.pool.get('res.partner')

        accountIds = Account.search(cursor, uid, [('code','ilike','163500%')])

        criteria = [('account_id','in',accountIds)]
        if stop: criteria.append(('date_created', '<=', str(stop)))
        if start: criteria.append(('date_created', '>=', str(start)))

        movelinesids = MoveLine.search(
            cursor, uid, criteria,
            order='date_created asc, id asc',
            context=context
            )
        for line in MoveLine.browse(cursor, uid, movelinesids, context):
            partnerid = line.partner_id.id
            if not partnerid:
                # Handle cases with no partner_id
                membercode = int(line.account_id.code[4:])
                partnerid = Partner.search(cursor, uid, [
                    ('ref', 'ilike', '%'+str(membercode).zfill(6))
                    ])[0]
            activation = None
            deactivation = None
            if waitingDays is not None:
                activation = str(
                    isodate(line.date_created)
                    +relativedelta(days=waitingDays))

                if expirationYears is not None:
                    deactivation = str(
                        isodatetime(activation)
                        +relativedelta(years=expirationYears))

            self.create(cursor, uid, dict(
                member_id=partnerid,
                nshares=(line.credit-line.debit)//100,
                purchase_date=line.date_created,
                activation_date=activation,
                deactivation_date=deactivation,
                ))

    def create_investments_from_paymentlines(self, cursor, uid,
            start, stop, waitingDays, expirationYears,
            context=None):
        tail = 0,None,None,context

        criteria = [('name','like','GKWH')]
        if stop: criteria.append(('create_date', '<=', str(stop)))
        if start: criteria.append(('create_date', '>=', str(start)))

        PaymentLine = self.pool.get('payment.line')
        paymentlineids = PaymentLine.search(cursor, uid, criteria,*tail)
        for payment in PaymentLine.browse(cursor, uid, paymentlineids, context):
            activation = None
            deactivation = None
            if waitingDays is not None:
                activation = str(
                    isodatetime(payment.create_date)
                    +relativedelta(days=waitingDays))

                if expirationYears is not None:
                    deactivation = str(
                        isodatetime(activation)
                        +relativedelta(years=expirationYears))

            self.create(cursor, uid, dict(
                member_id=payment.partner_id.id,
                nshares=-payment.amount_currency//100,
                purchase_date=payment.create_date,
                activation_date=activation,
                deactivation_date=deactivation,
                ))

GenerationkWhInvestments()


class GenerationkWhDealer(osv.osv):

    _name = 'generationkwh.dealer'
    _auto = False

    def is_active(self, cursor, uid,
                  contract_id, start_date, end_date,
                  context=None):
        """ Returns True if contract_id has generation kwh activated
            during the period"""
        dealer = self._createDealer(cursor, uid, context)

        return dealer.is_active(
            contract_id, start_date, end_date)

    def get_available_kwh(self, cursor, uid,
                          contract_id, start_date, end_date, fare, period,
                          context=None):
        """ Returns generationkwh [kWh] available for contract_id during the
            date interval, fare and period"""
        dealer = self._createDealer(cursor, uid, context)

        return dealer.get_available_kwh(
            contract_id, start_date, end_date, fare, period)

    def use_kwh(self, cursor, uid,
                contract_ia, start_date, end_date, fare, period, kwh,
                context=None):
        """Marks the indicated kwh as used, if available, for the contract,
           date interval, fare and period and returns the ones efectively used.
        """
        dealer = self._createDealer(cursor, uid, context)
        return dealer.use_kwh(
            contract_id, start_date, end_date, fare, period, kwh)

    def refund_kwh(self, cursor, uid,
                   contract_id, start_date, end_date, fare, period, kwh,
                   partner_id, context=None):
        """Refunds the indicated kwh, marking them as available again, for the
           contract, date interval, fare and period and returns the ones
           efectively used.
        """
        dealer = self._createDealer(cursor, uid, context)

        return dealer.refund_kwh(
            contract_id, start_date, end_date, fare, period, kwh)

    def _createDealer(self, cursor, uid, context):
        # TODO: Feed the dealer with data sources
        investments = InvestmentProvider(self, cursor, uid, context)
        holidays = HolidaysProvider(self, cursor, uid, context)
        return Dealer()


GenerationkWhDealer()


class GenerationkWhInvoiceLineOwner(osv.osv):
    """ Class with the relation between generation invoice line and rights owner
    """

    _name = 'generationkwh.invoice.line.owner'

    def name_get(self, cursor, uid, ids, context=None):
        """GkWH name"""
        res = []
        glo_vals = self.read(cursor, uid, ids, ['factura_line_id'])
        for glo in glo_vals:
            res.append((glo['id'], glo['factura_line_id'][1]))

        return res

    def _ff_invoice_number(self, cursor, uid, ids, field_name, arg,
                           context=None ):
        """Invoice Number"""
        if not ids:
            return []
        res = dict([(i, False) for i in ids])
        f_obj = self.pool.get('giscedata.facturacio.factura')

        glo_vals = self.read(cursor, uid, ids, ['factura_id'])
        inv_ids = [g['factura_id'][0] for g in glo_vals]
        inv_vals = f_obj.read(cursor, uid, inv_ids, ['number'])
        inv_dict = dict([(i['id'], i['number']) for i in inv_vals])
        for glo_val in glo_vals:
            glo_id = glo_val['id']
            glo_number = inv_dict[glo_val['factura_id'][0]]
            res.update({glo_id: glo_number})

        return res

    _columns = {
        'factura_id': fields.many2one(
            'giscedata.facturacio.factura', 'Factura', required=True,
            readonly=True
        ),
        'factura_number': fields.function(
            _ff_invoice_number, string='Num. Factura', method=True, type='char',
            size='64',
        ),
        'factura_line_id': fields.many2one(
            'giscedata.facturacio.factura.linia', 'Línia de factura',
            required=True, readonly=True
        ),
        'owner_id': fields.many2one(
            'res.partner', 'Soci Generation', required=True, readonly=True
        ),
    }

GenerationkWhInvoiceLineOwner()
# vim: ts=4 sw=4 et
