#!/usr/bin/env python

from .mongotimecurve import (
    MongoTimeCurve,
    dateToCurveIndex,
    curveIndexToDate,
    )
from .isodates import (
    asUtc,
    toLocal,
    localisodate,
    parseLocalTime,
    assertLocalDateTime,
    )
from . import testutils # proper ids
import pymongo
import datetime

import unittest

def localTime(string):
    isSummer = string.endswith("S")
    if isSummer: string=string[:-1]
    return parseLocalTime(string, isSummer)


class CurveDatetimeMapper_Test(unittest.TestCase):

    def assertDateEqual(self, result, expected):
        self.assertEqual(result, expected)
        self.assertEqual(str(result), str(expected))

    def test_dateToCurveIndex_inSummer(self):
       self.assertEqual(
            dateToCurveIndex(
                localisodate("2016-08-15"),
                localTime("2016-08-15 00:00:00")
                ), 0)

    def test_dateToCurveIndex_inSummer_secondHour(self):
       self.assertEqual(
            dateToCurveIndex(
                localisodate("2016-08-15"),
                localTime("2016-08-15 01:00:00")
                ), 1)

    def test_dateToCurveIndex_inSummer_nextDay(self):
       self.assertEqual(
            dateToCurveIndex(
                localisodate("2016-08-15"),
                localTime("2016-08-16 00:00:00")
                ), 25)

    def test_dateToCurveIndex_inWinter(self):
       self.assertEqual(
            dateToCurveIndex(
                localisodate("2016-12-25"),
                localTime("2016-12-25 00:00:00")
                ), 0)

    def test_dateToCurveIndex_beforeSummerToWinterChange(self):
       self.assertEqual(
            dateToCurveIndex(
                localisodate("2016-10-30"),
                localTime("2016-10-30 02:00:00S")
                ), 2)

    def test_dateToCurveIndex_afterSummerToWinterChange(self):
       self.assertEqual(
            dateToCurveIndex(
                localisodate("2016-10-30"),
                localTime("2016-10-30 02:00:00")
                ), 3)

    def test_dateToCurveIndex_beforeWinterToSummerChange(self):
       self.assertEqual(
            dateToCurveIndex(
                localisodate("2016-03-27"),
                localTime("2016-03-27 01:00:00")
                ), 1)

    def test_dateToCurveIndex_afterWinterToSummerChange(self):
       self.assertEqual(
            dateToCurveIndex(
                localisodate("2016-03-27"),
                localTime("2016-03-27 03:00:00")
                ), 2)


    def test_curveIndexToDate_summer(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-08-15"), 0),
            localTime("2016-08-15 00:00:00"))

    def test_curveIndexToDate_summer_secondHour(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-08-15"), 1),
            localTime("2016-08-15 01:00:00"))

    def test_curveIndexToDate_summer_lastHour(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-08-15"), 23),
            localTime("2016-08-15 23:00:00"))

    def test_curveIndexToDate_summer_padding_returnsNone(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-08-15"), 24),
            None)

    def test_curveIndexToDate_summer_nextDay(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-08-15"), 25),
            localTime("2016-08-16 00:00:00"))

    def test_curveIndexToDate_winter(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-12-25"), 1),
            localTime("2016-12-25 01:00:00"))

    def test_curveIndexToDate_winter_lastHour(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-12-25"), 23),
            localTime("2016-12-25 23:00:00"))

    def test_curveIndexToDate_winter_padding_returnsNone(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-12-25"), 24),
            None)

    def test_curveIndexToDate_winter_nextDay(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-12-25"), 26),
            localTime("2016-12-26 01:00:00"))

    
    def test_curveIndexToDate_toWinter_firsthour(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-10-30"), 0),
            localTime("2016-10-30 00:00:00"))

    def test_curveIndexToDate_toWinter_beforeChange(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-10-30"), 2),
            localTime("2016-10-30 02:00:00S"))

    def test_curveIndexToDate_toWinter_afterChange(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-10-30"), 3),
            localTime("2016-10-30 02:00:00"))

    def test_curveIndexToDate_toWinter_lastHour(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-10-30"), 24),
            localTime("2016-10-30 23:00:00"))


    def test_curveIndexToDate_toSummer_firstHour(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-03-27"), 0),
            localTime("2016-03-27 00:00:00"))

    def test_curveIndexToDate_toSummer_beforeChange(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-03-27"), 1),
            localTime("2016-03-27 01:00:00"))

    def test_curveIndexToDate_toSummer_afterChange(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-03-27"), 2),
            localTime("2016-03-27 03:00:00"))

    def test_curveIndexToDate_toSummer_lastHour(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-03-27"), 22),
            localTime("2016-03-27 23:00:00"))

    def test_curveIndexToDate_toSummer_padding1(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-03-27"), 23),
            None)

    def test_curveIndexToDate_toSummer_padding2(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-03-27"), 24),
            None)

    def test_curveIndexToDate_afterChanginToSummerSecond(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-03-27"), 3),
            localTime("2016-03-27 04:00:00"))

    def test_curveIndexToDate_summerButStartIsWinter(self):
       self.assertDateEqual(
            curveIndexToDate(localisodate("2016-10-29"), 51),
            localTime("2016-10-31 01:00:00"))

    def test_curveIndexToDate_winterButStartIsSummer(self):
        self.assertDateEqual(
            curveIndexToDate(localisodate("2016-3-26"), 50),
            localTime("2016-3-28 00:00:00"))



class MongoTimeCurve_Test(unittest.TestCase):

    def setUp(self):
        self.databasename = 'generationkwh_test'
        self.collection = 'generation'

        c = pymongo.MongoClient()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]

    def tearDown(self):
        c = pymongo.MongoClient()
        c.drop_database('generationkwh_test')
    
    def curve(self):
        return MongoTimeCurve(self.db, self.collection)

    def setupPoints(self, points):
        mtc = self.curve()
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
            start=localisodate('2015-01-01'),
            stop=localisodate('2015-01-01'),
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
            start=localisodate('2015-01-01'),
            stop=localisodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [0]*23+[10,0])

    def test_get_twoDays(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 10),
            ])

        curve = mtc.get(
            start=localisodate('2014-12-31'),
            stop=localisodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +25*[0]
            +23*[0]+[10,0]
            )

    def test_get_differentTime(self):
        mtc = self.setupPoints([
            ('2015-01-01 22:00:00', 'miplanta', 10),
            ])

        curve = mtc.get(
            start=localisodate('2015-01-01'),
            stop=localisodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            str(list(curve)),
            str(22*[0]+[10,0,0])
            )

    def test_get_outsideDates(self):
        mtc = self.setupPoints([
            ('2015-01-02 23:00:00', 'miplanta', 10),
            ])

        curve = mtc.get(
            start=localisodate('2015-01-01'),
            stop=localisodate('2015-01-01'),
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
            start=localisodate('2015-01-01'),
            stop=localisodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [0,10]+21*[0]+[10,0])

    def test_get_differentName_ignored(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'otraplanta', 10),
            ])

        curve = mtc.get(
            start=localisodate('2015-01-01'),
            stop=localisodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +25*[0])

    def test_get_noNameFilter_getsBoth(self):
        mtc = self.setupPoints([
            ('2015-01-01 21:00:00', 'miplanta', 10),
            ('2015-01-01 23:00:00', 'otraplanta', 20),
            ])

        curve = mtc.get(
            start=localisodate('2015-01-01'),
            stop=localisodate('2015-01-01'),
            filter=None,
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +21*[0]+[10,0,20,0])

    def test_get_differentNames_added(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 10),
            ('2015-01-01 23:00:00', 'otraplanta', 20),
            ])

        curve = mtc.get(
            start=localisodate('2015-01-01'),
            stop=localisodate('2015-01-01'),
            filter=None,
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +23*[0]+[30,0])

    def test_get_sameNameAndDate_prioritizesNewest(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 10),
            ])
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 30),
            ])

        curve = mtc.get(
            start=localisodate('2015-01-01'),
            stop=localisodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +23*[0]+[30,0])

    def test_get_noSummerPointsPadsLeft(self):
        mtc = self.setupPoints([
            ('2015-08-01 0:00:00', 'miplanta', 20),
            ('2015-08-01 23:00:00', 'miplanta', 10),
            ])

        curve = mtc.get(
            start=localisodate('2015-08-01'),
            stop=localisodate('2015-08-01'),
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
            start=localisodate('2015-03-29'),
            stop=localisodate('2015-03-29'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [1,2,3]+19*[0]+[4,0,0])

    def test_get_twoDays_includingToSummerDaylight(self):
        mtc = self.setupPoints([
            ('2015-03-30 23:00:00', 'miplanta', 10),
            ])

        curve = mtc.get(
            start=localisodate('2015-03-29'),
            stop=localisodate('2015-03-30'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +25*[0]
            +23*[0]+[10,0]
            )

    def test_get_dayligthIntoWinter(self):
        mtc = self.setupPoints([
            ('2015-10-25 00:00:00', 'miplanta', 1),
            ('2015-10-25 02:00:00S', 'miplanta', 2), # how to mark it??
            ('2015-10-25 02:00:00', 'miplanta', 3), # how to mark it??
            ('2015-10-25 23:00:00', 'miplanta', 4),
            ])

        curve = mtc.get(
            start=localisodate('2015-10-25'),
            stop=localisodate('2015-10-25'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [1,0,2,3]+20*[0]+[4])

    def test_fillPoint_complaintsMissingDatetime(self):
        mtc = self.curve()
        with self.assertRaises(Exception) as ass:
            mtc.fillPoint(
                name='miplanta',
                ae=10,
                )
        self.assertEqual(ass.exception.args[0],
            "Missing 'datetime'")

    def test_fillPoint_complaintsMissingName(self):
        mtc = self.curve()
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
        self.assertEqual(lastdate,localisodate('2015-01-01'))

    def test_lastDate_withOnePoint_atMidnight(self):
        mtc = self.setupPoints([
            ('2015-01-01 00:00:00', 'miplanta', 30),
            ])

        lastdate = mtc.lastDate('miplanta')
        self.assertEqual(lastdate,localisodate('2015-01-01'))

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
        self.assertEqual(lastdate,localisodate('2015-01-02'))

    def test_firstDate_whenNoPoint_returnsNone(self):
        mtc = self.setupPoints([
            ])

        lastdate = mtc.firstDate('miplanta')
        self.assertEqual(lastdate,None)

    def test_firstDate_withOnePoint_takesIt(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 30),
            ])

        lastdate = mtc.firstDate('miplanta')
        self.assertEqual(lastdate,localisodate('2015-01-01'))

    def test_firstDate_withForeignPoint_ignored(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'otraplanta', 30)
            ])

        lastdate = mtc.firstDate('miplanta')
        self.assertEqual(lastdate,None)

    def test_firstDate_withSeveralPoints_takesFirst(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 30),
            ('2015-01-02 23:00:00', 'miplanta', 30),
            ])

        lastdate = mtc.firstDate('miplanta')
        self.assertEqual(lastdate,localisodate('2015-01-01'))

    def setupDatePoints(self, date, name, values):
        return self.setupPoints([
            (date+" {:02}:00:00".format(i), name, value)
            for i, value in enumerate(values)
            ])

    def test_setupDatePoints(self):
        mtc = self.setupDatePoints('2015-01-01', 'miplanta', range(1,25))

        curve = mtc.get(
            start=localisodate('2015-01-01'),
            stop=localisodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            list(range(1,25)) + [0])

    def test_lastFullDate_withNoPoints(self):
        mtc = self.setupDatePoints('2015-01-01', 'miplanta', [1]*24)

        lastdate = mtc.lastFullDate('miplanta')
        self.assertEqual(lastdate,localisodate('2015-01-01'))

    def test_firstFullDate_withNoPoints(self):
        mtc = self.setupDatePoints('2015-01-01', 'miplanta', [1]*24)

        firstdate = mtc.lastFullDate('miplanta')
        self.assertEqual(firstdate,localisodate('2015-01-01'))

    def test_filled_whenEmpty(self):
        mtc = self.setupPoints([])

        _, curve = mtc.get(
            start=localisodate('2015-08-15'),
            stop=localisodate('2015-08-15'),
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
            start=localisodate('2015-08-15'),
            stop=localisodate('2015-08-15'),
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
                stop=localisodate("2015-08-15"),
                filter='miplanta',
                field='ae',
                )
        self.assertEqual(ctx.exception.args[0],
            "MongoTimeCurve.get called with naive (no timezone) start date")

    def test_get_withNaiveStopDate(self):
        mtc = self.setupPoints([])

        with self.assertRaises(AssertionError) as ctx:
            mtc.get(
                start=localisodate("2015-08-15"),
                stop=datetime.datetime(2015,8,15),
                filter='miplanta',
                field='ae',
                )
        self.assertEqual(ctx.exception.args[0],
            "MongoTimeCurve.get called with naive (no timezone) stop date")

    def test_update_singleBin(self):
        mtc = self.setupPoints([])

        curve = mtc.update(
            start=localisodate('2015-08-15'),
            filter='miplanta',
            field='ae',
            data=[1]+24*[0]
            )
        curve, filling = mtc.get(
            start=localisodate('2015-08-15'),
            stop=localisodate('2015-08-15'),
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

    def test_get_withFilledGap(self):
        mtc = self.setupPoints([])

        curve = mtc.update(
            start=localisodate('2015-08-01'),
            filter='miplanta',
            field='ae',
            data=+25*[1]+[1]+24*[1]
            )
        curve = mtc.get(
            start=localisodate('2015-08-01'),
            stop=localisodate('2015-08-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +24*[1]+[0]
            )

    def test_update_fullDay(self):
        mtc = self.setupPoints([])

        curve = mtc.update(
            start=localisodate('2015-08-15'),
            filter='miplanta',
            field='ae',
            data=+25*[1]
            )
        curve, filling = mtc.get(
            start=localisodate('2015-08-15'),
            stop=localisodate('2015-08-15'),
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

class MongoTimeCurveNew_Test(MongoTimeCurve_Test):
    def curve(self):
        return MongoTimeCurve(self.db, self.collection,
            creationField = 'create_date', 
            timestampField = 'utc_gkwh_timestamp',
            )



# TODO: Insert an object like the ones from gisce and read it

"""
{
        "_id" : ObjectId("5a846ed9c5a395531d1a78c1"),
        "create_date" : ISODate("2018-02-14T18:16:09.567Z"),
        "create_uid" : 1,
        "name" : "501600324",
        "timestamp" : ISODate("2018-01-25T23:00:00Z"),
        "season" : "W",
        "id" : 602,
        "magn" : 1000,
        "ae" : 0,
        "ai" : 3,
        "r1" : 0,
        "r2" : 0,
        "r3" : 0,
        "r4" : 6,
        "quality_ai" : 130,
        "quality_ae" : 130,
        "quality_r1" : 130,
        "quality_r2" : 130,
        "quality_r3" : 130,
        "quality_r4" : 130,
        "ae_fact" : 0,
        "ai_fact" : 0,
        "r1_fact" : 0,
        "r2_fact" : 0,
        "r3_fact" : 0,
        "r4_fact" : 0,
        "cch_fact" : false,
        "firm_fact" : false,
        "cch_bruta" : false,
        "valid" : false
        "valid_date" : false,
}
"""




# vim: et ts=4 sw=4
