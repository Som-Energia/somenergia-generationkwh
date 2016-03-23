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

def tzisodatetime(string):
    tz = pytz.timezone('CET')
    naive = datetime.datetime.strptime(string,
        "%Y-%m-%d %H:%M:%S%Z")
    localized = tz.localize(naive)
    if localized.dst(): return localized
    if not string.endswith('CEST'): return localized

    utcversion = localized.astimezone(pytz.utc)
    onehour = datetime.timedelta(hours=1)

    return (utcversion - onehour).astimezone(tz)

def dloffset(datestring):
    date = tzisodatetime(datestring)
    dstOffset = 0 if date.tzname()=='CEST' else 1
    return dstOffset+date.hour


class MongoTimeCurve(object):
    """Consolidates curve data in a mongo database"""

    def __init__(self, mongodb, collection):
        ""
        self.db = mongodb
        self.collectionName = collection
        self.collection = self.db[collection]

    def get(self, start, stop, filter, field):
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
            monthAndDay = point.datetime.month, point.datetime.day
            summerOffset = 1 if (3,26) < monthAndDay < (10,26) else 0
            timeindex = (
                +summerOffset
                +25*(point.datetime.date()-start.date()).days
                +point.datetime.hour
                )
            data[timeindex]=point.get(field)
        return data

    def fillPoint(self, **data):
        for requiredField in ('name', 'datetime'):
            if requiredField not in data:
                raise Exception("Missing '{}'".format(requiredField))

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
            return datetime.datetime.combine(
                ns(point).datetime.date(),
                datetime.time(0,0,0))

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
