# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields

from generationkwh.dealer import Dealer

def isodatetime(string):
    import datetime
    return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
def isodate(date):
    import datetime
    return date and datetime.datetime.strptime(date, '%Y-%m-%d')

from dateutil.relativedelta import relativedelta


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

        criteria = [('name','like','GKWH')]
        if stop: criteria.append(('create_date', '<=', str(stop)))
        if start: criteria.append(('create_date', '>=', str(start)))

        PaymentLine = self.pool.get('payment.line')
        paymentlineids = PaymentLine.search(cursor, uid, criteria, 0,0,False, context)
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


class InvestmentProvider():
    def __init__(self, erp, cursor, uid, context=None):
        self.erp = erp
        self.cursor = cursor
        self.uid = uid
        self.context = context

    def shareContracts(self, member=None, start=None, end=None):
        filters = []
        if member: filters.append( ('member_id','=',member) )
        if end: filters += [
            ('activation_date','<=',end),
            ('activation_date','!=',False),
            ]
        if start: filters += [
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
            for c in contracts
        ]


class GenerationkWhDealer(osv.osv):

    _name = 'generationkwh.dealer'
    _auto = False

    def is_active(self, cursor, uid,
                  contract_id, start_date, end_date,
                  context=None):
        """ Returns True if contract_id has generation kwh activated
            during the period"""
        dealer = self._createDealer(cursor, uid)

        return dealer.is_active(
            contract_id, start_date, end_date)

    def get_available_kwh(self, cursor, uid,
                          contract_id, start_date, end_date, fare, period,
                          context=None):
        """ Returns generationkwh [kWh] available for contract_id during the
            date interval, fare and period"""
        dealer = self._createDealer(cursor, uid)

        return dealer.get_available_kwh(
            contract_id, start_date, end_date, fare, period)

    def use_kwh(self, cursor, uid,
                contract_ia, start_date, end_date, fare, period, kwh,
                context=None):
        """Marks the indicated kwh as used, if available, for the contract,
           date interval, fare and period and returns the ones efectively used.
        """
        dealer = self._createDealer(cursor, uid)
        return dealer.use_kwh(
            contract_id, start_date, end_date, fare, period, kwh)

    def refund_kwh(self, cursor, uid,
                   contract_id, start_date, end_date, fare, period, kwh,
                   context=None):
        """Refunds the indicated kwh, marking them as available again, for the
           contract, date interval, fare and period and returns the ones
           efectively used.
        """
        dealer = self._createDealer(cursor, uid)

        return dealer.refund_kwh(
            contract_id, start_date, end_date, fare, period, kwh)

    def _createDealer(self, cursor, uid):
        # TODO: Feed the dealer with data sources
        return Dealer()


GenerationkWhDealer()

# vim: ts=4 sw=4 et
