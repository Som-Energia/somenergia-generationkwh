# -*- coding: utf-8 -*-
import unittest
import datetime
dbconfig = None
try:
    import dbconfig
    import erppeek
except ImportError:
    pass

@unittest.skipIf(not dbconfig, "depends on ERP")
class Remainder_Test(unittest.TestCase):

    def setUp(self):
        erp = erppeek.Client(**dbconfig.erppeek)
        self.RemainderHelper = erp.GenerationkwhRemainderTesthelper
        self.Remainder = erp.GenerationkwhRemainder
        self.RemainderHelper.clean()

    def setupProvider(self,remainders=[]):
        self.RemainderHelper.add(remainders)

    def assertLastEquals(self, expectation):
        result = self.RemainderHelper.last()
        self.assertEqual([list(a) for a in expectation], result)

    def tearDown(self):
        self.RemainderHelper.clean()

    def test_last_noRemainders(self):
        remainders=self.setupProvider()
        self.assertLastEquals([])

    def test_last_oneRemainder(self):
        remainders=self.setupProvider([
            (1,'2016-02-25',3),
            ])
        self.assertLastEquals([
            (1,'2016-02-25',3),
            ])

    def test_last_manyRemainder(self):
        remainders=self.setupProvider([
            (1,'2016-02-25',3),
            (2,'2016-02-25',1),
            ])
        self.assertLastEquals([
            (1,'2016-02-25',3),
            (2,'2016-02-25',1),
            ])

    def test_last_manyDates_takesLast(self):
        remainders=self.setupProvider([
            (1,'2016-02-25',3),
            (2,'2016-02-25',1),
            (1,'2016-01-24',2),
            (2,'2016-02-27',4),
            ])
        self.assertLastEquals([
            (1,'2016-02-25',3),
            (2,'2016-02-27',4),
            ])

    def test_last_sameDate_lastInsertedPrevails(self):
        remainders=self.setupProvider([
            (1,'2016-02-25',1),
            (1,'2016-02-25',2),
            (1,'2016-02-25',3),
            (1,'2016-02-25',4),
            (1,'2016-02-25',5),
            (1,'2016-02-25',6),
            ])
        self.assertLastEquals([
            (1,'2016-02-25',6),
            ])

    # TODO: Does this has sense at all? DGG
    def test_last_sameDateAndNShares_raises(self):
        remainders=self.Remainder.create(dict(
            n_shares=1,
            target_day='2016-02-25',
            remainder_wh=1,
        ))
        with self.assertRaises(Exception) as ctx:
            self.Remainder.create(dict(
                n_shares=1,
                target_day='2016-02-25',
                remainder_wh=2,
             ))

        self.assertIn(
            "Only one remainder of last date computed and "
            "number of shares is allowed",
            ctx.exception.faultCode
            )

if __name__ == '__main__':
    unittest.main()

