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

@unittest.skipIf(dbconfig, "depends on ERP")
class Remainder_Test(unittest.TestCase):

    def setupProvider(self,remainders=[]):
        Remainders = self.c.GenerationkwhRemainders
        for n,pointsDate,remainder in remainders:
            Remainders.create(dict(
                n_shares=n,
                last_day_computed=pointsDate,
                remainder_wh=remainder
                ))

    def assertRemaindersEqual(self, expectation):
        Remainders = self.c.GenerationkwhRemainders
        ids = Remainders.search([])
        result = [
            (
                r['n_shares'],
                r['last_day_computed'],
                r['remainder_wh']
            ) for r in Remainders.read(ids,
                ['n_shares','last_day_computed','remainder_wh'])
        ]
        self.assertEqual(result, expectation)

    def setUp(self):
        self.c = erppeek.Client(**dbconfig.erppeek)
        Remainders = self.c.GenerationkwhRemainders
        Remainders.unlink(Remainders.search())

    def tearDown(self):
        Remainders = self.c.GenerationkwhRemainders
        Remainders.unlink(Remainders.search())


    def test_no_remainders(self):
        remainders=self.setupProvider()
        self.assertRemaindersEqual([])

    def test_one_remainder(self):
        remainders=self.setupProvider([
                (1,'2016-02-25',3)
                ])
        self.assertRemaindersEqual([
            (1,'2016-02-25',3)
            ])

    def test_two_remainder(self):
        remainders=self.setupProvider([
                (1,'2016-02-25',3),
                (2,'2016-02-25',1)
                ])
        self.assertRemaindersEqual([
            (1,'2016-02-25',3),
            (2,'2016-02-25',1)
            ])
    
    def _test_dup_dates_remainder(self):
        remainders=self.setupProvider([
                (1,'2016-02-25',3),
                (2,'2016-02-25',1),
                (1,'2016-01-24',2),
                (2,'2016-02-27',4),
                ])
        self.assertRemaindersEqual([
                (1,'2016-02-25',3),
                (2,'2016-02-27',4),
        ])
    



if __name__ == '__main__':
    unittest.main()

