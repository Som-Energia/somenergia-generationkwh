#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Displays time series from Mongo
"""

import erppeek
import io
import datetime
from consolemsg import step, success, warn, error, fail
from yamlns import namespace as ns

import click

def config(filename):
    if filename:
        import imp
        dbconfig = imp.load_source('config',filename)
    else:
        import dbconfig
    return dbconfig

def erp(dbconfig=None):
    if hasattr(erp,'value'):
        return erp.value
    erp.value = erppeek.Client(**dbconfig.erppeek)
    return erp.value



@click.group()
@click.option(
    '-C','--config',
    metavar="DBCONFIG.py",
    help="explicitly use config file instead dbconfig.py at the binary location",
    )
def mtc(**args):
    """
    Retrieves time series from mongo.
    """
    dbconfig = config(args['config'])
    warn("Arguments:\n{}", ns(args).dump())
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
        selecttype: partner
    rightscorrection:
        collection: generationkwh_rightscorrection
        datafield: rights_kwh
        timefield: datetime
        creationfield: create_at
""")


def getMongoTimeCurve(database, sourceName, filter, firstDate, lastDate, **args):
    dbconfig = config(args.get('config', None))
    source = sources[sourceName]
    c = pymongo.MongoClient(**dbconfig.mongo)
    mongodb = c[database]
    mtc = MongoTimeCurve(
        mongodb,
        source.collection,
        source.timefield,
        source.creationfield,
        )
    if source.get('selecttype',False) == 'int':
        filter = filter and long(filter)

    if source.get('selecttype',False) == 'partner':
        O = erp(dbconfig)
        filter = preprocessMembers(O, [filter], args['idmode'])

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


def preprocessMembers(O,members=None,idmode=None, all=None):
    """Turns members in which ever format to the ones required by commands"""

    if all:
        return c.GenerationkwhAssignment.unassignedInvestors()

    if idmode=="partner":
        idmap = dict(O.GenerationkwhDealer.get_members_by_partners(members))
        return idmap.values()

    if idmode=="code":
        idmap = dict(O.GenerationkwhDealer.get_members_by_codes(members))
        return idmap.values()

    return members

partner_option = click.option(
    '-p','--partner',
    'idmode',
    flag_value='partner',
    help="select members by its partner database id",
    )
number_option = click.option(
    '-n','--number',
    'idmode',
    flag_value='code',
    help="select members by its member code number",
    )
member_option = click.option(
    '-m','--member',
    'idmode',
    flag_value='memberid',
    default=True,
    show_default=True,
    help="select members by its member database id",
    )
config_option = click.option(
    '-C','--config',
    metavar="DBCONFIG.py",
    help="explicitly use config file instead dbconfig.py at the binary location",
    )



@mtc.command()
@click.argument('type', type=click.Choice(sources.keys()))
@click.argument('select', required=False)
@partner_option
@number_option
@member_option
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
def curve(database, type, select, **args):
    """
    Outputs in a tabular format a mongo time curve

    $ scripts/genkwh_production.py curve gisce 501600324

    $ scripts/genkwh_production.py curve production 1
    """
    firstDate = args.get('from', None)
    lastDate = args.get('to',None)
    curve = getMongoTimeCurve(database, type, select, firstDate, lastDate, **args)

    display = dict(
        day = displayDayMatrix,
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
@click.argument('select', required=False)
@partner_option
@number_option
@member_option
@click.option('--output', '-o')
@click.option('--database', '-d', default='somenergia')
@click.option('--from','-f', type=localisodate, default="2016-05-01")
@click.option('--to','-t', type=localisodate, default=str(datetime.date.today()))
def plot(database, type, select, **args):
    "Shows the curve in a plot"
    from genkwh_curve import doPlot

    firstDate = args.get('from', None)
    lastDate = args.get('to',None)
    curve = getMongoTimeCurve(database, type, select, firstDate, lastDate, **args)

    title = '{}-{}'.format(type, select) if select else '{}-all'.format(type)

    doPlot([[title]+list(curve)],firstDate, lastDate)


if __name__ == '__main__':
    mtc(obj={})


# vim: et ts=4 sw=4
