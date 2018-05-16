#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manages production plants initialization
"""

import erppeek
import datetime
from consolemsg import step, success
from dateutil.relativedelta import relativedelta
import dbconfig
from yamlns import namespace as ns
from generationkwh.isodates import naiveisodate

import click

c = erppeek.Client(**dbconfig.erppeek)
aggr_obj = c.GenerationkwhProductionAggregator
plant_obj = c.GenerationkwhProductionPlant
meter_obj = c.GenerationkwhProductionMeter
meas_obj = c.GenerationkwhProductionMeasurement
warn_obj = c.GenerationkwhProductionNotifier


def csv2ts(filename, dtindex, valindex, valtype):
    with open(filename, 'rb') as f:
        return [
                (naiveisodate(row[dtindex]), valtype(row[index]))
                for row in csv.reader(f)
                ]

def clearAll():
    meter_obj.unlink(meter_obj.search([]))
    plant_obj.unlink(plant_obj.search([]))
    aggr_obj.unlink(aggr_obj.search([]))
    meas_obj.unlink(meas_obj.search([]))
    warn_obj.unlink(warn_obj.search([]))

def setupAggregator(aggr):
    plants = aggr.generationkwh.pop('plants')
    aggr = aggr_obj.create(dict(aggr.generationkwh))

    return dict(
            id = aggr.id,
            plants = [setupPlant(aggr, plant) for plant in plants.items()]
            )

def getAggregator(name):
    ids=aggr_obj.search([('name','=',name)])
    return ids[0] if ids else None

def setupPlant(aggr_id, plant):
    plant = plant[1]
    meters = plant.pop('meters')
    plant.update(dict(aggr_id=aggr_id))
    plant = plant_obj.create(dict(plant))

    return dict(
            id = plant.id,
            meters = [setupMeter(plant, meter) for meter in meters.items()]
            )

def setupMeter(plant_id, meter):
    meter = meter[1]
    meter.update(dict(plant_id=plant_id))
    return meter_obj.create(dict(meter))


@click.group()
def production():
    "Manages production mixes"

def coloredCheck(enabled):
    return u"\033[32;1m[✓]\033[0m" if enabled else u"\033[31;1m[✗]\033[0m"

@production.command(
        help="List aggregator platform objects")
def list():
    aggr_ids = aggr_obj.search([])
    aggrs = aggr_obj.read(aggr_ids, [])
    for aggr in aggrs:
        aggr = ns(aggr)
        print u"{enabled_tick} {id} - {name}: \"{description}\" ".format(
            enabled_tick=coloredCheck(aggr.enabled),
            **aggr
            )
        if not aggr.plants: continue
        plants = plant_obj.read(aggr.plants, [])
        for plant in plants:
            plant = ns(plant)
            print u"\t{enabled_tick} {id} - {name}: \"{description}\" ({nshares} shares)".format(
                enabled_tick=coloredCheck(plant.enabled),
                **plant
                )
            if not plant.meters: continue
            meters = meter_obj.read(plant.meters, [])
            for meter in meters:
                meter=ns(meter)
                print u"\t\t{enabled_tick} {id} - {name}: \"{description}\"".format(
                    enabled_tick=coloredCheck(meter.enabled),
                    **meter
                    )
                print u"\t\t\t{uri}".format(**meter)
                print u"\t\t\tLast Commit: {lastcommit}".format(**meter)
                #print plant.dump()


@production.command()
def clear():
    "Clear aggregator platftorm objects"
    clearAll()

@production.command()
@click.argument('filename')
def init(filename):
    "Initialize aggregator objects"
    if filename:
       aggr = setupAggregator(ns.load(filename))
       aggr_obj.update_kwh(aggr['id'])

@production.command()
@click.argument('filename')
def update_kwh(filename):
    "Update aggregator kWh"
    if filename:
       aggr_name=ns.load(filename)['generationkwh']['name']
       aggr_id=getAggregator(aggr_name)
       aggr_obj.update_kwh(aggr_id)

@production.command(
   help="Load measures from meters")
@click.argument('meter_path',
    default='',
    )
def load_measures(meter_path):
    # TODO: Unfinished reimplementation of update_kwh
    meterElements = meter_path.split('.')
    mixes = meterElements[0:1]
    plants = meterElements[1:2]
    meters = meterElements[2:3]

    aggr_id=getAggregator(mixes[0])
    aggr_obj.update_kwh(aggr_id)

@production.command()
@click.argument('name')
@click.argument('description')
def addmix(name, description):
    "Creates a new plant mix"
    mix = aggr_obj.create(dict(
        name=name,
        description=description,
        enabled=False,
        ))
    print mix.id

@production.command()
@click.argument('mix')
@click.argument('name')
@click.argument('description')
@click.argument('nshares', type=int)
def addplant(mix, name, description, nshares):
    "Creates a new plant"
    aggr_id = aggr_obj.search([
        ('name','=',mix),
        ])

    if not aggr_id:
        fail("Not such mix '{}'", mix)

    aggr_id = aggr_id[0]

    plant = plant_obj.create(dict(
        name=name,
        description=description,
        enabled=False,
        aggr_id=aggr_id,
        nshares = nshares,
        ))

@production.command()
@click.argument('mix')
@click.argument('plant')
@click.argument('name')
@click.argument('description')
@click.argument('uri')
@click.argument('lastcommit',
    default='',
    )
def addmeter(mix, plant, name, description, uri, lastcommit):
    "Creates a new meter"

    aggr_id = aggr_obj.search([
        ('name','=',mix),
        ])

    if not aggr_id:
        fail("Not such mix '{}'", mix)
    aggr_id = aggr_id[0]

    plant_id = plant_obj.search([
        ('aggr_id','=',aggr_id),
        ('name','=',plant),
        ])

    if not plant_id:
        fail("Not such plant '{}'", mix)
    plant_id = plant_id[0]

    if lastcommit == '':
        lastcommit = None
    meter = meter_obj.create(dict(
        plant_id=plant_id,
        name=name,
        description=description,
        uri=uri,
        lastcommit=lastcommit,
        enabled=False,
        ))

from plantmeter.isodates import localisodate
from plantmeter.isodates import addDays
from plantmeter.mongotimecurve import MongoTimeCurve
import pymongo

sources = ns.loads("""
    gisce:
        collection: tm_profile
        datafield: ae
        timefield: timestamp
        creationfield: create_date
    production:
        collection: generationkwh.production.measurement
        datafield: ae
        timefield: datetime
        creationfield: create_at
    rightspershare:
        collection: rightspershare
        datafield: rights_kwh
        timefield: datetime
        creationfield: create_at
    memberrightusage:
        collection: memberrightusage
        datafield: usage_kwh
        timefield: datetime
        creationfield: create_at
        intname: true
""")

@production.command()
@click.argument('type', type=click.Choice(sources.keys()))
@click.argument('name', required=False)
@click.option('--database', '-d', default='somenergia')
@click.option('--from','-f', type=localisodate, default="2016-05-01")
@click.option('--to','-t', type=localisodate, default=str(datetime.date.today()))
def curve(database, type, name, **args):
    """
    Outputs in a tabular format a mongo time curve

    $ scripts/genkwh_production.py curve gisce 501600324

    $ scripts/genkwh_production.py curve production 1
    """

    source = sources[type]
    c = pymongo.MongoClient()
    mongodb = c[database]
    mtc = MongoTimeCurve(
        mongodb,
        source.collection,
        source.timefield,
        source.creationfield,
        )
    curve = mtc.get(
        start=args.get('from',None),
        stop=args.get('to',None),
        filter=None if name is None else long(name) if source.get('intname',False) else name,
        field=source.datafield,
        )
    import numpy
    for day, measures in enumerate(numpy.reshape(curve,(-1,25))):
        print addDays(args['from'],day).date(),
        for x in measures:
            print format(x, ' 5d'),
        print format(sum(measures), ' 7d')

    print "Total", sum(curve)





if __name__ == '__main__':
    production(obj={})


# vim: et ts=4 sw=4
