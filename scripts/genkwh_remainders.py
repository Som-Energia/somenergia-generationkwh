#!/usr/bin/env python
description = """
Manages remainders of transforming plant production into GkWh rights
to be used as starting point for the next right recomputation.
Remainders are those Wh that do not sum up to a kWh to be used.
Each invesment profile (nshares) has its own remainders.
Remainders are stored with a target date where they will be used.
Ex. A computation up to 2010-01-01, will generate a remainder for
2010-01-02.
"""
import erppeek
import dbconfig
from yamlns import namespace as ns
from consolemsg import success, step, fail, warn

def parseArgumments():
    import argparse
    parser = argparse.ArgumentParser(description=description)

    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest='subcommand',
        )
    active = subparsers.add_parser('active',
        help="list current remainders",
        )
    listall = subparsers.add_parser('listall',
        help="list all remainders",
        )
    init = subparsers.add_parser('init',
        help="initialize remainders",
        )
    pop = subparsers.add_parser('pop',
        help="removes the remainders for the last date",
        )
    update = subparsers.add_parser('update',
        help="writes the remainders from a file",
        )
    clear = subparsers.add_parser('clear',
        help="clear remainders objects",
        )
    for sub in update,:
        sub.add_argument(
            dest='infile',
            metavar='FILE.csv',
            help='space separated values file with rows: nshares isodate Wh',
            )
    for sub in init,: 
        sub.add_argument(
            '--nshares',
            dest='nshares',
            type=int,
            metavar='NSHARES',
            help="number of shares",
            ),
        sub.add_argument(
            '--start',
            dest='start',
            type=str,
            metavar='START',
            help="start date"
            )
    return parser.parse_args(namespace=ns())

def active():
    Remainder = c.GenerationkwhRemainderTesthelper
    for nshares, day, remainderWh in sorted(Remainder.lastRemainders()):
        print nshares, day, remainderWh

def listall():
    Remainder = c.GenerationkwhRemainder
    remainders_id = Remainder.search([])
    remainders = Remainder.read(
            remainders_id,
            ['n_shares', 'target_day', 'remainder_wh']
            )

    for remainder in remainders:
        print remainder['n_shares'], \
              remainder['target_day'], \
              remainder['remainder_wh']

def init(start=None, nshares=None):
    Remainder = c.GenerationkwhRemainder
    Remainder.updateRemainders(
            [(n, start, 0)
                for n in range(1,nshares)])
def clear():
    Remainder = c.GenerationkwhRemainder
    Remainder.clean()

def update(infile):
    import io
    with io.open(infile) as f:
        remainders = [
            (int(nshares), targetDay, int(wh))
            for nshares, targetDay, wh
            in (line.split() for line in f)
        ]
    Remainder = c.GenerationkwhRemainder
    Remainder.updateRemainders(remainders)

def pop():
    Remainder = c.GenerationkwhRemainder
    Helper = c.GenerationkwhRemainderTesthelper
    lastRemainderTarget = max(
        targetDay
        for nshares, targetDay, remainderWh
        in Helper.lastRemainders() or [(0, '2000-01-01', 0)]
    )
    remaindersToPop = Remainder.search([('target_day','=',lastRemainderTarget)])

    remaindersToPop or fail("No remainders left to pop at date {}", lastRemainderTarget)
    step("Removing {} remainders at date {}", len(remaindersToPop), lastRemainderTarget)
    Remainder.unlink(remaindersToPop)
    success("Done")

    


c = erppeek.Client(**dbconfig.erppeek)

def main():
    # Calls the function homonymous to the subcommand
    # with the options as paramteres
    args = parseArgumments()
    warn(args.dump())
    subcommand = args.subcommand
    del args.subcommand
    globals()[subcommand](**args)

if __name__ == '__main__':
    main()
