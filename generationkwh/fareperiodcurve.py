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
import numpy
try:
    import libfacturacioatr
except ImportError:
    libfacturacioatr = None


class FarePeriodCurve(object):
    def __init__(self, holidays):
        self.holidays = holidays

    def mask(self, begin_date, end_date, fare, period):
        import libfacturacioatr
        begin = begin_date
        end = end_date
        Tarifa = libfacturacioatr.tarifes.Tarifa.get_class_by_code(fare)
        t = Tarifa({},{},
            '1970-01-01',
            '1970-01-01',
            data_inici_periode='1970-01-01',
            data_final_periode='1970-01-01',
            )
        startMonth = begin.year*12 + begin.month-1
        endMonth = end.year*12 + end.month-1
        allDays = sum([
            t.get_period_component(
                datetime.date(month//12, month%12+1, 1),
                period,
                holidays=self.holidays.get(begin,end)
                ).matrix
            for month in xrange(startMonth, endMonth+1)], [])
        return allDays[begin.day-1:] [:(end-begin).days+1]

    def periodMask(self, fare, period, begin_date, end_date):
        return numpy.array(sum(self.mask(begin_date, end_date, fare, period),[]))


# vim: ts=4 sw=4 et
