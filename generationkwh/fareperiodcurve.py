# -*- coding: utf-8 -*-

"""
TODO:
- Use numpy arrays
- Date parameter should be dates not strings
"""

import datetime
from dateutil.relativedelta import relativedelta
import numpy
try:
    import libfacturacioatr
except ImportError:
    libfacturacioatr = None

FIRST_DATE_TD_FARES = datetime.date(2021,6,1)
LAST_DATE_TRANSLATED_INTERVAL = FIRST_DATE_TD_FARES + relativedelta(years=1) - relativedelta(days=1)

class FarePeriodCurve(object):

    def __init__(self, holidays):
        self.holidays = holidays

    def equivalentIntervalsForTDFares(self, start, end):
        if start >= FIRST_DATE_TD_FARES:
            return [(start, end)]

        elif end < FIRST_DATE_TD_FARES:
            return [(start + relativedelta(years=+1), end + relativedelta(years=+1))]

        translated_start = start + relativedelta(years=+1)
        return [(translated_start, LAST_DATE_TRANSLATED_INTERVAL), (FIRST_DATE_TD_FARES, end)]

    def periodMaskConsideringOldAndTDFares(self, start, end, fare, period):

        if 'TD' in fare:
            period_dates = self.equivalentIntervalsForTDFares(start, end)
            mask = []
            for range_start, range_end in period_dates:
                mask += self._mask(range_start, range_end, fare, period)
            return mask
        else:
            return self._mask(start, end, fare, period)

    def _mask(self, begin_date, end_date, fare, period):
        import libfacturacioatr
        begin = begin_date
        end = end_date
        assert type(begin) == datetime.date
        assert type(end) == datetime.date
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
            t.get_period_component_aggregated(
                datetime.date(month//12, month%12+1, 1),
                period,
                holidays=self.holidays.get(begin,end)
                ).matrix
            for month in xrange(startMonth, endMonth+1)], [])
        return allDays[begin.day-1:] [:(end-begin).days+1]

    def periodMask(self, fare, period, begin_date, end_date):
        return numpy.array(sum(
            self.periodMaskConsideringOldAndTDFares(begin_date, end_date, fare, period),[]))


# vim: ts=4 sw=4 et
