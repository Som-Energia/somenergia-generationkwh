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

def asUtc(date):
    if date.tzinfo is None:
        return pytz.utc.localize(date)
    return date.astimezone(pytz.utc)

def toLocal(date):
    tz = pytz.timezone('Europe/Berlin')
    if date.tzinfo is None:
        return tz.localize(date)
    return date.astimezone(tz)


def dateToCurveIndex(start, localTime):
    ndays = (localTime.date()-start.date()).days
    winterOffset = 0 if localTime.dst() else 1
    return localTime.hour + 25*ndays + winterOffset

def curveIndexToDate(start, index):
    return start
   


class MongoTimeCurve(object):
    """Consolidates curve data in a mongo database"""

    def __init__(self, mongodb, collection):
        ""
        self.db = mongodb
        self.collectionName = collection
        self.collection = self.db[collection]

    def get(self, start, stop, filter, field):
        start = toLocal(start)
        stop = toLocal(stop)
        ndays = (stop-start).days+1
        data = numpy.zeros(ndays*25, numpy.int)
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
            summerOffset = 1 if localTime.dst() else 0
            timeindex = (
                +summerOffset
                +25*(localTime.date()-start.date()).days
                +localTime.hour
                )
            data[timeindex]=point.get(field)
        return data

    def fillPoint(self, **data):
        for requiredField in ('name', 'datetime'):
            if requiredField not in data:
                raise Exception("Missing '{}'".format(requiredField))

        # TOBEREMOVED: handle naive dates, NO DST SAFE!!
        data['datetime'] = toLocal(data['datetime'])

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


# vim: et ts=4 sw=4
