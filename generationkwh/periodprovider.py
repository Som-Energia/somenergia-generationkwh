import numpy
try:
    import libfacturacioatr
except ImportError:
    libfacturacioatr = None


def date(string):
    from datetime import datetime
    return datetime.strptime(string, '%Y-%m-%d').date()

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
        return t.get_period_component(begin, period, holidays=self.holidays).matrix


import unittest

@unittest.skipIf(libfacturacioatr is not None,
    'non-free libfacturacioatr module is not installed' )
class FarePeriodProvider_Test(unittest.TestCase):

    def assertArrayEqual(self, expected, result):
        # TODO: Change this as we turn it into a numpy array
        return self.assertEqual(expected, result)

    def test_20A_singleMonth(self):
        p = FarePeriodProvider()

        mask = p.mask('2015-12-01', '2015-12-31', '2.0A', 'P1')

        self.assertArrayEqual(mask, [ [1]*24+[0] ]*31)

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

    def test_30A_P1_singleDay(self):
        p = FarePeriodProvider(holidays=[
            date('2015-12-25'),
        ])

        mask = p.mask('2015-12-10', '2015-12-10', '3.0A', 'P1')

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


