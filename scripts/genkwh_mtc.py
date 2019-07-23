#!/usr/bin/env python
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

import click


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


def getMongoTimeCurve(database, sourceName, filter, firstDate, lastDate):
    source = sources[sourceName]
    c = pymongo.MongoClient(**dbconfig.mongo)
    mongodb = c[database]
    mtc = MongoTimeCurve(
        mongodb,
        source.collection,
        source.timefield,
        source.creationfield,
        )
    if source.get('intname',False):
        filter = filter and long(filter)

    return mtc.get(
        start=firstDate,
        stop=lastDate,
        filter=filter,
        field=source.datafield,
        )

def displayDayMatrix(firstDate, curve):
    import numpy
    return '\n'.join(
        ' '.join([
            str(addDays(firstDate,day).date()),
            ' '.join(
                format(x, ' 5d')
                for x in measures
            ),
            format(sum(measures), ' 6d')
        ])
        for day, measures
        in enumerate(numpy.reshape(curve,(-1,25)))
    ) + "\nTotal {}".format(sum(curve))

def displayDayHourMatrix(firstDate, curve):
    import numpy
    return '\n'.join(
        u' '.join([
            str(addDays(firstDate,day).date()),
            u' '.join(
                format(x, ' 5d')
                for x in measures
            ),
            format(sum(measures), ' 6d')
        ])
        for day, measures
        in enumerate(numpy.reshape(curve,(-1,25)))
    ) + u"\nTotal {}".format(sum(curve))


def displayMonthMatrix(firstDate, curve):
    import numpy
    daily = numpy.sum(numpy.reshape(curve, (-1, 25)), axis=1)
    dates = [ addDays(firstDate, i).date() for i in range(len(daily)) ]
    monthfirst = [
        i
        for i, (date, yesterday)
        in enumerate(zip(dates, [None]+dates))
        if yesterday is None
        or date.month != yesterday.month
    ]
    monthly = numpy.array([
        numpy.sum(month)
        for month
        in numpy.split(daily, monthfirst)
        ])
    return u'\n'.join(
        u'{:%Y-%m} {}'.format(
            addDays(firstDate, idate),
            value,
        )
        for idate, value in zip(monthfirst, monthly)
        )+ u"\nTotal {}\n".format(monthly.sum())

def displayMonthHourMatrix(firstDate, curve):
    import numpy
    daily = numpy.reshape(curve, (-1, 25))
    dates = [ addDays(firstDate, i).date() for i in range(len(daily)) ]
    monthfirst = [
        i
        for i, (date, yesterday)
        in enumerate(zip(dates, [None]+dates))
        if yesterday is None
        or date.month != yesterday.month
    ]
    monthly = numpy.array([
        month.sum(axis=0)
        for month
        in numpy.split(daily, monthfirst)
        ])
    return u'\n'.join(
        u'{:%Y-%m}{} {: 8d}'.format(
            addDays(firstDate, idate),
            ' '.join(format(x,' 7d') for x in value),
            value.sum(),
        )
        for idate, value in zip(monthfirst, monthly)
        )+ u"\nTotal {}\n".format(monthly.sum())



@mtc.command()
@click.argument('type', type=click.Choice(sources.keys()))
@click.argument('name', required=False)
@click.option('--output', '-o')
@click.option('--database', '-d', default='somenergia')
@click.option('--from','-f', type=localisodate, default="2016-05-01")
@click.option('--to','-t', type=localisodate, default=str(datetime.date.today()))
@click.option('--by', type=click.Choice([
    'dayhour',
    'monthhour',
    'day',
    'month',
    ]),
    default='dayhour') 
def curve(database, type, name, **args):
    """
    Outputs in a tabular format a mongo time curve

    $ scripts/genkwh_production.py curve gisce 501600324

    $ scripts/genkwh_production.py curve production 1
    """
    firstDate = args.get('from', None)
    lastDate = args.get('to',None)
    curve = getMongoTimeCurve(database, type, name, firstDate, lastDate)

    display = dict(
        dayhour = displayDayHourMatrix,
        dayhour = displayDayHourMatrix,
        monthhour = displayMonthHourMatrix,
        month = displayMonthMatrix,
    )[args.get('by', 'dayhour')]

    result = display(firstDate, curve)
    output = args.get('output',None)
    print "outputing to {}".format(output)
    if output:
        with io.open(output,'w') as output_file:
            output_file.write(result)
    print result


@mtc.command()
@click.argument('type', type=click.Choice(sources.keys()))
@click.argument('name', required=False)
@click.option('--output', '-o')
@click.option('--database', '-d', default='somenergia')
@click.option('--from','-f', type=localisodate, default="2016-05-01")
@click.option('--to','-t', type=localisodate, default=str(datetime.date.today()))
def plot(database, type, name, **args):
    from genkwh_curve import doPlot

    firstDate = args.get('from', None)
    lastDate = args.get('to',None)
    curve = getMongoTimeCurve(database, type, name, firstDate, lastDate)

    title = '{}-{}'.format(type, name) if name else '{}-all'.format(type)

    doPlot([[title]+list(curve)],firstDate, lastDate)


if __name__ == '__main__':
    mtc(obj={})


# vim: et ts=4 sw=4
