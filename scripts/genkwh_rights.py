#!/usr/bin/env python
description = """
Generates rights per shares
"""

import erppeek
import dbconfig
from yamlns import namespace as ns

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
        help="init rights per sahare",
        )
    clear = subparsers.add_parser('clear',
        help="clear rights per share",
        )
    for sub in init,:
        sub.add_argument(
            '--activeshares',
            dest='activeshares',
            type=int,
            metavar='ACTIVESHARES',
            help="number of active shares"
            ),
        sub.add_argument(
            '--start',
            dest='start',
            type=str,
            metavar='START',
            help="start date"
            ),
        sub.add_argument(
            '--ndays',
            dest='ndays',
            type=int,
            metavar='NDAYS',
            help="number of days"
            ),
        sub.add_argument(
            '--nshares',
            dest='nshares',
            type=int,
            metavar='NSHARES',
            help="number of shares"
            ),
        sub.add_argument(
            dest='production',
            ngargs='*',
            help="production"
            )
    for sub in listactive,:
        sub.add_argument(
            '--nshares',
            dest='nshares',
            type=int,
            metavar='NSHARES',
            help="number of shares"
            ),
        sub.add_argument(
            '--start',
            dest='start',
            type=str,
            metavar='START',
            help="start date"
            ),
        sub.add_argument(
            '--end',
            dest='end',
            type=str,
            metavar='END',
            help="end date"
            )
    return parser.parse_args(namespace=ns())

def listactive(nshares=None,start=None,end=None):
    genkwh_obj = c.GenerationkwhTestHelper
    for rights,start,date in genkwh_obj.rights_per_share(
            nshares,
            start,
            end):
        print nshares,start,end

def init(production=None,activeshares=None,start=None,ndays=None,nshares=None):
    production=np.tile(np.array(production), ndays)
    for nshare in range(nshares):
        rights_per_share=production*nshares/activeshares
        c.GenerationkwhTesthelper.setup_rights_per_share(
            nshare, start, rights_per_share.tolist())

def clear():
    genkwh_obj = c.GenerationkwhTestHelper
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
