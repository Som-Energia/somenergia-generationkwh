# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields

from generationkwh.dealer import Dealer


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

    def boo(self, cursor, uid, context=None):
        return "Hola"

    def getList(self, cursor, uid, member=None, start=None, end=None,
            context=None):
        provider = InvestmentProvider(self, cursor, uid, context)
        return provider.shareContracts(member, start, end)
        

GenerationkWhInvestments()

class InvestmentProvider():
    def __init__(self, erp, cursor, uid, context=None):
        self.erp = erp
        self.cursor = cursor
        self.uid = uid
        self.context = context

    def shareContracts(self, member=None, start=None, end=None):
        def isodate(date):
            import datetime
            return datetime.datetime.strptime(date, '%Y-%m-%d').date()

        filters = []
        if member: filters.append( ('member','==',member) )
        if start: filters.append( ('deactivation_date','>=',start) )
        if end: filters.append( ('activation_date','>=',end) )

        contracts = self.erp.search(
            self.cursor, self.uid,
            'generationkwh.investments', filters)

        return [
            (
                c['member'],
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
