# -*- coding: utf-8 -*-

from .fareperiodcurve import FarePeriodCurve, libfacturacioatr
import unittest
import datetime
from .isodates import isodate
import numpy

class HolidaysProvidersMockup(object):
    def get(self, start, stop):
        return self.holidays

    def set(self, holidays):
        self.holidays= [isodate(holiday) for holiday in holidays]

    def __init__(self, holidays=[]):
        self.set(holidays)

@unittest.skipIf(libfacturacioatr is None,
    'non-free libfacturacioatr module is not installed' )

class LibFacturacioAtr_Factory_Test(unittest.TestCase):
    def test_get_class_by_code(self):
        import libfacturacioatr.tarifes as tarifes
        for code, clss in [
            ('2.0A', tarifes.Tarifa20A),
            ('3.0A', tarifes.Tarifa30A),
            ('3.1A', tarifes.Tarifa31A),
            ('2.0DHA', tarifes.Tarifa20DHA),
            ]:
            self.assertEqual(
                tarifes.Tarifa.get_class_by_code(code), clss)

        with self.assertRaises(KeyError):
            tarifes.Tarifa.get_class_by_code("Bad")

    def test_get_class_by_code_fromPool(self):
        import libfacturacioatr.pool.tarifes as tarifespool
        for code, clss in [
            ('2.0A', tarifespool.Tarifa20APool),
            ('3.0A', tarifespool.Tarifa30APool),
            ('3.1A', tarifespool.Tarifa31APool),
            ('2.0DHA', tarifespool.Tarifa20DHAPool),
            ]:
            self.assertEqual(
                tarifespool.TarifaPool.get_class_by_code(code), clss)

        with self.assertRaises(KeyError):
            tarifespool.TarifaPool.get_class_by_code("Bad")

@unittest.skipIf(libfacturacioatr is None,
    'non-free libfacturacioatr module is not installed' )

class FarePeriodCurve_Test(unittest.TestCase):

    def setupCurve(self,start_date,end_date,fare,period,holidays=[]):
        self.maxDiff = None
        p = FarePeriodCurve(
            holidays=HolidaysProvidersMockup(holidays)
            )
        return p.periodMask(fare, period, isodate(start_date), isodate(end_date))

    def assertArrayEqual(self, result, expected):
        result = list(result)
        result = [result[i:i+25] for i in xrange(0,len(result),25)]
        expected = [expected[i:i+25] for i in xrange(0,len(expected),25)]
        return self.assertEqual(result, expected)

    def test_20A_singleMonth(self):
        p = FarePeriodCurve(holidays=HolidaysProvidersMockup())

        mask = self.setupCurve('2015-12-01', '2015-12-31', '2.0A', 'P1')

        self.assertArrayEqual(mask,
            + 31 * ( [1]*24+[0] )
            )

    def test_20DHA_singleMonth_summer(self):
        p = FarePeriodCurve(holidays=HolidaysProvidersMockup())

        mask = self.setupCurve('2015-08-01', '2015-08-31', '2.0DHA', 'P2')

        self.assertArrayEqual(mask,
            + 31 * ( [1]*13+[0]*10+[1,0] )
            )

    def test_20DHA_singleMonth_winter(self):
        p = FarePeriodCurve(holidays=HolidaysProvidersMockup())

        mask = self.setupCurve('2015-12-01', '2015-12-31', '2.0DHA', 'P2')

        self.assertArrayEqual(mask,
            + 31 * ( [1]*12+[0]*10+[1,1,0] )
            )

    def test_20DHA_singleMonth_summerToWinter(self):
        p = FarePeriodCurve(holidays=HolidaysProvidersMockup())

        mask = self.setupCurve('2016-10-01', '2016-10-31', '2.0DHA', 'P2')

        self.assertArrayEqual(mask,
            + 29 * ( [1]*13+[0]*10+[1,0] )
            +  1 * ( [1]*13+[0]*10+[1,1] )
            +  1 * ( [1]*12+[0]*10+[1,1,0] )
            )

    def test_20DHA_singleMonth_winterToSummer(self):
        p = FarePeriodCurve(holidays=HolidaysProvidersMockup())

        mask = self.setupCurve('2016-03-01', '2016-03-31', '2.0DHA', 'P2')

        self.assertArrayEqual(mask,
            + 26 * ( [1]*12+[0]*10+[1,1,0] )
            +  1 * ( [1]*12+[0]*10+[1,0,0] )
            +  4 * ( [1]*13+[0]*10+[1,0] )
            )

    def test_31A_P1_singleMonth(self):
        p = FarePeriodCurve(holidays=HolidaysProvidersMockup())

        mask = self.setupCurve('2015-12-01', '2015-12-31', '3.1A', 'P1')

        self.assertArrayEqual(mask,
            + 4 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 )
            )

    def test_31A_P3_singleMonth(self):
        p = FarePeriodCurve(holidays=HolidaysProvidersMockup())

        mask = self.setupCurve('2015-12-01', '2015-12-31', '3.1A', 'P3')

        self.assertArrayEqual(mask,
            + 4 * ( [1]*8 + [0]*17 )
            + 2 * ( [1]*18 + [0]*7 )
            + 5 * ( [1]*8 + [0]*17 )
            + 2 * ( [1]*18 + [0]*7 )
            + 5 * ( [1]*8 + [0]*17 )
            + 2 * ( [1]*18 + [0]*7 )
            + 5 * ( [1]*8 + [0]*17 )
            + 2 * ( [1]*18 + [0]*7 )
            + 4 * ( [1]*8 + [0]*17 )
            )

    def test_31A_P1_singleMonth_withHolidays(self):
        holidays = HolidaysProvidersMockup([
            '2015-12-25',
        ])
        p = FarePeriodCurve(holidays=
            holidays
        )

        mask =self.setupCurve('2015-12-01', '2015-12-31', '3.1A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 4 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 ) # Christmasts
            + 3 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 )
            )

    def test_30A_P1_singleMonth_withHolidays_asWorkingP1AndP4Aggregated(self):
        holidays = HolidaysProvidersMockup([
            '2015-12-25',
        ])
        p = FarePeriodCurve(holidays=
            holidays
        )

        mask =self.setupCurve('2015-12-01', '2015-12-31', '3.0A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 6 * ( [0]*18 + [1]*4+ [0]*3 )
            + 7 * ( [0]*18 + [1]*4+ [0]*3 )
            + 7 * ( [0]*18 + [1]*4+ [0]*3 )
            + 7 * ( [0]*18 + [1]*4+ [0]*3 ) # Christmasts
            + 4 * ( [0]*18 + [1]*4+ [0]*3 )
            )

    def test_31A_P1_startedMonth(self):
        holidays = HolidaysProvidersMockup([
            '2015-12-25',
        ])
        p = FarePeriodCurve(holidays=
            holidays,
        )

        mask = self.setupCurve('2015-12-7', '2015-12-31', '3.1A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 ) # Christmasts
            + 3 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 )
            )

    def test_31A_P1_partialMonth(self):
        mask = self.setupCurve('2015-12-7', '2015-12-27', '3.1A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 ) # Christmasts
            + 3 * ( [0]*25 )
            )

    def test_31A_P1_singleDay(self):
        mask = self.setupCurve('2015-12-25', '2015-12-25', '3.1A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 1 * ( [0]*25 )
            )

    def test_31A_P1_accrossMonths(self):

        mask = self.setupCurve('2015-11-25', '2015-12-25', '3.1A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 3 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 ) # Christmasts
            + 1 * ( [0]*25 )
            )

# vim: ts=4 sw=4 et
