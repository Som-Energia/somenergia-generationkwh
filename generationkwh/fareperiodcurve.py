# -*- coding: utf-8 -*-

"""
TODO:
- Fares dictionary should be at libfacturacioatr
- Include all fares
- Use numpy arrays
- Where to get holidays?
- Date parameter should be dates not strings
"""

import datetime
try:
    import libfacturacioatr
except ImportError:
    libfacturacioatr = None


def isodate(string):
    return datetime.datetime.strptime(string, '%Y-%m-%d').date()

class FarePeriodCurve(object):
    def __init__(self, holidays=[]):
        self.holidays = holidays

    def mask(self, begin_date, end_date, fare, period):
        import libfacturacioatr
        begin = isodate(begin_date)
        end = isodate(end_date)
        fares = {
            '2.0A': libfacturacioatr.tarifes.Tarifa20A,
            '3.0A': libfacturacioatr.tarifes.Tarifa30A,
        }
        t = fares[fare]({},{},
            begin,
            end,
            data_inici_periode=begin,
            data_final_periode=end,
            )
        startMonth = begin.year*12 + begin.month-1
        endMonth = end.year*12 + end.month-1
        allDays = sum([
            t.get_period_component(
                datetime.date(month//12, month%12+1, 1),
                period,
                holidays=self.holidays
                ).matrix
            for month in xrange(startMonth, endMonth+1)], [])
        return allDays[begin.day-1:][:(end-begin).days+1]


# vim: ts=4 sw=4 et
