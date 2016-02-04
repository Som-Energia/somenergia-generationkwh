# -*- coding: utf-8 -*-

"""
TODO:
- Fares dictionary should be at libfacturacioatr
- Extend fare selection to all fares
- Use numpy arrays
- Where to get holidays?
- Date parameter should be dates not strings
"""

import numpy
try:
    import libfacturacioatr
except ImportError:
    libfacturacioatr = None

import datetime

def date(string):
    return datetime.datetime.strptime(string, '%Y-%m-%d').date()

class FarePeriodProvider(object):
    def __init__(self, holidays=[]):
        self.holidays = holidays

    def mask(self, begin_date, end_date, fare, period):
        import libfacturacioatr
        begin = date(begin_date)
        end = date(end_date)
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
        allDays = allDays[begin.day-1:]
        return allDays[:(end-begin).days+1]


import unittest

@unittest.skipIf(libfacturacioatr is None,
    'non-free libfacturacioatr module is not installed' )

class FarePeriodProvider_Test(unittest.TestCase):

    def assertArrayEqual(self, expected, result):
        # TODO: Change this as we turn it into a numpy array
        return self.assertEqual(expected, result)

    def test_20A_singleMonth(self):
        p = FarePeriodProvider()

        mask = p.mask('2015-12-01', '2015-12-31', '2.0A', 'P1')

        self.assertArrayEqual(mask, 
            + 31 * [ [1]*24+[0] ]
            )

    def test_30A_P1_singleMonth(self):
        p = FarePeriodProvider()

        mask = p.mask('2015-12-01', '2015-12-31', '3.0A', 'P1')

        self.assertArrayEqual(mask,
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ]
            )

    def test_30A_P3_singleMonth(self):
        p = FarePeriodProvider()

        mask = p.mask('2015-12-01', '2015-12-31', '3.0A', 'P3')

        self.assertArrayEqual(mask,
            + 4 * [ [1]*8 + [0]*17 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [1]*8 + [0]*17 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [1]*8 + [0]*17 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [1]*8 + [0]*17 ]
            + 2 * [ [0]*25 ]
            + 4 * [ [1]*8 + [0]*17 ]
            )

    def test_30A_P1_singleMonth_withHolidays(self):
        p = FarePeriodProvider(holidays=[
            date('2015-12-25'),
        ])

        mask = p.mask('2015-12-01', '2015-12-31', '3.0A', 'P1')

        self.assertArrayEqual(mask,
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ] # Christmasts
            + 3 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ]
            )

    def test_30A_P1_startedMonth(self):
        p = FarePeriodProvider(holidays=[
            date('2015-12-25'),
        ])

        mask = p.mask('2015-12-7', '2015-12-31', '3.0A', 'P1')

        self.assertArrayEqual(mask,
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ] # Christmasts
            + 3 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ]
            )

    def test_30A_P1_partialMonth(self):
        p = FarePeriodProvider(holidays=[
            date('2015-12-25'),
        ])

        mask = p.mask('2015-12-7', '2015-12-27', '3.0A', 'P1')

        self.assertArrayEqual(mask,
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ] # Christmasts
            + 3 * [ [0]*25 ]
            )

    def test_30A_P1_singleDay(self):
        p = FarePeriodProvider(holidays=[
            date('2015-12-25'),
        ])

        mask = p.mask('2015-12-25', '2015-12-25', '3.0A', 'P1')

        self.assertArrayEqual(mask,
            + 1 * [ [0]*25 ]
            )

    def test_30A_P1_accrossMonths(self):
        p = FarePeriodProvider(holidays=[
            date('2015-12-25'),
        ])

        mask = p.mask('2015-11-25', '2015-12-25', '3.0A', 'P1')

        self.assertArrayEqual(mask,
            + 3 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ] # Christmasts
            + 1 * [ [0]*25 ]
            )

# vim: ts=4 sw=4 et
