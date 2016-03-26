#!/usr/bin/env python

import pymongo
from yamlns import namespace as ns
import numpy
import datetime
import pytz

"""
+ More than one meassure
+ Different name ignored
+ Priority for newer meassuers the same hour
+ Summer daylight
+ Check mandatory fields
+ last meassure
+ first meassure
+ remove urlparse dependency on backends
- Properly detect summer daylight change
- lastFullDate: proper implementation

"""

tz = pytz.timezone('Europe/Madrid')

def asUtc(date):
    if date.tzinfo is None:
        return pytz.utc.localize(date)
    return date.astimezone(pytz.utc)

def toLocal(date):
    if date.tzinfo is None:
        return tz.localize(date)
    return date.astimezone(tz)

def parseLocalTime(string, isSummer=False):
    naive = datetime.datetime.strptime(string,
        "%Y-%m-%d %H:%M:%S")
    localized = tz.localize(naive)
    if not isSummer: return localized
    if localized.dst(): return localized
    onehour = datetime.timedelta(hours=1)
    lesser = tz.normalize(localized-onehour)
    return lesser if lesser.dst() else localized

"""
- Spain daylight:
    - UTC offset
        - +1h in winter
        - +2h in summer
    - Hourly curves have
        - an padding to the left in winter: _ X X X ... X X
        - an padding to the right in summer: X X X ... X _
    - Summer to winter is last sunday of october
        - that day has no padding in neither side
        - It has two 2:00h, a summer and a winter one
    - Winter to summer is last sunday of march
        - that day has paddings on both sides
        - It has no 2:00h, next to winter 1:00h is summer 3:00h
"""


def dateToCurveIndex(start, localTime):
    """
        Maps a timezoned datetime to a hourly curve index starting
        at 'start' date. Time part of 'start' is ignored.
        Both times' timezone should match curve's timezone.

        A day in houry curve has 25 positions. Padding is added
        to keep same solar time in the same position across summer
        daylight saving shift.
    """
    ndays = (localTime.date()-start.date()).days
    winterOffset = 0 if localTime.dst() else 1
    return localTime.hour + 25*ndays + winterOffset

def addDays(date, ndays):
    resultday = date.date() + datetime.timedelta(days=ndays)
    naiveday = datetime.datetime.combine(resultday, datetime.time(0,0,0))
    return toLocal(naiveday)


def curveIndexToDate(start, index):
    """
        Maps an index withing an hourly curve starting at 'start' date
        into a local date.

        A day in houry curve has 25 positions. Padding is added
        to keep same solar time in the same position across summer
        daylight saving shift.
    """
    days = index//25
    localday = addDays(start, days)

    nextDay = tz.normalize(localday + datetime.timedelta(days=1))
    toWinterDls = localday.dst() and not nextDay.dst()
    toSummerDls = not localday.dst() and nextDay.dst()

    if not localday.dst(): index-=1
    hours = index%25
    if hours == 24 and not toWinterDls: return None
    if hours == 23 and toSummerDls: return None
    return tz.normalize(localday+datetime.timedelta(hours=hours))
   


class MongoTimeCurve(object):
    """Consolidates curve data in a mongo database"""

    def __init__(self, mongodb, collection):
        ""
        self.db = mongodb
        self.collectionName = collection
        self.collection = self.db[collection]

    def get(self, start, stop, filter, field, filling=None):

        assert start.tzinfo is not None, (
            "MongoTimeCurve.get called with naive (no timezone) start date")

        assert stop.tzinfo is not None, (
            "MongoTimeCurve.get called with naive (no timezone) stop date")

        ndays = (stop-start).days+1
        data = numpy.zeros(ndays*25, numpy.int)
        if filling :
            filldata = numpy.zeros(ndays*25, numpy.bool)
        filters = dict(
            name = filter,
            datetime = {
                '$gte': start,
                '$lte': stop+datetime.timedelta(days=1)
            }
        )

        for x in (self.collection
                .find(filters, [field,'datetime'])
                .sort('create_at',pymongo.ASCENDING)
                ):
            point = ns(x)
            localTime = toLocal(asUtc(point.datetime))
            timeindex = dateToCurveIndex (start, localTime)
            data[timeindex]=point.get(field)
            if filling: filldata[timeindex]=True

        if filling: return data, filldata
        return data

    def fillPoint(self, **data):
        for requiredField in ('name', 'datetime'):
            if requiredField not in data:
                raise Exception("Missing '{}'".format(requiredField))

        assert data['datetime'].tzinfo is not None, (
            "MongoTimeCurve.fillPoint with naive (no timezone) datetime")

        counter = self.db['counters'].find_and_modify(
            {'_id': self.collectionName},
            {'$inc': {'counter': 1}}
        )
        data.update(
            create_at = datetime.datetime.now()
            )
        return self.collection.insert(data)

    def _firstLastDate(self, name, first=False):
        """returns the date of the first or last item of a given name"""
        order = pymongo.ASCENDING if first else pymongo.DESCENDING
        for point in (self.collection
                .find(dict(name=name))
                .sort('datetime', order)
                .limit(1)
                ):
            return toLocal(datetime.datetime.combine(
                ns(point).datetime.date(),
                datetime.time(0,0,0)))

        return None

    def firstDate(self, name):
        """returns the date of the first item of a given name"""
        return self._firstLastDate(name, first=True)

    def lastDate(self, name):
        """returns the date of the last item of a given name"""
        return self._firstLastDate(name)

    def lastFullDate(self,name):
        # TODO: dumb implementation, if there is a single point consider it filled
        return self.lastDate(name)

    def update(self, start, filter, field, data):
        """Updates the curve with new data"""

        assert start.tzinfo is not None, (
            "MongoTimeCurve.update called with naive (no timezone) start date")

        stop = start + datetime.timedelta(days=len(data)//25+1)
        oldData, filling = self.get(start, stop, filter, field, filling=True)
        for i,(bin,old,f) in enumerate(zip(data,oldData,filling)):
            curveDate = curveIndexToDate(start, i)
            if curveDate is None: continue
            if bin == old: continue
            self.fillPoint(
                datetime=curveDate,
                name=filter,
                **dict([(field, bin)])
                )



# vim: et ts=4 sw=4
