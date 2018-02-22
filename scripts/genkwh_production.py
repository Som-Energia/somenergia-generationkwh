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
def aggregator():
    ""

def coloredCheck(enabled):
    return u"\033[32;1m[✓]\033[0m" if enabled else u"\033[31;1m[✗]\033[0m"

@aggregator.command(
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
                

@aggregator.command(
        help="Clear aggregator platftorm objects")
def clear():
    clearAll()

@aggregator.command(
        help="Initialize aggregator objects")
@click.argument('filename')
def init(filename):
    if filename:
       aggr = setupAggregator(ns.load(filename))
       aggr_obj.update_kwh(aggr['id'])

@aggregator.command(
        help="Update aggregator kWh")
@click.argument('filename')
def update_kwh(filename):
    if filename:
       aggr_name=ns.load(filename)['generationkwh']['name']
       aggr_id=getAggregator(aggr_name)
       aggr_obj.update_kwh(aggr_id)

@aggregator.command(
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

@aggregator.command(
   help="Creates a new plant mix")
@click.argument('name')
@click.argument('description')
def addmix(name, description):
    mix = aggr_obj.create(dict(
        name=name,
        description=description,
        enabled=False,
        ))
    print mix.id

@aggregator.command(
   help="Creates a new plant")
@click.argument('mix')
@click.argument('name')
@click.argument('description')
@click.argument('nshares', type=int)
def addplant(mix, name, description, nshares):
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

@aggregator.command(
   help="Creates a new meter")
@click.argument('mix')
@click.argument('plant')
@click.argument('name')
@click.argument('description')
@click.argument('uri')
@click.argument('lastcommit',
    default='',
    )

def addmeter(mix, plant, name, description, uri, lastcommit):
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


if __name__ == '__main__':
    aggregator(obj={})


# vim: et ts=4 sw=4
