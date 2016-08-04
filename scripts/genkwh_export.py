#!/usr/bin/env python

"""
Export kWh from aggregators
"""

import erppeek
import dbconfig

from plantmeter.isodates import isodate 
from dateutil import tz

import pymongo
import click

c = erppeek.Client(**dbconfig.erppeek)
m = pymongo.Connection(*dbconfig.mongo)
mdb = m['somenergia']
collection = mdb['generationkwh.production.measurement']

aggr_obj = c.GenerationkwhProductionAggregator
plant_obj = c.GenerationkwhProductionPlant
meter_obj = c.GenerationkwhProductionMeter
meas_obj = c.GenerationkwhProductionMeasurement
warn_obj = c.GenerationkwhProductionNotifier

from_zone = tz.tzutc()
to_zone = tz.tzlocal()

def get_kwh(meters, start, end):
    search_params = {}

    if meters:
        search_params.update({'name': {'$in': meters}})
    if start:
        start = isodate(start)
        search_params.update({'datetime': {'$gt': start}})
    if end:
        end = isodate(end)
        if 'datetime' in search_params:
            search_params['datetime'].update({'$lt': end})
        else:
            search_params.update({'datetime': {'$lt': end}})

    measures = [x for x in collection.find(
        search_params,
        {'datetime':1, 'ae':1},
        sort=[('datetime', pymongo.ASCENDING)])]

    return [(
        measure['datetime'].replace(tzinfo=from_zone).astimezone(to_zone),
        measure['ae'])
        for measure in measures]

def get(aggregator, start, end):
    search_params = []
    if aggregator:
        search_params = [('id', '=', aggregator)]
    aggrs = aggr_obj.search(search_params)

    meters= [str(meter) for aggr in aggrs
            for plant in aggr_obj.read(aggr, 'plants')
            for meter in plant_obj.read(plant, 'meters')]
    return get_kwh(meters, start, end)

@click.group()
def aggregator():
    ""

@aggregator.command(
        help="Export data from generationkWh")
@click.option('--aggregator', default=None)
@click.option('--start', default=None)
@click.option('--end', default=None)
def export(aggregator, start, end):
    measures = get(aggregator, start, end)
    for measure in measures:
        print measure['datetime'],measure['ai']

if __name__ == '__main__':
    aggregator(obj={})

