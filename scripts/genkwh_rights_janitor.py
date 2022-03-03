# -*- coding: utf-8 -*-

"""
Displays time series from Mongo
"""

import erppeek
import io
import datetime
from consolemsg import step, success, warn, error, fail
import dbconfig
from yamlns import namespace as ns
from plantmeter.isodates import localisodate, toLocal, asUtc, addDays
import pymongo

mongoClient = pymongo.MongoClient(**dbconfig.mongo)

def get_mongo_rights(start, stop, member_id):
    mongodb = mongoClient.somenergia
    start = localisodate(start)
    stop = localisodate(stop)

    filters = {
        'datetime': {
            '$gte': start,
            '$lt': addDays(stop,1)
        },
        "name": member_id,
    }
    from bson.son import SON

    pipeline = [
        # pick the ones matching the filters
        {"$match":
            filters,
        },
        # sort by timestamp, name and new firsts
        {"$sort": SON([
            ("datetime", 1),
            ("name", 1),
            ("create_at", -1),
        ])},
        # group all having the same timestamp and name, pick newest on collission
        {"$group": {
            '_id': {
                "datetime": '$datetime',
                'name': '$name',
            },
            "datetime": {'$first': '$datetime'},
            "usage_kwh": {'$first': "$usage_kwh"}
        }},
        # Suma tots els que tenen el mateix timestamp, diferent nom
        {"$group": {
            '_id': '$datetime',
         'datetime': {'$first': '$datetime'},
            'usage_kwh': {'$sum': '$usage_kwh'},
        }},
    ]
    toLocalDateString = lambda x: datetime.datetime.strftime(toLocal(asUtc(x)), '%Y-%m-%d %H:%M:%S')
    return {
        toLocalDateString(x['datetime']): x['usage_kwh']
        for x in mongodb.memberrightusage.aggregate(pipeline,cursor={},allowDiskUse=True)
    }

