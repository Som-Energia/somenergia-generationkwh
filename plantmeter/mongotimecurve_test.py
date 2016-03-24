#!/usr/bin/env python

from .mongotimecurve import (
    MongoTimeCurve,
    dateToCurveIndex,
    curveIndexToDate,
    parseLocalTime,
    tz,
    )
import pymongo
import datetime

import unittest

def isodate(string):
    return tz.localize(datetime.datetime.strptime(string, "%Y-%m-%d"))

def localTime(string):
    isSummer = string.endswith("S")
    if isSummer: string=string[:-1]
    return parseLocalTime(string, isSummer)

class LocalTime_Test(unittest.TestCase):

    def test_localTime_fullySummer(self):
        self.assertEqual(
            str(localTime("2016-08-15 02:00:00")),
            "2016-08-15 02:00:00+02:00")

    def test_localTime_fullyWinter(self):
        self.assertEqual(
            str(localTime("2016-01-01 02:00:00")),
            "2016-01-01 02:00:00+01:00")

    def test_localTime_badTz_ignored(self):
        self.assertEqual(
            str(localTime("2016-01-01 02:00:00S")),
            "2016-01-01 02:00:00+01:00")

    def test_localTime_badSummerTz_ignored(self):
        self.assertEqual(
            str(localTime("2016-08-15 02:00:00")),
            "2016-08-15 02:00:00+02:00")

    def test_localTime_beforeOctoberChange(self):
        self.assertEqual(
            str(localTime("2016-10-30 02:00:00S")),
            "2016-10-30 02:00:00+02:00")

    def test_localTime_afterOctoberChange(self):
        self.assertEqual(
            str(localTime("2016-10-30 02:00:00")),
            "2016-10-30 02:00:00+01:00")

    def test_localTime_SIgnored(self):
        self.assertEqual(
            str(localTime("2016-10-30 03:00:00S")),
            "2016-10-30 03:00:00+01:00")

    def test_localTime_unexistingHour(self):
        # TOREVIEW: should it fail
        self.assertEqual(
            str(localTime("2016-03-27 02:00:00")),
            "2016-03-27 02:00:00+01:00")

class CurveDatetimeMapper_Test(unittest.TestCase):

    def assertDateEqual(self, result, expected):
        self.assertEqual(result, expected)
        self.assertEqual(str(result), str(expected))

    def test_dateToCurveIndex_inSummer(self):
       self.assertEquals(
            dateToCurveIndex(
                isodate("2016-08-15"),
                localTime("2016-08-15 00:00:00")
                ), 0)

    def test_dateToCurveIndex_inSummer_secondHour(self):
       self.assertEquals(
            dateToCurveIndex(
                isodate("2016-08-15"),
                localTime("2016-08-15 01:00:00")
                ), 1)

    def test_dateToCurveIndex_inSummer_nextDay(self):
       self.assertEquals(
            dateToCurveIndex(
                isodate("2016-08-15"),
                localTime("2016-08-16 00:00:00")
                ), 25)

    def test_dateToCurveIndex_inWinter(self):
       self.assertEquals(
            dateToCurveIndex(
                isodate("2016-12-25"),
                localTime("2016-12-25 00:00:00")
                ), 1)

    def test_dateToCurveIndex_beforeSummerToWinterChange(self):
       self.assertEquals(
            dateToCurveIndex(
                isodate("2016-10-30"),
                localTime("2016-10-30 02:00:00S")
                ), 2)

    def test_dateToCurveIndex_afterSummerToWinterChange(self):
       self.assertEquals(
            dateToCurveIndex(
                isodate("2016-10-30"),
                localTime("2016-10-30 02:00:00")
                ), 3)

    def test_dateToCurveIndex_beforeWinterToSummerChange(self):
       self.assertEquals(
            dateToCurveIndex(
                isodate("2016-03-27"),
                localTime("2016-03-27 01:00:00")
                ), 2)

    def test_dateToCurveIndex_afterWinterToSummerChange(self):
       self.assertEquals(
            dateToCurveIndex(
                isodate("2016-03-27"),
                localTime("2016-03-27 03:00:00")
                ), 3)

    def test_curveIndexToDate_summer(self):
       self.assertDateEqual(
            curveIndexToDate(isodate("2016-08-15"), 0),
            localTime("2016-08-15 00:00:00"))

    def test_curveIndexToDate_summer_secondHour(self):
       self.assertDateEqual(
            curveIndexToDate(isodate("2016-08-15"), 1),
            localTime("2016-08-15 01:00:00"))

    def test_curveIndexToDate_summer_nextDay(self):
       self.assertDateEqual(
            curveIndexToDate(isodate("2016-08-15"), 25),
            localTime("2016-08-16 00:00:00"))

    def test_curveIndexToDate_summer_paddingReturnsNone(self):
       self.assertDateEqual(
            curveIndexToDate(isodate("2016-08-15"), 24),
            None)

    def test_curveIndexToDate_winter(self):
       self.assertDateEqual(
            curveIndexToDate(isodate("2016-12-25"), 1),
            localTime("2016-12-25 00:00:00"))

    def test_curveIndexToDate_winter_paddingReturnsNone(self):
       self.assertDateEqual(
            curveIndexToDate(isodate("2016-12-25"), 0),
            None)

    def test_curveIndexToDate_winter_nextDay(self):
       self.assertDateEqual(
            curveIndexToDate(isodate("2016-12-25"), 26),
            localTime("2016-12-26 00:00:00"))

    
    def test_curveIndexToDate_beforeChanginToWinter(self):
       self.assertDateEqual(
            curveIndexToDate(isodate("2016-10-30"), 2),
            localTime("2016-10-30 02:00:00S"))

    def test_curveIndexToDate_afterChanginToWinter(self):
       self.assertDateEqual(
            curveIndexToDate(isodate("2016-10-30"), 3),
            localTime("2016-10-30 02:00:00"))

    def test_curveIndexToDate_afterChanginToWinter(self):
       self.assertDateEqual(
            curveIndexToDate(isodate("2016-10-30"), 3),
            localTime("2016-10-30 02:00:00"))

    def test_curveIndexToDate_summerButStartIsWinter(self):
       self.assertDateEqual(
            curveIndexToDate(isodate("2016-10-29"), 51),
            localTime("2016-10-31 00:00:00"))

    def test_curveIndexToDate_winterButStartIsSummer(self):
        self.assertDateEqual(
            curveIndexToDate(isodate("2016-3-26"), 50),
            localTime("2016-3-28 00:00:00"))

    def test_curveIndexToDate_noPaddingBeforeSummerToWinter(self):
        self.assertDateEqual(
            curveIndexToDate(isodate("2016-10-30"), 0),
            localTime("2016-10-30 00:00:00"))

    def test_curveIndexToDate_noPaddingAfterSummerToWinter(self):
        self.assertDateEqual(
            curveIndexToDate(isodate("2016-10-30"), 24),
            localTime("2016-10-30 23:00:00"))

    def test_curveIndexToDate_paddingBeforeWinterToSummer(self):
        self.assertDateEqual(
            curveIndexToDate(isodate("2016-03-27"), 0),
            None)

    def test_curveIndexToDate_paddingAfterWinterToSummer(self):
        self.assertDateEqual(
            curveIndexToDate(isodate("2016-03-27"), 24),
            None)

    

class MongoTimeCurve_Test(unittest.TestCase):

    def setUp(self):
        self.databasename = 'generationkwh_test'
        self.collection = 'generation'

        c = pymongo.Connection()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]

    def tearDown(self):
        c = pymongo.Connection()
        c.drop_database('generationkwh_test')
    
    def setupPoints(self, points):
        mtc = MongoTimeCurve(self.db, self.collection)
        for datetime, plant, value in points:
            mtc.fillPoint(
                datetime=localTime(datetime),
                name=plant,
                ae=value,
            )
        return mtc


    def test_get_whenEmpty(self):
        mtc = self.setupPoints([
            ])
        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [0]*25)

    def test_get_withSingleData(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 10),
            ])

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [0]*24+[10])

    def test_get_twoDays(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 10),
            ])

        curve = mtc.get(
            start=isodate('2014-12-31'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +25*[0]
            +24*[0]+[10]
            )

    def test_get_differentTime(self):
        mtc = self.setupPoints([
            ('2015-01-01 22:00:00', 'miplanta', 10),
            ])

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            str(list(curve)),
            str(+23*[0]+[10,0])
            )

    def test_get_withOutsideData(self):
        mtc = self.setupPoints([
            ('2015-01-02 23:00:00', 'miplanta', 10),
            ])

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +25*[0])

    def test_get_withTwoPoints(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 10),
            ('2015-01-01 01:00:00', 'miplanta', 10),
            ])

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [0,0,10]+21*[0]+[10])

    def test_get_differentNameIgnored(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'otraplanta', 10),
            ])

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +25*[0])


    def test_get_prioritizesNewest(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 10),
            ('2015-01-01 23:00:00', 'miplanta', 30),
            ])

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +24*[0]+[30])

    def test_get_summerPointsPadsLeft(self):
        mtc = self.setupPoints([
            ('2015-08-01 0:00:00', 'miplanta', 20),
            ('2015-08-01 23:00:00', 'miplanta', 10),
            ])

        curve = mtc.get(
            start=isodate('2015-08-01'),
            stop=isodate('2015-08-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [20]+22*[0]+[10,0])

    def test_get_dayligthIntoSummer(self):
        mtc = self.setupPoints([
            ('2015-03-29 00:00:00', 'miplanta', 1),
            ('2015-03-29 01:00:00', 'miplanta', 2),
#            ('2015-03-29 02:00:00', 'miplanta', 2), # should fail (other test?)
            ('2015-03-29 03:00:00', 'miplanta', 3),
            ('2015-03-29 23:00:00', 'miplanta', 4),
            ])

        curve = mtc.get(
            start=isodate('2015-03-29'),
            stop=isodate('2015-03-29'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [0,1,2,3]+19*[0]+[4,0])

    def test_get_dayligthIntoWinter(self):
        mtc = self.setupPoints([
            ('2015-10-25 00:00:00', 'miplanta', 1),
            ('2015-10-25 02:00:00S', 'miplanta', 2), # how to mark it??
            ('2015-10-25 02:00:00', 'miplanta', 3), # how to mark it??
            ('2015-10-25 23:00:00', 'miplanta', 4),
            ])

        curve = mtc.get(
            start=isodate('2015-10-25'),
            stop=isodate('2015-10-25'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [1,0,2,3]+20*[0]+[4])

    def test_fillPoint_complaintsMissingDatetime(self):
        mtc = MongoTimeCurve(self.db, self.collection)
        with self.assertRaises(Exception) as ass:
            mtc.fillPoint(
                name='miplanta',
                ae=10,
                )
        self.assertEqual(ass.exception.args[0],
            "Missing 'datetime'")

    def test_fillPoint_complaintsMissingName(self):
        mtc = MongoTimeCurve(self.db, self.collection)
        with self.assertRaises(Exception) as ass:
            mtc.fillPoint(
                datetime=localTime('2015-08-01 23:00:00'),
                ae=10,
                )
        self.assertEqual(ass.exception.args[0],
            "Missing 'name'")

    def test_lastDate_whenNoPoint_returnsNone(self):
        mtc = self.setupPoints([
            ])

        lastdate = mtc.lastDate('miplanta')
        self.assertEqual(lastdate,None)

    def test_lastDate_withOnePoint_takesIt(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 30),
            ])

        lastdate = mtc.lastDate('miplanta')
        self.assertEqual(lastdate,isodate('2015-01-01'))

    def test_lastDate_withForeignPoint_ignored(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'otraplanta', 30)
            ])

        lastdate = mtc.lastDate('miplanta')
        self.assertEqual(lastdate,None)
      
    def test_lastDate_withSeveralPoints_takesLast(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 30),
            ('2015-01-02 23:00:00', 'miplanta', 30),
            ])

        lastdate = mtc.lastDate('miplanta')
        self.assertEqual(lastdate,isodate('2015-01-02'))

    def test_firstDate_withSeveralPoints_takesFirst(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 30),
            ('2015-01-02 23:00:00', 'miplanta', 30),
            ])

        lastdate = mtc.firstDate('miplanta')
        self.assertEqual(lastdate,isodate('2015-01-01'))

    def setupDatePoints(self, date, name, values):
        return self.setupPoints([
            (date+" {:02}:00:00".format(i), name, value)
            for i, value in enumerate(values)
            ])

    def test_setupDatePoints(self):
        mtc = self.setupDatePoints('2015-01-01', 'miplanta', range(1,25))

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            list([0]+range(1,25)))

    def test_lastFullDate_withNoPoints(self):
        mtc = self.setupDatePoints('2015-01-01', 'miplanta', [1]*24)

        lastdate = mtc.lastFullDate('miplanta')
        self.assertEqual(lastdate,isodate('2015-01-01'))

    def test_filled_whenEmpty(self):
        mtc = self.setupPoints([])

        _, curve = mtc.get(
            start=isodate('2015-08-15'),
            stop=isodate('2015-08-15'),
            filter='miplanta',
            field='ae',
            filling=True,
            )
        self.assertEqual(
            list(curve),
            +25*[False]
            )

    def test_filled_withAPoint_inSummer(self):
        mtc = self.setupPoints([
            ('2015-08-15 00:00:00', 'miplanta', 30),
            ])

        _,curve = mtc.get(
            start=isodate('2015-08-15'),
            stop=isodate('2015-08-15'),
            filter='miplanta',
            field='ae',
            filling=True,
            )
        self.assertEqual(
            list(curve),
            [True]+24*[False]
            )

    def test_update_withNaiveDate(self):
        mtc = self.setupPoints([])

        with self.assertRaises(AssertionError) as ctx:
            mtc.update(
                start=datetime.datetime(2015,8,15),
                filter='miplanta',
                field='ae',
                data=[],
                )
        self.assertEqual(ctx.exception.args[0],
            "MongoTimeCurve.update called with naive (no timezone) start date")

    def test_fillPoint_withNaiveDatetime(self):
        mtc = self.setupPoints([])

        with self.assertRaises(AssertionError) as ctx:
            mtc.fillPoint(
                datetime=datetime.datetime(2015,8,15),
                name='miplanta',
                ae=10,
                )
        self.assertEqual(ctx.exception.args[0],
            "MongoTimeCurve.fillPoint with naive (no timezone) datetime")

    def test_get_withNaiveStartDate(self):
        mtc = self.setupPoints([])

        with self.assertRaises(AssertionError) as ctx:
            mtc.get(
                start=datetime.datetime(2015,8,15),
                stop=isodate("2015-08-15"),
                filter='miplanta',
                field='ae',
                )
        self.assertEqual(ctx.exception.args[0],
            "MongoTimeCurve.get called with naive (no timezone) start date")

    def test_get_withNaiveStopDate(self):
        mtc = self.setupPoints([])

        with self.assertRaises(AssertionError) as ctx:
            mtc.get(
                start=isodate("2015-08-15"),
                stop=datetime.datetime(2015,8,15),
                filter='miplanta',
                field='ae',
                )
        self.assertEqual(ctx.exception.args[0],
            "MongoTimeCurve.get called with naive (no timezone) stop date")

    def test_update_singleBin(self):
        mtc = self.setupPoints([])

        curve = mtc.update(
            start=isodate('2015-08-15'),
            filter='miplanta',
            field='ae',
            data=[1]+24*[0]
            )
        curve, filling = mtc.get(
            start=isodate('2015-08-15'),
            stop=isodate('2015-08-15'),
            filter='miplanta',
            field='ae',
            filling=True,
            )
        self.assertEqual(
            list(curve),
            [1]+24*[0]
            )
        self.assertEqual(
            list(filling),
            [True]+24*[False]
            )

    def test_update_fullDay(self):
        mtc = self.setupPoints([])

        curve = mtc.update(
            start=isodate('2015-08-15'),
            filter='miplanta',
            field='ae',
            data=+25*[1]
            )
        curve, filling = mtc.get(
            start=isodate('2015-08-15'),
            stop=isodate('2015-08-15'),
            filter='miplanta',
            field='ae',
            filling=True,
            )
        self.assertEqual(
            list(curve),
            +24*[1]+[0]
            )
        self.assertEqual(
            list(filling),
            +24*[True]+[False]
            )




# vim: et ts=4 sw=4
