#! /usr/bin/env python
# -*- coding: utf-8 -*-
from plantmeter.mongotimecurve import MongoTimeCurve
from generationkwh.isodates import isodate
from generationkwh.memberrightsusage import MemberRightsUsage
import pymongo
import csv
from yamlns import namespace as ns
from sequence import sequence
import datetime
import erppeek

dbname='generationkwh_test'

def doPlot(columns, first, last):
    from pyqtgraph.Qt import QtGui, QtCore
    import numpy as np
    import pyqtgraph as pg
    import pyqtgraph.exporters
    import itertools

    pg.setConfigOptions(
        antialias=True,
        background='w',
        foreground='k',
        )
    app = QtGui.QApplication([])

    win = pg.GraphicsWindow(title="Curve plotter")
    win.setWindowTitle('Curve plotter')

    plot = win.addPlot(title="Rights and Usage")
    ndays=(last-first).days+1
    timeAxis = plot.getAxis('bottom')
    timeAxis.setTicks([[
        (i*25, first+datetime.timedelta(days=i))
        for i in xrange(ndays)
        ],[
        (i, i%25)
        for i in xrange(25*ndays)
        ]])
    timeAxis.setStyle(
        tickTextHeight=390,
        )
    timeAxis.setGrid(100)

    plot.addLegend()
    for i,column in enumerate(columns):
        plot.plot(np.array(column[1:]),
            pen=pg.intColor(i),
            name=column[0],
            symbol='o',
            symbolBrush=pg.intColor(i),
            )

    win.show()
    app.exec_()

def compute(member, first, last, output=None, idmode='memberid', shares=None, show=False, **args):
    config = args.get('config',None)
    if config:
        import imp
        dbconfig=imp.load_source('dbconfig',config)
    else:
        import dbconfig

    erp = erppeek.Client(**dbconfig.erppeek)
    member = preprocessMembers(erp,[member], idmode=idmode)[0]
    first, last = str(first), str(last)
    columns=[]
    if args.get('dumpMemberShares',False):
        columns.append(['memberShares']+
            erp.GenerationkwhTesthelper.member_shares(
                member, first, last))
    if args.get('dumpRights',True):
        columns.append(['rights']+
            erp.GenerationkwhTesthelper.rights_kwh(
                member, first, last))
    if args.get('dumpUsage',True):
        columns.append(['usage']+
            erp.GenerationkwhTesthelper.usage(
                member, first, last))
    if shares:
        for n in shares:
            columns.append(['{}share'.format(n)]+
                erp.GenerationkwhTesthelper.rights_per_share(
                    n, first, last))

    return columns


def plot(member, first, last,
        output=None, idmode='memberid', shares=None, show=False, **args):

    columns = compute(
        member, first, last,
        output, idmode, shares, show,
        **args)

    doPlot(columns, first, last)

def dump(member, first, last,
        output=None, idmode='memberid', shares=None, show=False, **args):

    columns = compute(
        member, first, last,
        output, idmode, shares, show,
        **args)

    if show: doPlot(columns, first, last)

    csv = "\n".join((
        '\t'.join(str(item) for item in row)
        for row in zip(*columns)
        ))

    if args.get('returnCsv', False):
        return csv

    if output is None:
        print csv
    else:
        with open(output,'w') as f:
            f.write(csv)




def parseArguments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest="subcommand",
        )
    dump = subparsers.add_parser('dump',
        help="dumps the curves as csv"
        )
    plot = subparsers.add_parser('plot',
        help="shows curves in a plot window")
    init = subparsers.add_parser('init',
        help="clears and initializes curves and remainders")
    for sub in init,:
        sub.add_argument(
            'first',
            metavar='FIRSTDATE',
            type=isodate,
            help="First production date (iso format)",
            )
        sub.add_argument(
            'totalshares',
            metavar='BUILTSHARES',
            type=int,
            help="Initial number of built shares",
            )
        sub.add_argument(
            '--shares',
            type=sequence,
            help="besides 1-share curve, init others n-shares"
                "values separated with commas. "
                "You can use hyphen to indicate a range. "
                "Example: 1-3,9 is 1,2,3,9.",
            )
    for sub in dump,plot,init,:
        sub.add_argument(
            '-C','--config',
            dest='config',
            metavar="DBCONFIG.py",
            help="explicitly use config file instead dbconfig.py at the binary location",
            )

    for sub in dump,plot,:
        sub.add_argument(
            'member',
            type=int,
            help="investor of Generation-kWh (see --partner and --number)",
            )
        sub.add_argument(
            'first',
            type=isodate,
            help="Start date (isoformat)",
            )
        sub.add_argument(
            'last',
            type=isodate,
            help="End date (isoformat)",
            )
        sub.add_argument(
            '--output', '-o',
            type=str,
            help="Output file",
            )
        sub.add_argument(
            '-p','--partner',
            dest='idmode',
            action='store_const',
            const='partner',
            default='memberid',
            help="select members by its partner database id, "
                "instead of member database id",
            )
        sub.add_argument(
            '-n','--number',
            dest='idmode',
            action='store_const',
            const='code',
            default='memberid',
            help="select members by its member code number, "
                "instead of member database id",
            )
        sub.add_argument(
            '--shares',
            type=sequence,
            help="adds columns with rights for specified share numbers. "
                "values separated with commas. "
                "You can use hyphen to indicate a range. "
                "Example: 1-3,9 is 1,2,3,9.",
            )
        sub.add_argument(
            '--membershares',
            dest='dumpMemberShares',
            action='store_true',
            help="append member usage column. ",
            )
        sub.add_argument(
            '--nousage',
            dest='dumpUsage',
            action='store_false',
            help="do not append member usage column. ",
            )
        sub.add_argument(
            '--norights',
            dest='dumpRights',
            action='store_false',
            help="do not append member rights column. ",
            )
            

    return parser.parse_args(namespace=ns())

def preprocessMembers(erp,members=None,idmode=None, all=None):
    """Turns members in which ever format to the ones required by commands"""

    if all:
        return c.GenerationkwhAssignment.unassignedInvestors()

    if idmode=="partner":
        idmap = dict(erp.GenerationkwhDealer.get_members_by_partners(members))
        return idmap.values()

    if idmode=="code":
        idmap = dict(erp.GenerationkwhDealer.get_members_by_codes(members))
        return idmap.values()

    return members

def main():
    args = parseArguments()
    print ns(args).dump()
    globals()[args.subcommand](**args)

if __name__ == '__main__':
    main()
