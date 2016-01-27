# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields


class GenerationkWhDealer(osv.osv):

    _name = 'generationkwh.dealer'
    _auto = False

    def is_active(self, cursor, uid, contract_id, start_date, end_date,
                  context=None):
        """ Returns True if contract_id has generation kwh activated
            during the period"""
        return False

    def get_available_kwh(self, cursor, uid, contract_id, start_date, end_date,
                          fare, period, context=None):
        """ Returns generationkwh [kWh] available for contract_id during the
            date interval, fare and period"""
        return 40

    def use_kwh(self, cursor, uid, contract_id, start_date, end_date, fare,
                period, kwh, context=None):
        """Marks the indicated kwh as used, if available, for the contract,
           date interval, fare and period and returns the ones efectively used.
        """
        return kwh

    def refund_kwh(self, cursor, uid, contract_id, start_date, end_date, fare,
                   period, kwh, context=None):
        """Refunds the indicated kwh, marking them as available again, for the
           contract, date interval, fare and period and returns the ones
           efectively used.
        """

GenerationkWhDealer()

# vim: ts=4 sw=4 tw=79 cc=+1 et
