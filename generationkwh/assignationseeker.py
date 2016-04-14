# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta


class AssignationSeeker(object):
    def __init__(self, usagetracker=None, assignationProvider=None):
        self._usage = usagetracker
        self._assignations = assignationProvider

    def use_kwh(self, contract_id, start_date, end_date, fare, period, kwh):
        seek_start = start_date + relativedelta(years=-1)
        assignations = self._assignations.seek(contract_id)
        used = 0
        for asig in assignations:
            seek_end = min(end_date,asig.last_usable_date)
            if seek_end<seek_start: continue
            used += self._usage.use_kwh(
                    asig.member_id,
                    seek_start,
                    seek_end,
                    fare, period, kwh - used)
        return used




# vim: ts=4 sw=4 et
