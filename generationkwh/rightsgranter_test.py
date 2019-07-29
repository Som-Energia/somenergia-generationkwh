# -*- coding: utf-8 -*-

from .rightsgranter import RightsGranter
import unittest
import datetime
import pymongo
from .rightspershare import RightsPerShare
from .rightscorrection import RightsCorrection
import numpy

from .isodates import  isodate, localisodate

def zeropad(array, left, right):
    return numpy.pad(array, (left, right), 'constant', constant_values=[0])

# Py3 compatibility. Alternative from future.utils import lrange
def lrange(start, stop=None, step=1):
    if stop is None:
        return list(range(0,start,step))
    return list(range(start, stop, step))

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

        data = self.data[offset:offset+nbins-frontpad-backpad]

        return zeropad(data, frontpad, backpad)

    def getFirstMeasurementDate(self):
        return self.firstDate

    def getLastMeasurementDate(self):
        return self.lastDate

class ProductionAggregatorMockUp_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.p = ProductionAggregatorMockUp(
            first=isodate('2015-08-11'),
            last=isodate('2015-08-15'),
            data=numpy.arange(100),
            )

    def test_getkwh_empyinterval(self):
        result = self.p.get_kwh(
            isodate('2015-08-12'),
            isodate('2015-08-11'),
            )
        self.assertEqual(list(result), [])

    def test_getkwh_singleDate(self):
        result = self.p.get_kwh(
            isodate('2015-08-12'),
            isodate('2015-08-12'),
            )
        self.assertEqual(list(result), lrange(25,50))

    def test_getkwh_beforeData(self):
        result = self.p.get_kwh(
            isodate('2015-08-09'),
            isodate('2015-08-10'),
            )
        self.assertEqual(list(result), 50*[0])

    def test_getkwh_afterData(self):
        result = self.p.get_kwh(
            isodate('2015-08-16'),
            isodate('2015-08-17'),
            )
        self.assertEqual(list(result), 50*[0])

    def test_getkwh_matchingData(self):
        result = self.p.get_kwh(
            isodate('2015-08-11'),
            isodate('2015-08-15'),
            )
        self.assertEqual(list(result), lrange(100))

    def test_getkwh_startInMiddle(self):
        result = self.p.get_kwh(
            isodate('2015-08-12'),
            isodate('2015-08-15'),
            )
        self.assertEqual(list(result), lrange(25,100))

    def test_getkwh_endInMiddle(self):
        result = self.p.get_kwh(
            isodate('2015-08-11'),
            isodate('2015-08-13'),
            )
        self.assertEqual(list(result), lrange(75))

    def test_getkwh_startingBeforeData(self):
        result = self.p.get_kwh(
            isodate('2015-08-10'),
            isodate('2015-08-15'),
            )
        self.assertEqual(list(result), 25*[0]+lrange(100))

    def test_getkwh_startingBeforeDataEndingMiddle(self):
        result = self.p.get_kwh(
            isodate('2015-08-10'),
            isodate('2015-08-13'),
            )
        self.assertEqual(list(result), 25*[0]+lrange(75))

    def test_getkwh_endingAfterData(self):
        result = self.p.get_kwh(
            isodate('2015-08-11'),
            isodate('2015-08-16'),
            )
        self.assertEqual(list(result), lrange(100)+25*[0])

    def test_getkwh_endingAfterDataStartingMiddle(self):
        result = self.p.get_kwh(
            isodate('2015-08-12'),
            isodate('2015-08-16'),
            )
        self.assertEqual(list(result), lrange(25,100)+25*[0])

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


class RightsGranterTest(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.databasename = 'generationkwh_test'

        c = pymongo.MongoClient()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]

    def tearDown(self):
        c = pymongo.MongoClient()
        c.drop_database(self.databasename)


    def assertOlderRemainderEqual(self, remainders, expected):
        l = RightsGranter()
        date = l._olderRemainder([
            (shares, isodate(date), remainderwh)
            for shares, date, remainderwh in remainders
            ])
        self.assertEqual(date and str(date), expected)

    def test_olderRemainder_noremainders(self):
        self.assertOlderRemainderEqual([
            ], None)

    def test_olderRemainder_singleRemainder(self):
        self.assertOlderRemainderEqual([
            (1, '2001-01-01', 45),
            ], '2001-01-01')

    def test_olderRemainder_manyRemainders_takesEarlier(self):
        self.assertOlderRemainderEqual([
            (1, '2001-01-01', 45),
            (2, '2000-01-01', 45),
            ], '2000-01-01')


    def assertDatePairEqual(self, expected, result):
        e1,e2 = expected
        self.assertEqual((isodate(e1),isodate(e2)), result)

    def test_updatableInterval_withNoremainders_takesFirstMeassure(self):
        p = ProductionAggregatorMockUp(
                first=isodate('2000-01-01'),
                last=isodate('2006-01-01'),
                )
        l = RightsGranter(productionAggregator=p)
        interval = l._updatableInterval([])
        self.assertDatePairEqual( ('2000-01-01','2006-01-01'), interval)

    def test_updatableInterval_withSingleRemainders_takesIt(self):
        p = ProductionAggregatorMockUp(
                first=isodate('2000-01-01'),
                last=isodate('2006-01-01'),
                )
        l = RightsGranter(productionAggregator=p)
        interval = l._updatableInterval([
            (1,isodate('2001-01-01'), 45),
            ])
        self.assertDatePairEqual( ('2001-01-01','2006-01-01'), interval)

    def test_updatableInterval_withManyRemainders_takesEarlier(self):
        p = ProductionAggregatorMockUp(
                first=isodate('2000-01-01'),
                last=isodate('2006-01-01'),
                )
        l = RightsGranter(productionAggregator=p)
        interval = l._updatableInterval([
            (1,isodate('2002-01-01'), 45),
            (2,isodate('2001-01-01'), 45),
            ])
        self.assertDatePairEqual( ('2001-01-01','2006-01-01'), interval)

    def test_appendRightsPerShare_singleDay(self):
        l = RightsGranter()
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
        l = RightsGranter()
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
        l = RightsGranter()
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
        l = RightsGranter()
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
        l = RightsGranter()
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
        l = RightsGranter()
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
        l = RightsGranter()
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
        l = RightsGranter()
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
        l = RightsGranter()
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
        l = RightsGranter()
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
        rightsCorrection = RightsCorrection(self.db)
        remainders = RemainderProviderMockup([])
        l = RightsGranter(
            rightsPerShare=rights,
            remainders=remainders,
            rightsCorrection=rightsCorrection,
            )

        l._updateRights(
            nshares=3,
            rights = 50*[1],
            firstDate=isodate('2015-08-16'),
            lastDate=isodate('2015-08-17'),
            remainder=69,
            rightsCorrection = 50*[4]
            )

        result = rights.rightsPerShare(3,
            isodate('2015-08-16'),
            isodate('2015-08-17'))
        self.assertEqual(list(result),
            +24*[1]+[0]
            +24*[1]+[0]
            )

        result = rightsCorrection.rightsCorrection(3,
            isodate('2015-08-16'),
            isodate('2015-08-17'))
        self.assertEqual(list(result),
            +24*[4]+[0]
            +24*[4]+[0]
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
        l = RightsGranter(productionAggregator=production,
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
        l = RightsGranter(productionAggregator=production,
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
        l = RightsGranter(productionAggregator=production,
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
            (1, isodate('2015-08-17'), 0),
            (2, isodate('2015-08-16'), 0),
            ])
        production = ProductionAggregatorMockUp(
                first=isodate('2015-08-16'),
                last=isodate('2015-08-18'),
                data=numpy.array(
                    +25*[1000] # 16
                    +25*[2000] # 17
                    +25*[3000] # 18
                ))
        plantShare = PlantShareCurverMockup(
                data=numpy.array(125*[1]))
        l = RightsGranter(productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders)

        l.computeAvailableRights()

        result = rights.rightsPerShare(1,
            isodate('2015-08-16'),
            isodate('2015-08-19'))
        self.assertEqual(list(result),
            +25*[0] # already generated, untouched
            +24*[2000]+[0]
            +24*[3000]+[0]
            +25*[0] # no production yet
            )
        result = rights.rightsPerShare(2,
            isodate('2015-08-16'),
            isodate('2015-08-19'))
        self.assertEqual(list(result),
            +24*[2*1000]+[0] # generaed for 2 shares
            +24*[2*2000]+[0]
            +24*[2*3000]+[0]
            +25*[0] # no production yet
            )
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-19'), 0),
            (2, isodate('2015-08-19'), 0),
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
        l = RightsGranter(productionAggregator=production,
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

    def test_computeAvailableRights_remainder(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([
            (1, isodate('2015-08-16'), 3),
            ])
        production = ProductionAggregatorMockUp(
                first=isodate('2015-08-16'),
                last=isodate('2015-08-17'),
                data=numpy.array(
                    +10*[0]+[3003]+14*[0]
                    +10*[0]+[5006]+14*[0]
                ))
        plantShare = PlantShareCurverMockup(
                data=numpy.array(2*25*[10]))
        l = RightsGranter(productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders)
        log = l.computeAvailableRights()
        result = rights.rightsPerShare(1,
            isodate('2015-08-16'),
            isodate('2015-08-17'))
        self.assertEqual(list(result),
            +10*[0]+[300]+14*[0]
            +10*[0]+[500]+14*[0]
            )
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-18'), 903),
            ])
        self.assertMultiLineEqual(log,
            "Computing rights for members with 1 shares from 2015-08-16 to 2015-08-17\n"
            "- 3 Wh of remainder from previous days\n"
            "- 800 kWh granted\n"
            "- 903 Wh of remainder for the next days"
        )

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
        l = RightsGranter(productionAggregator=production,
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
        correction = RightsCorrection(self.db)
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

        l = RightsGranter(
                productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders,
                rightsCorrection=correction,
                )

        log = l.recomputeRights(isodate('2015-08-11'), isodate('2015-08-14'))

        result = rights.rightsPerShare(1,
            isodate('2015-08-11'),
            isodate('2015-08-14'))
        self.assertEqual(list(result),
            +24*[5]+[0] # Same
            +24*[6]+[0] # Higher
            +24*[5]+[0] # Lower
            +12*[5]+11*[7]+[5]+[0] # Higher after lower
            )

        result = correction.rightsCorrection(1,
            isodate('2015-08-11'),
            isodate('2015-08-14'))
        self.assertEqual(list(result),
            +24*[0]+[0] # Same
            +24*[0]+[0] # Higher
            +24*[1]+[0] # Lower
            +12*[-2]+11*[0]+[2]+[0] # Higher after lower
            )

        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-15'), -1500),
            ])
        self.assertMultiLineEqual(log,
            "Recomputing rights for members with 1 shares from 2015-08-11 to 2015-08-14\n"
            "- 526 kWh granted\n"
            "- 46 kWh added\n"
            "- 26 kWh kept above the real production\n"
            "- -24 kWh of those could be compensated\n"
            "- 2 kWh substracted as Wh to the next remainder.\n"
        )



# vim: ts=4 sw=4 et
