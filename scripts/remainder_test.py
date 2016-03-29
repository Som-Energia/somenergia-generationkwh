# -*- coding: utf-8 -*-
import unittest
import datetime
dbconfig = None
try:
    import dbconfig
    import erppeek
except ImportError:
    pass

def isodate(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()

@unittest.skipIf(not dbconfig, "depends on ERP")
class Remainder_Test(unittest.TestCase):

    def setUp(self):
        erp = erppeek.Client(**dbconfig.erppeek)
        self.Remainders = erp.GenerationkwhRemainders
        self.Remainders.clean()

    def setupProvider(self,remainders=[]):
        self.Remainders.add(remainders)

    def assertRemaindersEqual(self, expectation):
        result = self.Remainders.last()
        self.assertEqual(result, [list(a) for a in expectation])

    def tearDown(self):
        self.Remainders.clean()

    def test_no_remainders(self):
        remainders=self.setupProvider()
        self.assertRemaindersEqual([])

    def test_one_remainder(self):
        remainders=self.setupProvider([
            [1,'2016-02-25',3]
            ])
        self.assertRemaindersEqual([
            [1,'2016-02-25',3]
            ])

    def test_two_remainder(self):
        remainders=self.setupProvider([
            [1,'2016-02-25',3],
            [2,'2016-02-25',1]
            ])
        self.assertRemaindersEqual([
            [1,'2016-02-25',3],
            [2,'2016-02-25',1]
            ])

    def test_dup_dates_remainder(self):
        remainders=self.setupProvider([
            [1,'2016-02-25',3],
            [2,'2016-02-25',1],
            [1,'2016-01-24',2],
            [2,'2016-02-27',4],
            ])
        self.assertRemaindersEqual([
            [1,'2016-02-25',3],
            [2,'2016-02-27',4],
        ])

    def test_return_last_dup_dates_remainder(self):
        remainders=self.setupProvider([
            [1,'2016-02-25',1],
            [1,'2016-02-25',2],
            [1,'2016-02-25',3],
            [1,'2016-02-25',4],
            [1,'2016-02-25',5],
            [1,'2016-02-25',6],
        ])
        self.assertRemaindersEqual([
            [1,'2016-02-25',6]
        ])

    def test_uniq_creation(self):
        remainders=self.Remainders.create({
            'n_shares': 1,
            'last_day_computed': '2016-02-25',
            'remainder_wh': 1
        })
        with self.assertRaises(Exception):
            self.Remainders.create({
                'n_shares': 1,
                'last_day_computed': '2016-02-25',
                'remainder_wh': 2
             })

if __name__ == '__main__':
    unittest.main()

