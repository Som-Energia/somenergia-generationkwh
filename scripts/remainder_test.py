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
        self.Remainder = erp.GenerationkwhRemainder
        self.RemainderHelper = erp.GenerationkwhRemainderTesthelper
        self.RemainderHelper.clean()

    def setupProvider(self,remainders=[]):
        self.RemainderHelper.updateRemainders(remainders)

    def assertLastEquals(self, expectation):
        result = self.RemainderHelper.lastRemainders()
        self.assertEqual([list(a) for a in expectation], result)

    def tearDown(self):
        self.RemainderHelper.clean()

    def test_last_noRemainders(self):
        self.setupProvider()
        self.assertLastEquals([])

    def test_last_oneRemainder(self):
        self.setupProvider([
            (1,'2016-02-25',3),
            ])
        self.assertLastEquals([
            (1,'2016-02-25',3),
            ])

    def test_last_manyRemainder(self):
        self.setupProvider([
            (1,'2016-02-25',3),
            (2,'2016-02-25',1),
            ])
        self.assertLastEquals([
            (1,'2016-02-25',3),
            (2,'2016-02-25',1),
            ])

    def test_last_manyDates_takesLast(self):
        self.setupProvider([
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
        self.setupProvider([
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
        self.Remainder.create(dict(
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

    def test_newRemaindersToTrack_when1SharesAvailable(self):
        self.setupProvider([
            (1,'2016-02-25',1),
            ])
        self.Remainder.newRemaindersToTrack([3])
        self.assertLastEquals([
            (1,'2016-02-25',1),
            (3,'2016-02-25',0),
            ])

    def test_newRemaindersToTrack_when1SharesAvailable_takesOlder(self):
        self.setupProvider([
            (1,'2016-02-25',1),
            (1,'2016-02-28',1),
            ])
        self.Remainder.newRemaindersToTrack([3])
        self.assertLastEquals([
            (1,'2016-02-28',1),
            (3,'2016-02-25',0),
            ])

    def test_newRemaindersToTrack_no1Shares_ignores(self):
        self.setupProvider([
            ])
        self.Remainder.newRemaindersToTrack([3])
        self.assertLastEquals([
            ])

    def test_newRemaindersToTrack_otherButNo1Shares_ignored(self):
        self.setupProvider([
            (2,'2016-02-25',1),
            ])
        self.Remainder.newRemaindersToTrack([3])
        self.assertLastEquals([
            (2,'2016-02-25',1),
            ])

    def test_newRemaindersToTrack_manyRemindersToTrack(self):
        self.setupProvider([
            (1,'2016-02-25',0),
            ])
        self.Remainder.newRemaindersToTrack([3,6])
        self.assertLastEquals([
            (1,'2016-02-25',0),
            (3,'2016-02-25',0),
            (6,'2016-02-25',0),
            ])

    def assertFilledEqual(self, expectation):
        result = self.Remainder.filled()
        self.assertEqual(expectation, result)

    def test_filled_oneReminder_returnsNothing(self):
        self.setupProvider([
            (1,'2016-02-25',3),
            ])
        self.assertFilledEqual([
            ])

    def test_filled_twoReminder_thatReminder(self):
        self.setupProvider([
            (1,'2016-02-25',3),
            (1,'2016-02-26',2),
            ])
        self.assertFilledEqual([1])

    def test_filled_twoReminder_differentNShares(self):
        self.setupProvider([
            (1,'2016-02-25',3),
            (2,'2016-02-25',3),
            ])
        self.assertFilledEqual([])


if __name__ == '__main__':
    unittest.main()

