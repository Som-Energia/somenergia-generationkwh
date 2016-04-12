# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta


class AssignationSeeker(object):
    def __init__(self, usagetracker=None, assinationProvider=None):
        self._usage = usagetracker
        self._assignations = assinationProvider

    def use_kwh(self, contract_id, start_date, end_date, fare, period, kwh):
        seek_start = start_date + relativedelta(years=-1)
        assignations = self._assignations.seek(contract_id)
        if assignations:
            asig = assignations[0]
            seek_end = min(end_date,asig.last_usable_date)
            if seek_end<seek_start: return 0
            return self._usage.use_kwh( asig.member_id,
                    seek_start,
                    seek_end,
                    fare, period, kwh)
        return 0




# vim: ts=4 sw=4 et
