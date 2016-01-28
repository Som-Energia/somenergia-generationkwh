# -*- encoding: utf-8 -*-

class Dealer(object):
    
    def is_active(self,
            contract_id, start_date, end_date):
        """ Returns True if contract_id has generation kwh activated
            during the period"""
        return False

    def get_available_kwh(self, contract_id, start_date, end_date, fare, period):
        """ Returns generationkwh [kWh] available for contract_id during the
            date interval, fare and period"""
        return 40

    def use_kwh(self, contract_id, start_date, end_date, fare, period, kwh):
        """Marks the indicated kwh as used, if available, for the contract,
           date interval, fare and period and returns the ones efectively used.
        """
        return kwh

    def refund_kwh(self, contract_id, start_date, end_date, fare, period, kwh):
        """Refunds the indicated kwh, marking them as available again, for the
           contract, date interval, fare and period and returns the ones
           efectively used.
        """
        pass


