# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta


class AssignmentSeeker(object):
    def __init__(self, usageTracker=None, assignmentProvider=None):
        self._usage = usageTracker
        self._assignments = assignmentProvider

    def use_kwh(self, contract_id, start_date, end_date, fare, period, kwh):
        """
            Marks the indicated kwh as used, if available, for the contract,
            date interval, fare and period.
            Returns a list of dictionaries each with member_id and kwh
            effectively allocated.
        """
        seek_start = start_date + relativedelta(years=-1)
        assignments = self._assignments.seek(contract_id)
        used = 0
        result = []
        for asig in assignments:
            seek_end = min(end_date,asig.last_usable_date)
            if seek_end<seek_start: continue
            memberUse = self._usage.use_kwh(
                    asig.member_id,
                    seek_start,
                    seek_end,
                    fare, period, kwh - used)
            result.append(dict(member_id=asig.member_id, kwh=memberUse))
            used += memberUse
        return result

    def refund_kwh(self, contract_id, start_date, end_date, fare, period, kwh,
                   partner_id):
        """
            Refunds the indicated kwh, marking them as available again,
            for the contract, date interval, fare and period and
            returns the kwh efectively refunded.
        """



# vim: ts=4 sw=4 et
