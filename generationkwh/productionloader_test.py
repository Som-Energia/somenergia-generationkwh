# -*- coding: utf-8 -*-

from .productionloader import ProductionLoader
import unittest
import datetime
import pymongo
from .rightspershare import RightsPerShare
import numpy

from .isodates import  isodate, localisodate

def zeropad(array, left, right):
    return numpy.pad(array, (left, right), 'constant', constant_values=[0])

class ProductionAggregatorMockUp(object):

    def __init__(self,first=None,last=None,data=None):
        self.data = data
        self.firstDate = first
        self.lastDate = last

    def get_kwh(self, firstDate, lastDate):
        if firstDate > lastDate:
            return numpy.array([])
        nbins = 25*((lastDate-firstDate).days+1)

        if lastDate<self.firstDate:
            return numpy.zeros(nbins)
        if self.lastDate<firstDate:
            return numpy.zeros(nbins)

        frontpad = backpad = 0
        offset = (firstDate - self.firstDate).days * 25
        trailing = (self.lastDate - lastDate).days * 25

        if offset<0:
            frontpad = -offset
            offset = 0
        if trailing<0:
            backpad = -trailing
            trailing = 0

        data = self.data[offset:nbins-trailing-frontpad]

        return zeropad(data, frontpad, backpad)

    def getFirstMeasurementDate(self):
        return self.firstDate

    def getLastMeasurementDate(self):
        return self.lastDate

class ProductionAggregatorMockUp_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.p = ProductionAggregatorMockUp(
            first=isodate('2015-08-16'),
            last=isodate('2015-08-20'),
            data=numpy.arange(100),
            )

    def test_getkwh_empyInterval(self):
        result = self.p.get_kwh(
            isodate('2015-08-17'),
            isodate('2015-08-16'),
            )
        self.assertEqual(list(result), [])

    def test_getkwh_beforeData(self):
        result = self.p.get_kwh(
            isodate('2015-08-14'),
            isodate('2015-08-15'),
            )
        self.assertEqual(list(result), 50*[0])

    def test_getkwh_afterData(self):
        result = self.p.get_kwh(
            isodate('2015-08-21'),
            isodate('2015-08-22'),
            )
        self.assertEqual(list(result), 50*[0])

    def test_getkwh_matchingData(self):
        result = self.p.get_kwh(
            isodate('2015-08-16'),
            isodate('2015-08-20'),
            )
        self.assertEqual(list(result), range(100))

    def test_getkwh_startInMiddle(self):
        result = self.p.get_kwh(
            isodate('2015-08-17'),
            isodate('2015-08-20'),
            )
        self.assertEqual(list(result), range(25,100))

    def test_getkwh_endInMiddle(self):
        result = self.p.get_kwh(
            isodate('2015-08-16'),
            isodate('2015-08-19'),
            )
        self.assertEqual(list(result), range(75))

    def test_getkwh_startingBeforeData(self):
        result = self.p.get_kwh(
            isodate('2015-08-15'),
            isodate('2015-08-20'),
            )
        self.assertEqual(list(result), 25*[0]+range(100))

    def test_getkwh_startingBeforeDataEndingMiddle(self):
        result = self.p.get_kwh(
            isodate('2015-08-15'),
            isodate('2015-08-19'),
            )
        self.assertEqual(list(result), 25*[0]+range(75))

    def test_getkwh_endingAfterData(self):
        result = self.p.get_kwh(
            isodate('2015-08-16'),
            isodate('2015-08-21'),
            )
        self.assertEqual(list(result), range(100)+25*[0])

    def test_getkwh_endingAfterDataStartingMiddle(self):
        result = self.p.get_kwh(
            isodate('2015-08-17'),
            isodate('2015-08-21'),
            )
        self.assertEqual(list(result), range(25,100)+25*[0])

class RemainderProviderMockup(object):

    def __init__(self,remainders=[]):
        self.remainders = dict((remainder[0], remainder) for remainder in remainders)

    def lastRemainders(self):
        return [self.remainders[nshares] for nshares in self.remainders]

    def updateRemainders(self, remainders):
        for nshares, date, remainder in remainders:
            self.remainders[nshares] = (nshares, date, remainder)

class PlantShareCurverMockup(object):

    def __init__(self, data):
        self.data = data

    def hourly(self, start, end):
        return self.data


class ProductionLoaderTest(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.databasename = 'generationkwh_test'

        c = pymongo.MongoClient()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]

    def tearDown(self):
        c = pymongo.MongoClient()
        c.drop_database(self.databasename)


    def assertStartPointEqual(self, firstProductionDate, remainders, expected):
        l = ProductionLoader()
        date = l.startPoint(isodate(firstProductionDate),[
            (shares, isodate(date), remainderwh)
            for shares, date, remainderwh in remainders
            ])
        self.assertEqual(str(date), expected)

    def test_startPoint_withNoremainders(self):
        self.assertStartPointEqual('2000-01-01',[
            ], '2000-01-01')

    def test_startPoint_withSingleRemainder(self):
        self.assertStartPointEqual('2000-01-01',[
            (1, '2001-01-01', 45),
            ], '2001-01-01')

    def test_startPoint_withManyRemainders(self):
        self.assertStartPointEqual('2000-01-01',[
            (1, '2002-01-01', 45),
            (2, '2001-01-01', 45),
            ], '2001-01-01')


    def test_endPoint_withNoProduction(self):
        l = ProductionLoader()
        date = l.endPoint(isodate('2000-01-01'), [])
        self.assertEqual('2000-01-01', str(date))

    def test_endPoint_withOneDay(self):
        l = ProductionLoader()
        date = l.endPoint(isodate('2000-01-01'), 25*[0])
        self.assertEqual('2000-01-02', str(date))

    def test_endPoint_withHalfADay_justReturnsTheWholeOnes(self):
        l = ProductionLoader()
        date = l.endPoint(isodate('2000-01-01'), 27*[0])
        self.assertEqual('2000-01-02', str(date))


    def assertDatePairEqual(self, expected, result):
        e1,e2 = expected
        self.assertEqual((isodate(e1),isodate(e2)), result)

    def test_getRecomputationInterval_withNoremainders_takesFirstMeassure(self):
        p = ProductionAggregatorMockUp(
                first=isodate('2000-01-01'),
                last=isodate('2006-01-01'),
                )
        l = ProductionLoader(productionAggregator=p)
        interval = l._recomputationInterval([])
        self.assertDatePairEqual( ('2000-01-01','2006-01-01'), interval)

    def test_getRecomputationInterval_withSingleRemainders_takesIt(self):
        p = ProductionAggregatorMockUp(
                first=isodate('2000-01-01'),
                last=isodate('2006-01-01'),
                )
        l = ProductionLoader(productionAggregator=p)
        interval = l._recomputationInterval([
            (1,isodate('2001-01-01'), 45),
            ])
        self.assertDatePairEqual( ('2001-01-01','2006-01-01'), interval)

    def test_getRecomputationInterval_withManyRemainders_takesEarlier(self):
        p = ProductionAggregatorMockUp(
                first=isodate('2000-01-01'),
                last=isodate('2006-01-01'),
                )
        l = ProductionLoader(productionAggregator=p)
        interval = l._recomputationInterval([
            (1,isodate('2002-01-01'), 45),
            (2,isodate('2001-01-01'), 45),
            ])
        self.assertDatePairEqual( ('2001-01-01','2006-01-01'), interval)

    @unittest.skip("Failing case!!")
    def test_getRecomputationInterval_withRemaindersSameTarget_takesLater(self):
        p = ProductionAggregatorMockUp(
                first=isodate('2000-01-01'),
                last=isodate('2006-01-01'),
                )
        l = ProductionLoader(productionAggregator=p)
        interval = l._recomputationInterval([
            (1,isodate('2002-01-01'), 45),
            (1,isodate('2001-01-01'), 45),
            ])
        self.assertDatePairEqual(
            ('2002-01-01','2006-01-01'),
            interval)

    def test_appendRightsPerShare_singleDay(self):
        l = ProductionLoader()
        rights, remainder = l._appendRightsPerShare(
            nshares=1,
            firstDateToCompute=isodate('2015-08-16'),
            lastDateToCompute=isodate('2015-08-16'),
            lastRemainder=0,
            production=numpy.array(+10*[0]+[1000]+14*[0]),
            plantshares=numpy.array(25*[1]),
            )
        self.assertEqual(list(rights),
            +10*[0]+[1000]+14*[0])
        self.assertEqual(remainder, 0)
    

    def test_appendRightsPerShare_manyDays(self):
        l = ProductionLoader()
        rights, remainder = l._appendRightsPerShare(
            nshares=1,
            firstDateToCompute=isodate('2015-08-16'),
            lastDateToCompute=isodate('2015-08-17'),
            lastRemainder=0,
            production=numpy.array((+10*[0]+[1000]+14*[0])*2),
            plantshares=numpy.array(25*[1]*2),
            )
        self.assertEqual(list(rights),
            (+10*[0]+[1000]+14*[0])*2)
        self.assertEqual(remainder, 0)

    def test_appendRightsPerShare_withManyPlantShares_divides(self):
        l = ProductionLoader()
        rights, remainder = l._appendRightsPerShare(
            nshares=1,
            firstDateToCompute=isodate('2015-08-16'),
            lastDateToCompute=isodate('2015-08-16'),
            lastRemainder=0,
            production=numpy.array(+10*[0]+[2000]+14*[0]),
            plantshares=numpy.array(25*[4]), # here
            )
        self.assertEqual(list(rights),
            +10*[0]+[500]+14*[0])
        self.assertEqual(remainder, 0)

    def test_appendRightsPerShare_withNShares_multiplies(self):
        l = ProductionLoader()
        rights, remainder = l._appendRightsPerShare(
            nshares=2, # here
            firstDateToCompute=isodate('2015-08-16'),
            lastDateToCompute=isodate('2015-08-16'),
            lastRemainder=0,
            production=numpy.array(+10*[0]+[1000]+14*[0]),
            plantshares=numpy.array(25*[1]),
            )
        self.assertEqual(list(rights),
            +10*[0]+[2000]+14*[0])
        self.assertEqual(remainder, 0)

    def test_appendRightsPerShare_withAdvancedRemainder(self):
        l = ProductionLoader()
        rights, remainder = l._appendRightsPerShare(
            nshares=1,
            firstDateToCompute=isodate('2015-08-16'),
            lastDateToCompute=isodate('2015-08-16'),
            lastRemainder=0,
            production=numpy.array(100*[0]+10*[0]+[1000]+14*[0]), # 100+1 days
            plantshares=numpy.array(100*[0]+25*[1]),
            )
        self.assertEqual(list(rights),
            +10*[0]+[1000]+14*[0])
        self.assertEqual(remainder, 0)


    def test_appendRightsPerShare_firstDateToCompute_isProtected(self):
        l = ProductionLoader()
        with self.assertRaises(AssertionError) as ctx:
            l._appendRightsPerShare(
                nshares=1,
                firstDateToCompute=localisodate('2015-08-16'), # here
                lastDateToCompute=isodate('2015-08-16'),
                lastRemainder=0,
                production=numpy.array(25*[1]),
                plantshares=numpy.array(25*[1]),
                )
        # also non CEST/CET, and naive, using assertLocalDateTime
        self.assertEqual(ctx.exception.args[0],
            "firstDateToCompute should be a datetime.date but it is "
            "2015-08-16 00:00:00+02:00")

    def test_appendRightsPerShare_lastDateToCompute_isProtected(self):
        l = ProductionLoader()
        with self.assertRaises(AssertionError) as ctx:
            l._appendRightsPerShare(
                nshares=1,
                firstDateToCompute=isodate('2015-08-16'),
                lastDateToCompute=localisodate('2015-08-16'), # here
                lastRemainder=0,
                production=numpy.array(25*[1]),
                plantshares=numpy.array(25*[1]),
                )
        # also non CEST/CET, and naive, using assertLocalDateTime
        self.assertEqual(ctx.exception.args[0],
            "lastDateToCompute should be a datetime.date but it is "
            "2015-08-16 00:00:00+02:00")

    def test_appendRightsPerShare_tooSmallProductionArray(self):
        l = ProductionLoader()
        with self.assertRaises(AssertionError) as ctx:
            l._appendRightsPerShare(
                nshares=1,
                firstDateToCompute=isodate('2015-08-16'),
                lastDateToCompute=isodate('2015-08-17'),
                lastRemainder=0,
                production=numpy.array(49*[1]),
                plantshares=numpy.array(50*[1]),
                )
        self.assertEqual(ctx.exception.args[0],
            "Not enough production data to compute such date interval")

    def test_appendRightsPerShare_tooSmallShareArray(self):
        l = ProductionLoader()
        with self.assertRaises(AssertionError) as ctx:
            l._appendRightsPerShare(
                nshares=1,
                firstDateToCompute=isodate('2015-08-16'),
                lastDateToCompute=isodate('2015-08-17'),
                lastRemainder=0,
                production=numpy.array(50*[1]),
                plantshares=numpy.array(49*[1]),
                )
        self.assertEqual(ctx.exception.args[0],
            "Not enough plant share data to compute such date interval")

    def test_appendRightsPerShare_crossedDates(self):
        l = ProductionLoader()
        with self.assertRaises(AssertionError) as ctx:
            l._appendRightsPerShare(
                nshares=1,
                firstDateToCompute=isodate('2015-08-16'),
                lastDateToCompute=isodate('2015-08-15'),
                lastRemainder=0,
                production=numpy.array(50*[1]),
                plantshares=numpy.array(50*[1]),
                )
        self.assertEqual(ctx.exception.args[0],
            "Empty interval starting at 2015-08-16 and ending at 2015-08-15")

    def test_updateRights(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShare=rights, remainders=remainders)

        l._updateRights(
            nshares=3,
            rights = 50*[1],
            firstDate=isodate('2015-08-16'),
            lastDate=isodate('2015-08-17'),
            remainder=69,
            )

        result = rights.rightsPerShare(3,
            isodate('2015-08-16'),
            isodate('2015-08-17'))
        self.assertEqual(list(result),
            +24*[1]+[0]
            +24*[1]+[0]
            )
        self.assertEqual(remainders.lastRemainders(), [
            (3, isodate('2015-08-18'), 69),
            ])

    def test_computeAvailableRights_singleDay(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([
            (1, isodate('2015-08-16'), 0),
            ])
        production = ProductionAggregatorMockUp(
                first=isodate('2015-08-16'),
                last=isodate('2015-08-16'),
                data=numpy.array(+10*[0]+[1000]+14*[0]))
        plantShare = PlantShareCurverMockup(
                data=numpy.array(25*[1]))
        l = ProductionLoader(productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders)
        l.computeAvailableRights()
        result = rights.rightsPerShare(1,
            isodate('2015-08-16'),
            isodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[1000]+14*[0])
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-17'), 0),
            ])

    def test_computeAvailableRights_withManyPlantShares_divides(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([
            (1, isodate('2015-08-16'), 0),
            ])
        production = ProductionAggregatorMockUp(
                first=isodate('2015-08-16'),
                last=isodate('2015-08-16'),
                data=numpy.array(+10*[0]+[20000]+14*[0]))
        plantShare = PlantShareCurverMockup(
                data=numpy.array(25*[4]))
        l = ProductionLoader(productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders)
        l.computeAvailableRights()
        result = rights.rightsPerShare(1,
            isodate('2015-08-16'),
            isodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[5000]+14*[0])
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-17'), 0),
            ])

    def test_computeAvailableRights_withNShares_multiplies(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([
            (1, isodate('2015-08-16'), 0),
            (2, isodate('2015-08-16'), 0),
            ])
        production = ProductionAggregatorMockUp(
                first=isodate('2015-08-16'),
                last=isodate('2015-08-16'),
                data=numpy.array(+10*[0]+[1]+14*[0]))
        plantShare = PlantShareCurverMockup(
                data=numpy.array(25*[1]))
        l = ProductionLoader(productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders)
        l.computeAvailableRights()
        result = rights.rightsPerShare(2,
            isodate('2015-08-16'),
            isodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[2]+14*[0])
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-17'), 0),
            (2, isodate('2015-08-17'), 0),
            ])

    def test_computeAvailableRights_withAdvancedRemainder(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([
            (1, isodate('2015-08-16'), 0),
            ])
        production = ProductionAggregatorMockUp(
                first=isodate('2015-08-16'),
                last=isodate('2015-08-16'),
                data=numpy.array(100*[0]+10*[0]+[1000]+14*[0]))
        plantShare = PlantShareCurverMockup(
                data=numpy.array(100*[0]+25*[1]))
        l = ProductionLoader(productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders)
        l.computeAvailableRights()
        result = rights.rightsPerShare(1,
            isodate('2015-08-16'),
            isodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[1000]+14*[0])
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-17'), 0),
            ])

    def test_computeAvailableRights_withSeveralDays(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([
            (1, isodate('2015-08-16'), 0),
            ])
        production = ProductionAggregatorMockUp(
                first=isodate('2015-08-16'),
                last=isodate('2015-08-17'),
                data=numpy.array(
                    +10*[0]+[1000]+14*[0]
                    +10*[0]+[2000]+14*[0]
                ))
        plantShare = PlantShareCurverMockup(
                data=numpy.array(50*[1]))
        l = ProductionLoader(productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders)
        l.computeAvailableRights()
        result = rights.rightsPerShare(1,
            isodate('2015-08-16'),
            isodate('2015-08-17'))
        self.assertEqual(list(result),
            +10*[0]+[1000]+14*[0]
            +10*[0]+[2000]+14*[0]
            )
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-18'), 0),
            ])

    def test_computeAvailableRights_withExplicitStop(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([
            (1, isodate('2015-08-16'), 0),
            ])
        production = ProductionAggregatorMockUp(
                first=isodate('2015-08-16'),
                last=isodate('2015-08-17'),
                data=numpy.array(
                    +10*[0]+[1000]+14*[0]
                    +10*[0]+[2000]+14*[0]
                ))
        plantShare = PlantShareCurverMockup(
                data=numpy.array(50*[1]))
        l = ProductionLoader(productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders)

        l.computeAvailableRights(isodate('2015-08-16'))

        result = rights.rightsPerShare(1,
            isodate('2015-08-16'),
            isodate('2015-08-17'))
        self.assertEqual(list(result),
            +10*[0]+[1000]+14*[0]
            +25*[0]
            )
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-17'), 0),
            ])

    def test_recomputeRights(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([
            (1, isodate('2015-08-15'), 10),
            ])
        rights.updateRightsPerShare(1, isodate('2015-08-11'),
            4*25*[5])

        production = ProductionAggregatorMockUp(
                first=isodate('2015-08-11'),
                last=isodate('2015-08-14'),
                data=numpy.array(
                    +24*[50]+[0] # Same
                    +24*[60]+[0] # Higher
                    +24*[40]+[0] # Lower
                    +23*[70]+[35]+[0] # Higher after lower
                )
            )
        plantShare = PlantShareCurverMockup(
                data=numpy.array(25*4*[10]))

        l = ProductionLoader(
                productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders)

        l.recomputeRights(isodate('2015-08-11'), isodate('2015-08-14'))

        result = rights.rightsPerShare(1,
            isodate('2015-08-11'),
            isodate('2015-08-14'))
        self.assertEqual(list(result),
            +24*[5]+[0] # Same
            +24*[6]+[0] # Higher
            +24*[5]+[0] # Lower
            +12*[5]+11*[7]+[5]+[0] # Higher after lower
            )

        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-15'), -1500),
            ])



# vim: ts=4 sw=4 et
