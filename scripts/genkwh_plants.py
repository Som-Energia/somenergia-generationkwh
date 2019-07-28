#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manages production plants initialization
"""

import erppeek
import datetime
from consolemsg import step, success, warn, error, fail, out
import dbconfig
from yamlns import namespace as ns
from generationkwh.isodates import naiveisodate

import click

erp = erppeek.Client(**dbconfig.erppeek)
Mix = erp.GenerationkwhProductionAggregator
Plant = erp.GenerationkwhProductionPlant
Meter = erp.GenerationkwhProductionMeter

def clearAll():
    Meter.unlink(Meter.search([]))
    Plant.unlink(Plant.search([]))
    Mix.unlink(Mix.search([]))

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
        out(u"{enabled_tick} {id} - {name}: \"{description}\" ".format(
            enabled_tick=coloredCheck(aggr.enabled),
            **aggr
            ))
        if not aggr.plants: continue
        plants = Plant.read(aggr.plants, [])
        for plant in plants:
            plant = ns(plant)
            out(u"\t{enabled_tick} {id} - {name}: \"{description}\" ({nshares} shares)".format(
                enabled_tick=coloredCheck(plant.enabled),
                **plant
                ))
            out(u"\t\tFirst active date: {first_active_date}".format(**plant))
            out(u"\t\tLast active date: {last_active_date}".format(**plant))
            if not plant.meters: continue
            meters = Meter.read(plant.meters, [])
            for meter in meters:
                meter=ns(meter)
                out(u"\t\t{enabled_tick} {id} - {name}: \"{description}\"".format(
                    enabled_tick=coloredCheck(meter.enabled),
                    **meter
                    ))
                out(u"\t\t\tFirst active date: {first_active_date}".format(**meter))

@production.command(
        help="Dumps current plant structure as commands to recreate it")
def dump():
    import sys
    aggr_ids = Mix.search([])
    aggrs = Mix.read(aggr_ids, [])
    for aggr in aggrs:
        aggr = ns(aggr)
        out(u"{} addmix {name!r} {description!r}".format(sys.argv[0],**aggr))
        if aggr.enabled:
            out(u"{} setmix {name!r} enabled True".format(sys.argv[0], **aggr))

        if not aggr.plants: continue
        plants = Plant.read(aggr.plants, [])
        for plant in plants:
            plant = ns(plant)
            out(u"{} addplant {mix!r} {name!r} {description!r} {nshares} {first_active_date} {last_active_date}".format(sys.argv[0], mix=aggr.name, **plant))
            if plant.enabled:
                out(u"{} setplant {mix!r} {name!r} enabled True".format(sys.argv[0], mix=aggr.name, **plant))
            if not plant.meters: continue
            meters = Meter.read(plant.meters, [])
            for meter in meters:
                meter=ns(meter)
                out(u"{} addmeter {mix!r} {plant!r} {name!r} {description!r} {first_active_date}"
                    .format(sys.argv[0], mix=aggr.name, plant=plant.name, **meter))
                if meter.enabled:
                    out(u"{} setmeter {mix!r} {plant!r} {name!r} enabled True"
                        .format(sys.argv[0], mix=aggr.name, plant=plant.name, **meter))

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
    success(u"Created mix with id {}".format(mix.id))

@production.command()
@click.argument('mix')
@click.argument('name')
@click.argument('description')
@click.argument('nshares', type=int)
@click.argument('first_active_date', default='')
@click.argument('last_active_date', default='')
def addplant(mix, name, description, nshares, first_active_date, last_active_date):
    "Creates a new plant"
    mix_id = getMix(mix)
    plant = Plant.create(dict(
        name=name,
        description=description,
        enabled=False,
        aggr_id=mix_id,
        nshares = nshares,
        first_active_date=first_active_date,
        last_active_date=last_active_date,
        ))

@production.command()
@click.argument('mix')
@click.argument('plant')
@click.argument('meter')
@click.option('--force', '-f')
def delmeter(mix, plant, meter, force=False):
    "Removes a meter"
    if not force:
        warn("You are about to remove meter {}.{}.{}", mix, plant, meter)
        meter_id = getMeter(mix, plant, meter)
        click.confirm('Do you want to continue?', abort=True)
        click.confirm('SERIOUSLY, do you want to continue?', abort=True)
        click.confirm('REALLY REALLY SERIOUSLY, do you want to continue?', abort=True)
    step("Removing meter {}.{}.{}", mix, plant, meter)
    Meter.unlink(meter_id)

@production.command()
@click.argument('mix')
@click.argument('plant')
@click.option('--force', '-f')
def delplant(mix, plant, force=False):
    "Removes a plant"
    if not force:
        warn("You are about to remove plant {}.{}", mix, plant)
        plant_id = getPlant(mix, plant)
        click.confirm('Do you want to continue?', abort=True)
        click.confirm('SERIOUSLY, do you want to continue?', abort=True)
        click.confirm('REALLY REALLY SERIOUSLY, do you want to continue?', abort=True)
    step("Removing plant {}.{}", mix, plant)
    Plant.unlink(plant_id)

@production.command()
@click.argument('mix')
@click.option('--force', '-f')
def delmix(mix, force=False):
    "Removes a mix"
    if not force:
        warn("You are about to remove mix {}", mix)
        mix_id = getMix(mix)
        click.confirm('Do you want to continue?', abort=True)
        click.confirm('SERIOUSLY, do you want to continue?', abort=True)
        click.confirm('REALLY REALLY SERIOUSLY, do you want to continue?', abort=True)
    step("Removing mix {}", mix)
    Mix.unlink(mix_id)



@production.command()
@click.argument('mix')
@click.argument('plant')
@click.argument('meter')
@click.argument('parameter')
@click.argument('value')
def editmeter(mix, plant, meter, parameter, value):
    "Changes a parameter on the meter"
    meter_id = getMeter(mix, plant, meter)
    meter_data = Meter.read(meter_id, [parameter])
    step("Changing meter parameter {} from '{}' to '{}'", parameter, meter_data[parameter], value)
    Meter.write(meter_id, {parameter:value})

@production.command()
@click.argument('mix')
@click.argument('plant')
@click.argument('parameter')
@click.argument('value')
def editplant(mix, plant, parameter, value):
    "Changes a parameter on the plant"
    plant_id = getPlant(mix, plant)
    plant_data = Plant.read(plant_id, [parameter])
    step("Changing plant parameter {} from '{}' to '{}'", parameter, plant_data[parameter], value)
    Plant.write(plant_id, {parameter:value})


@production.command()
@click.argument('mix')
@click.argument('plant')
@click.argument('name')
@click.argument('description')
@click.argument('first_active_date', default='')
def addmeter(mix, plant, name, description, first_active_date):
    "Creates a new meter"

    plant_id = getPlant(mix, plant)

    if first_active_date == '':
        first_active_date = None
    meter = Meter.create(dict(
        plant_id=plant_id,
        name=name,
        description=description,
        first_active_date=first_active_date,
        enabled=False,
        ))



if __name__ == '__main__':
    production(obj={})


# vim: et ts=4 sw=4
