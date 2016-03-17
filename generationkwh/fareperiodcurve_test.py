# -*- coding: utf-8 -*-

from fareperiodcurve import FarePeriodCurve, libfacturacioatr, isodate
import unittest

class HolidaysProvidersMockup(object):
    def get(self, start, stop):
        return self.holidays

    def set(self, holidays):
        self.holidays= [isodate(holiday) for holiday in holidays]

    def __init__(self, holidays=[]):
        self.set(holidays)

@unittest.skipIf(libfacturacioatr is None,
    'non-free libfacturacioatr module is not installed' )

class FarePeriodCurve_Test(unittest.TestCase):
    def setupCurve(self,start_date,end_date,fare,period,holidays=[]):
        
        p = FarePeriodCurve(
            holidays=HolidaysProvidersMockup(holidays)
            )

        return p.mask(start_date, end_date, fare, period)

        
    def assertArrayEqual(self, result, expected):
        # TODO: Change this as we turn it into a numpy array
        return self.assertEqual(list(result), expected)

    def test_20A_singleMonth(self):
        p = FarePeriodCurve(holidays=HolidaysProvidersMockup())

        mask = self.setupCurve('2015-12-01', '2015-12-31', '2.0A', 'P1')

        self.assertArrayEqual(mask, 
            + 31 * [ [1]*24+[0] ]
            )

    def test_30A_P1_singleMonth(self):
        p = FarePeriodCurve(holidays=HolidaysProvidersMockup())

        mask = self.setupCurve('2015-12-01', '2015-12-31', '3.0A', 'P1')

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
        p = FarePeriodCurve(holidays=HolidaysProvidersMockup())

        mask = self.setupCurve('2015-12-01', '2015-12-31', '3.0A', 'P3')

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
        holidays = HolidaysProvidersMockup([
            '2015-12-25',
        ])
        p = FarePeriodCurve(holidays=
            holidays
        )

        mask =self.setupCurve('2015-12-01', '2015-12-31', '3.0A', 'P1', ['2015-12-25'])

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
        holidays = HolidaysProvidersMockup([
            '2015-12-25',
        ])
        p = FarePeriodCurve(holidays=
            holidays,
        )

        mask = self.setupCurve('2015-12-7', '2015-12-31', '3.0A', 'P1', ['2015-12-25'])

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
        mask = self.setupCurve('2015-12-7', '2015-12-27', '3.0A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 5 * [ [0]*18 + [1]*4+ [0]*3 ]
            + 2 * [ [0]*25 ]
            + 4 * [ [0]*18 + [1]*4+ [0]*3 ] # Christmasts
            + 3 * [ [0]*25 ]
            )

    def test_30A_P1_singleDay(self):
        mask = self.setupCurve('2015-12-25', '2015-12-25', '3.0A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 1 * [ [0]*25 ]
            )

    def test_30A_P1_accrossMonths(self):

        mask = self.setupCurve('2015-11-25', '2015-12-25', '3.0A', 'P1', ['2015-12-25'])

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
