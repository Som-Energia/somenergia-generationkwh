# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields

from generationkwh.dealer import Dealer


class GenerationkWhDealer(osv.osv):

    _name = 'generationkwh.dealer'
    _auto = False


    def _createDealer(self, cursor, uid):
        # TODO: Feed the dealer with data sources
        return Dealer()


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

GenerationkWhDealer()



# vim: ts=4 sw=4 et
