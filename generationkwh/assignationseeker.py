# -*- coding: utf-8 -*-


class AssignationSeeker(object):
    def __init__(self, usagetracker=None, assinationProvider=None):
        self._usage = usagetracker
        self._assignations = assinationProvider

    def use_kwh(self, contract_id, start_date, end_date, fare, period, kwh):
        assignations = self._assignations.seek(contract_id)
        if assignations:
            asig = assignations[0]
            self._usage.use_kwh( asig.member_id,
                    '2014-08-01 00:00:00+02:00',
                    end_date,
                    fare, period, kwh)
            return 20
        return 0




# vim: ts=4 sw=4 et
