#!/usr/bin/env python
description = """
Generates remainders 
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
        help="list remainders",
        )
    init = subparsers.add_parser('init',
        help="initialize remainders",
        )
    clear = subparsers.add_parser('clear',
        help="clear remainders objects",
        )
    for sub in init,: 
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
            )
    return parser.parse_args(namespace=ns())

def listactive():
    remainder_obj = c.GenerationkwhRemainder
    remainders_id = remainder_obj.search([])
    remainders = remainder_obj.read(
            remainders_id,
            ['n_shares', 'target_day', 'remainder_wh']
            )

    for remainder in remainders:
        print remainder['n_shares'], \
              remainder['target_day'], \
              remainder['remainder_wh']

def init(start=None, nshares=None):
    remainder_obj = c.GenerationkwhRemainder
    remainder_obj.updateRemainders(
            [(n, start, 0)
                for n in range(1,nshares)])
def clear():
    remainder_obj = c.GenerationkwhRemainder
    remainder_obj.clean()

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
