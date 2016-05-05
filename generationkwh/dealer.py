# -*- encoding: utf-8 -*-

from dateutil.relativedelta import relativedelta
import datetime

class DummyDealer(object):

    """ It deals investors Generation kWh use rights to contracts according its
        availability and investors criteria.
    """

    def __init__(self, usageTracker, assignmentProvider):
        self._usageTracker = usageTracker
        self._assignments = assignmentProvider
    
    def is_active(self,
            contract_id, start_date, end_date):
        """ Returns True if contract_id has generation kwh activated
            during the period"""
        if contract_id == 2:
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
           efectively refund.
        """
        pass


class Dealer(object):
    """ It deals investors Generation kWh use rights to contracts according its
        availability and investors criteria.
    """

    def __init__(self, usageTracker, assignmentProvider):
        self._tracker = usageTracker
        self._assignments = assignmentProvider

    
    def is_active(self,
            contract_id, start_date, end_date):
        """ Returns True if contract_id has generation kwh activated
            during the period"""
        raise NotImplemented
        if contract_id == 4:
            return True
        return False

    # Do not use for invoicing, ONLY statistics
    def get_available_kwh(self, contract_id, start_date, end_date, fare, period):
        """ Returns generationkwh [kWh] available for contract_id during the
            date interval, fare and period"""
        raise NotImplemented

    def use_kwh(self, contract_id, start_date, end_date, fare, period, kwh):
        """
            Marks the indicated kwh as used, if available, for the contract,
            date interval, fare and period.
            Returns a list of dictionaries each with member_id and kwh
            effectively allocated.
        """
        assert type(start_date) == datetime.date
        assert type(end_date) == datetime.date
        seek_start = start_date + relativedelta(years=-1)
        assignments = self._assignments.seek(contract_id)
        used = 0
        result = []
        for asig in assignments:
            seek_end = min(end_date,asig.last_usable_date)
            if seek_end<seek_start: continue
            memberUse = self._tracker.use_kwh(
                    asig.member_id,
                    seek_start,
                    seek_end,
                    fare, period, kwh - used)
            result.append(dict(member_id=asig.member_id, kwh=int(memberUse)))
            used += memberUse
        return result

    def refund_kwh(self, contract_id, start_date, end_date, fare, period, kwh,
            member_id):
        """
            Refunds the indicated kwh, marking them as available again,
            for the contract, date interval, fare and period and
            returns the kwh efectively refunded.
        """
        assert type(start_date) == datetime.date
        assert type(end_date) == datetime.date
        seek_start = start_date + relativedelta(years=-1)
        return self._tracker.refund_kwh(member_id,
            seek_start, end_date,
            fare, period, kwh)


# vim: ts=4 sw=4 et
