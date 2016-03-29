# -*- encoding: utf-8 -*-

class Dealer(object):
    """ It deals investors Generation kWh use rights to contracts according its
        availability and investors criteria.
    """

    def __init__(self, usageTracker):
        self._usageTracker = usageTracker
    
    def is_active(self,
            contract_id, start_date, end_date):
        """ Returns True if contract_id has generation kwh activated
            during the period"""
        if contract_id == 4:
            return True
        return False

    # Do not use for invoicing, ONLY statistics
    def get_available_kwh(self, contract_id, start_date, end_date, fare, period):
        """ Returns generationkwh [kWh] available for contract_id during the
            date interval, fare and period"""
        return 40

    def use_kwh(self, contract_id, start_date, end_date, fare, period, kwh):
        """Marks the indicated kwh as used, if available, for the contract,
           date interval, fare and period and returns the ones efectively used.
        """
        return [
            {'member_id': 13, 'kwh': int(round(kwh / 2))},
            {'member_id': 42, 'kwh': int(round(kwh / 4))}
        ]

    def refund_kwh(self, contract_id, start_date, end_date, fare, period, kwh,
                   partner_id):
        """Refunds the indicated kwh, marking them as available again, for the
           contract, date interval, fare and period and returns the ones
           efectively used.
        """
        pass


# vim: ts=4 sw=4 et
