# -*- encoding: utf-8 -*-

from dateutil.relativedelta import relativedelta
import datetime
from .isodates import assertDateOrNone, assertDate

class Dealer(object):
    """ It deals investors Generation kWh use rights to contracts according its
        availability and investors criteria.
    """

    def __init__(self, usageTracker, assignmentProvider, investments=None):
        self._tracker = usageTracker
        self._assignments = assignmentProvider
        self._investments = investments

    
    def is_active(self,
            contract_id, first_date, last_date):
        """ Returns True if contract_id has generation kwh activated
            during the period"""
        assertDateOrNone('first_date', first_date)
        assertDateOrNone('last_date', last_date)
        if not self._assignments.anyForContract(contract_id):
            return False

        for assigment in self._assignments.contractSources(contract_id):
            if self._investments.effectiveForMember(
                    assigment.member_id, first_date, last_date):
                return True
        return False

    # Do not use for invoicing, ONLY statistics
    def get_available_kwh(self, contract_id, first_date, last_date, fare, period):
        """ Returns generationkwh [kWh] available for contract_id during the
            date interval, fare and period"""
        raise NotImplemented

    def use_kwh(self, contract_id, first_date, last_date, fare, period, kwh):
        """
            Marks the indicated kwh as used, if available, for the contract,
            date interval, fare and period.
            Returns a list of dictionaries each with member_id and kwh
            effectively allocated.
        """
        assertDate('first_date', first_date)
        assertDate('last_date', last_date)
        assert kwh>=0, ("Negative use not allowed")
        seek_start = first_date + relativedelta(years=-1)
        assignments = self._assignments.contractSources(contract_id)
        used = 0
        result = []
        for asig in assignments:
            seek_end = min(last_date,asig.last_usable_date)
            if seek_end<seek_start: continue
            memberUse, usage = self._tracker.use_kwh_with_dates_dict(
                    asig.member_id,
                    seek_start,
                    seek_end,
                    fare, period, kwh - used,
                    )
            assert memberUse >= 0, (
                "Genkwh Usage traker returned negative use ({}) for member {}"
                .format(memberUse, asig.member_id))
            assert memberUse <= kwh - used, (
                "Genkwh Usage traker returned more ({}) than required (10) for member member1"
                .format( memberUse, kwh-used, asig.member_id ))

            result.append(dict(member_id=asig.member_id, kwh=int(memberUse), usage=usage))
            used += memberUse

        return result

    def refund_kwh(self, contract_id, first_date, last_date, fare, period, kwh,
            member_id):
        """
            Refunds the indicated kwh, marking them as available again,
            for the contract, date interval, fare and period and
            returns the kwh efectively refunded.
        """
        assert type(first_date) == datetime.date
        assert type(last_date) == datetime.date
        seek_start = first_date + relativedelta(years=-1)
        memberUse, unusage =  self._tracker.refund_kwh_with_dates_dict(member_id,
            seek_start, last_date,
            fare, period, kwh)

        return dict(member_id=member_id, kwh=int(memberUse), unusage=unusage)

# vim: ts=4 sw=4 et
