#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manages production plants initialization
"""

import erppeek
import datetime
from consolemsg import step, success, warn, error, fail
import dbconfig
from yamlns import namespace as ns

import click

erp = erppeek.Client(**dbconfig.erppeek)
Mix = erp.GenerationkwhProductionAggregator
Plant = erp.GenerationkwhProductionPlant
Meter = erp.GenerationkwhProductionMeter


@click.group()
def mtc():
    """
    Retrieves time series from mongo.
    """
    privateconfig = ns(dbconfig.erppeek)
    del privateconfig.password
    warn("Using the following configuration {}:\n\n{}\n", dbconfig.__file__, privateconfig.dump())

from plantmeter.isodates import localisodate
from plantmeter.isodates import addDays
from plantmeter.mongotimecurve import MongoTimeCurve
import pymongo

sources = ns.loads("""
    production:
        collection: tm_profile
        datafield: ae
        timefield: utc_gkwh_timestamp
        creationfield: create_date
    production_old: # deprecated
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
    rightscorrection:
        collection: generationkwh_rightscorrection
        datafield: rights_kwh
        timefield: datetime
        creationfield: create_at
""")

@mtc.command()
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
    mtc(obj={})


# vim: et ts=4 sw=4
