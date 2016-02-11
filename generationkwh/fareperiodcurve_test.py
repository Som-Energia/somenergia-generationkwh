# -*- coding: utf-8 -*-

from fareperiodcurve import FarePeriodCurve, libfacturacioatr, isodate
import unittest

@unittest.skipIf(libfacturacioatr is None,
    'non-free libfacturacioatr module is not installed' )

class FarePeriodCurve_Test(unittest.TestCase):

    def assertArrayEqual(self, result, expected):
        # TODO: Change this as we turn it into a numpy array
        return self.assertEqual(list(result), expected)

    def test_20A_singleMonth(self):
        p = FarePeriodCurve()

        mask = p.mask('2015-12-01', '2015-12-31', '2.0A', 'P1')

        self.assertArrayEqual(mask, 
            + 31 * [ [1]*24+[0] ]
            )

    def test_30A_P1_singleMonth(self):
        p = FarePeriodCurve()

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
        p = FarePeriodCurve()

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
        p = FarePeriodCurve(holidays=[
            isodate('2015-12-25'),
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
        p = FarePeriodCurve(holidays=[
            isodate('2015-12-25'),
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
        p = FarePeriodCurve(holidays=[
            isodate('2015-12-25'),
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
        p = FarePeriodCurve(holidays=[
            isodate('2015-12-25'),
        ])

        mask = p.mask('2015-12-25', '2015-12-25', '3.0A', 'P1')

        self.assertArrayEqual(mask,
            + 1 * [ [0]*25 ]
            )

    def test_30A_P1_accrossMonths(self):
        p = FarePeriodCurve(holidays=[
            isodate('2015-12-25'),
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
