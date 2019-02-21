#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manages production plants initialization
"""

import erppeek
import datetime
from consolemsg import step, success, warn, error, fail
from dateutil.relativedelta import relativedelta
import dbconfig
from yamlns import namespace as ns
from generationkwh.isodates import naiveisodate

import click

erp = erppeek.Client(**dbconfig.erppeek)
Mix = erp.GenerationkwhProductionAggregator
Plant = erp.GenerationkwhProductionPlant
Meter = erp.GenerationkwhProductionMeter
Meassures = erp.GenerationkwhProductionMeasurement
Logger = erp.GenerationkwhProductionNotifier

def csv2ts(filename, dtindex, valindex, valtype):
    with open(filename, 'rb') as f:
        return [
                (naiveisodate(row[dtindex]), valtype(row[index]))
                for row in csv.reader(f)
                ]

def clearAll():
    Meter.unlink(Meter.search([]))
    Plant.unlink(Plant.search([]))
    Mix.unlink(Mix.search([]))
    Meassures.unlink(Meassures.search([]))
    Logger.unlink(Logger.search([]))

def setupAggregator(aggr):
    plants = aggr.generationkwh.pop('plants')
    aggr = Mix.create(dict(aggr.generationkwh))

    return dict(
        id = aggr.id,
        plants = [setupPlant(aggr, plant) for plant in plants.items()]
        )

def setupPlant(mix_id, plant):
    plant = plant[1]
    meters = plant.pop('meters')
    plant.update(dict(mix_id=mix_id))
    plant = Plant.create(dict(plant))

    return dict(
        id = plant.id,
        meters = [setupMeter(plant, meter) for meter in meters.items()]
        )

def setupMeter(plant_id, meter):
    meter = meter[1]
    meter.update(dict(plant_id=plant_id))
    return Meter.create(dict(meter))


def getMix(name):
    ids=Mix.search([('name','=',name)])
    if not ids:
        fail("Not such mix '{}'", mix)
    return ids[0] if ids else None

def getPlant(mix, plant):
    mix_id = getMix(mix)

    plant_id = Plant.search([
        ('aggr_id','=',mix_id),
        ('name','=',plant),
        ])

    if not plant_id:
        fail("Not such plant '{}'".format(plant))
    plant_id = plant_id[0]

    return plant_id

def getMeter(mix, plant, meter):
    plant_id = getPlant(mix, plant)

    meter_id = Meter.search([
        ('plant_id','=',plant_id),
        ('name','=',meter),
        ])

    if not meter_id:
        fail("Not such meter '{}'".format(meter))
    meter_id = meter_id[0]

    return meter_id


@click.group()
def production():
    """
    Manages the plant mix to be used in Generation kWh.

    Production of the set of plants which form a plant mix
    has to be aggregated as a single virtual plant.

    Each plant may have several meters, each meter defines
    an url which indicates how to fetch its measures.
    """
    privateconfig = ns(dbconfig.erppeek)
    del privateconfig.password
    warn("Using the following configuration {}:\n\n{}\n", dbconfig.__file__, privateconfig.dump())

def coloredCheck(enabled):
    if enabled:
        return u"\033[32;1m[✓]\033[0m"
    return u"\033[31;1m[✗]\033[0m"

@production.command(
        help="List aggregator platform objects")
def list():
    aggr_ids = Mix.search([])
    aggrs = Mix.read(aggr_ids, [])
    for aggr in aggrs:
        aggr = ns(aggr)
        print u"{enabled_tick} {id} - {name}: \"{description}\" ".format(
            enabled_tick=coloredCheck(aggr.enabled),
            **aggr
            )
        if not aggr.plants: continue
        plants = Plant.read(aggr.plants, [])
        for plant in plants:
            plant = ns(plant)
            print u"\t{enabled_tick} {id} - {name}: \"{description}\" ({nshares} shares)".format(
                enabled_tick=coloredCheck(plant.enabled),
                **plant
                )
            if not plant.meters: continue
            meters = Meter.read(plant.meters, [])
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
    warn("YOU ARE ABOUT TO CLEAR ALL THE DATA RELATED TO GENERATION kWh!!")
    click.confirm('Do you want to continue?', abort=True)
    click.confirm('SERIOUSLY, do you want to continue?', abort=True)
    click.confirm('REALLY REALLY SERIOUSLY, do you want to continue?', abort=True)
    clearAll()

@production.command()
@click.argument('filename')
def init(filename):
    "Initialize aggregator objects"
    if filename:
       aggr = setupAggregator(ns.load(filename))
       Mix.update_kwh(aggr['id'])

@production.command()
@click.argument('filename')
def update_kwh(filename):
    "Update aggregator kWh (deprecated)"
    if filename:
       aggr_name=ns.load(filename)['generationkwh']['name']
       mix_id=getMix(aggr_name)
       Mix.update_kwh(mix_id)

@production.command(
   help="Load measures from meters (unfinished rewrite of update_kwh command)")
@click.argument('meter_path',
    default='',
    )
def load_measures(meter_path):
    # TODO: Unfinished reimplementation of update_kwh
    meterElements = meter_path.split('.')
    mixes = meterElements[0:1]
    plants = meterElements[1:2]
    meters = meterElements[2:3]

    mix_id=getMix(mixes[0])
    Mix.update_kwh(mix_id)

@production.command(
    help="Checks for failed production imports in the last days",
    )
def pull_status():
    twoDaysAgo = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
    step("Checking ftp pulls since {}", twoDaysAgo)

    last_pulls_ids = Logger.search([('date_pull', '>', twoDaysAgo)])
    if not last_pulls_ids and False:
        fail("No data pull for the last 2 days")

    last_pulls = Logger.read(last_pulls_ids)

    last_pulls = [ns(p) for p in last_pulls]
    #print(ns(imports=last_pulls).dump())

    for pull in last_pulls[::-1]:
        pull=ns(pull)
        # avoid conflict among message is the first parameter for error and success
        pull.msg = pull.pop('message') or '' 
        if pull.msg: pull.msg=': '+pull.msg
        if pull.status != 'done':
            error('Pull at {date_pull} from meter {meter_id[0]} failed: {status}{msg}', **pull)
        else:
            success('Pull at {date_pull} from meter {meter_id[0]} successful{msg}', **pull)

    if any(pull.status!='done' for pull in last_pulls):
        fail("Failed pulls detected")
    success("The last imports were successfull")

@production.command()
@click.argument('name')
@click.argument('description')
def addmix(name, description):
    "Creates a new plant mix"
    mix = Mix.create(dict(
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
    mix_id = getMix(mix)
    plant = Plant.create(dict(
        name=name,
        description=description,
        enabled=False,
        aggr_id=mix_id,
        nshares = nshares,
        ))



@production.command()
@click.argument('mix')
@click.argument('plant')
@click.argument('meter')
@click.argument('parameter')
@click.argument('value')
def meterset(mix, plant, meter, parameter, value):
    meter_id = getMeter(mix, plant, meter)
    meter_data = Meter.read(meter_id, [parameter])
    step("Changing meter parameter {} from '{}' to '{}'", parameter, meter_data[parameter], value)
    Meter.write(meter_id, {parameter:value})

@production.command()
@click.argument('mix')
@click.argument('plant')
@click.argument('parameter')
@click.argument('value')
def plantset(mix, plant, parameter, value):
    plant_id = getPlant(mix, plant)
    plant_data = Plant.read(plant_id, [parameter])
    step("Changing plant parameter {} from '{}' to '{}'", parameter, plant_data[parameter], value)
    Plant.write(plant_id, {parameter:value})


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

    plant_id = getPlant(mix, plant)

    if lastcommit == '':
        lastcommit = None
    meter = Meter.create(dict(
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
        timefield: utc_gkwh_timestamp
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
    c = pymongo.MongoClient(**dbconfig.mongo)
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
