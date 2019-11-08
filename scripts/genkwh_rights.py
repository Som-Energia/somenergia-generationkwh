#!/usr/bin/env python
description = """
Generates rights per shares
"""

import datetime
import erppeek
import dbconfig
from yamlns import namespace as ns
from somutils.sequence import sequence

from generationkwh.isodates import isodate
import numpy as np

def datespan(startDate, endDate, delta=datetime.timedelta(days=1)):
    currentDate = startDate
    while currentDate < endDate:
        yield currentDate
        currentDate += delta

def parseArgumments():
    import argparse
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest='subcommand',
        )
    listactive = subparsers.add_parser('listactive',
        help="list rights per share",
        )
    init = subparsers.add_parser('init',
        help="init rights per share",
        )
    clear = subparsers.add_parser('clear',
        help="clear rights per share",
        )
    for sub in init, listactive,:
        sub.add_argument(
            '--nshares',
            dest='nshares',
            type=sequence,
            metavar='NSHARES',
            required=True,
            help="number of shares"
            ),
        sub.add_argument(
            '--start',
            dest='start',
            type=str,
            metavar='START',
            required=True,
            help="start date"
            ),
    for sub in listactive,:
        sub.add_argument(
            '--end',
            dest='end',
            type=str,
            metavar='END',
            help="end date"
            )
    for sub in init,:
        sub.add_argument(
            '--ndays',
            dest='ndays',
            type=int,
            metavar='NDAYS',
            help="number of days"
            ),
        sub.add_argument(
            dest='rights',
            nargs='+',
            help="rights"
            )
    return parser.parse_args(namespace=ns())

def listactive(nshares=None,start=None,end=None):
    genkwh_obj = c.model('generationkwh.testhelper')
    rights = genkwh_obj.rights_per_share(nshares, start, end)
    start=isodate(start)
    end=isodate(end)
    ndays=(end-start).days+1
    rights=np.reshape(rights,(ndays,25))
    dates=datespan(start,end)
    for _date,_rights in zip(dates,rights):
        print _date,_rights

def init(rights=None,start=None,ndays=None,nshares=None):
    rights=[int(r) for r in rights]
    rights=np.tile(np.array(rights), ndays)
    c.GenerationkwhTesthelper.setup_rights_per_share(
        nshares, start, rights.tolist())

def clear():
    genkwh_obj = c.model('generationkwh.testhelper')
    genkwh_obj.clear_mongo_collections(['rightspershare'])
 
c = erppeek.Client(**dbconfig.erppeek)

def main():
    # Calls the function homonymous to the subcommand
    # with the options as paramteres
    args = parseArgumments()
    print args.dump()
    subcommand = args.subcommand
    del args.subcommand
    globals()[subcommand](**args)

if __name__ == '__main__':
    main()
