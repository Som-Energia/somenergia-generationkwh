#!/usr/bin/env python

import pymongo
from yamlns import namespace as ns
import numpy
import datetime

"""
+ More than one meassure
+ Different name ignored
+ Priority for newer meassuers the same hour
+ Summer daylight
+ Check mandatory fields
+ last meassure
+ first meassure
+ remove urlparse dependency on backends
+ Properly detect summer daylight change
- lastFullDate: proper implementation

"""

from .isodates import (
    asUtc,
    toLocal,
    tz,
    addDays,
    )


hoursPerDay=25

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

    sofDay = toLocal(datetime.datetime(localTime.year,
                               localTime.month,
                               localTime.day))
    nextDay = tz.normalize(sofDay + datetime.timedelta(days=1))
    toWinterDls = sofDay.dst() and not nextDay.dst()
    toSummerDls = not sofDay.dst() and nextDay.dst()
    offset = 1 if toWinterDls and not localTime.dst() else (
             -1 if toSummerDls and localTime.dst() else 0)
    return localTime.hour + hoursPerDay*ndays + offset


def curveIndexToDate(start, index):
    """
        Maps an index withing an hourly curve starting at 'start' date
        into a local date.

        A day in houry curve has 25 positions. Padding is added
        to keep same solar time in the same position across summer
        daylight saving shift.
    """
    days = index//hoursPerDay
    localday = addDays(start, days)

    nextDay = tz.normalize(localday + datetime.timedelta(days=1))
    toWinterDls = localday.dst() and not nextDay.dst()
    toSummerDls = not localday.dst() and nextDay.dst()

    hours = index%hoursPerDay
    if hours == 24 and not toWinterDls: return None
    if hours == 23 and toSummerDls: return None
    return tz.normalize(localday+datetime.timedelta(hours=hours))



class MongoTimeCurve(object):
    """Consolidates curve data in a mongo database (old format)"""

    def __init__(self, mongodb, collection,
            timestampField='datetime',
            creationField='create_at',
        ):
        self.db = mongodb
        self.collectionName = collection
        self.collection = self.db[collection]
        self.timestamp = timestampField
        self.creation = creationField

    def get(self, start, stop, filter, field, filling=None):
        assert start.tzinfo is not None, (
            "MongoTimeCurve.get called with naive (no timezone) start date")

        assert stop.tzinfo is not None, (
            "MongoTimeCurve.get called with naive (no timezone) stop date")

        ndays = (stop.date()-start.date()).days+1
        data = numpy.zeros(ndays*hoursPerDay, numpy.int)
        if filling :
            filldata = numpy.zeros(ndays*hoursPerDay, numpy.bool)
        filters = {
            self.timestamp: {
                '$gte': start,
                '$lt': addDays(stop,1)
            }
        }
        if filter: filters.update(name=filter)
        from bson.son import SON

        pipeline = [
            # pick the ones matching the filters
            {"$match":
                filters,
            },
            # sort by timestamp, name and new firsts
            {"$sort": SON([
                (self.timestamp, 1),
                ("name", 1),
                (self.creation, -1),
            ])},
            # group all having the same timestamp and name, pick newest on collission
            {"$group": {
                '_id': {
                    self.timestamp: '$'+self.timestamp,
                    'name': '$name',
                },
                self.timestamp: {'$first': '$'+self.timestamp},
                field: {'$first': '$'+field}
            }},
            # Suma tots els que tenen el mateix timestamp, diferent nom
            {"$group": {
                '_id': '$'+self.timestamp,
                self.timestamp: {'$first': '$'+self.timestamp},
                field: {'$sum': '$'+field},
            }},
        ]

        for x in self.collection.aggregate(pipeline,cursor={},allowDiskUse=True):
            point = ns(x)
            localTime = toLocal(asUtc(point[self.timestamp]))
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
        timestamp = data.pop('datetime')
        data.update({
            self.creation: datetime.datetime.now(),
            self.timestamp: timestamp,
            })
        return self.collection.insert(data)

    def _firstLastDate(self, name, first=False):
        """returns the date of the first or last item of a given name"""
        order = pymongo.ASCENDING if first else pymongo.DESCENDING
        for point in (self.collection
                .find(dict(name=name))
                .sort(self.timestamp, order)
                .limit(1)
                ):
            return toLocal(asUtc(point[self.timestamp])).replace(
                    hour=0,minute=0,second=0)
        return None

    def firstDate(self, name):
        """returns the date of the first item of a given name"""
        return self._firstLastDate(name, first=True)

    def lastDate(self, name):
        """returns the date of the last item of a given name"""
        return self._firstLastDate(name)

    def lastFullDate(self,name):
        # TODO: dumb implementation, having just a single hour considers whole date filled
        return self.lastDate(name)
    def firstFullDate(self,name):
        # TODO: dumb implementation, having just a single hour considers whole date filled
        return self.firstDate(name)

    def update(self, start, filter, field, data):
        """Updates the curve with new data"""

        assert start.tzinfo is not None, (
            "MongoTimeCurve.update called with naive (no timezone) start date")

        stop = start + datetime.timedelta(days=len(data)//hoursPerDay+1)
        oldData, filling = self.get(start, stop, filter, field, filling=True)
        for i,(bin,old,f) in enumerate(zip(data,oldData,filling)):
            curveDate = curveIndexToDate(start, i)
            if curveDate is None: continue
            if bin == old: continue
            self.fillPoint(
                datetime=curveDate,
                name=filter,
                **{field: bin}
                )



# vim: et ts=4 sw=4
