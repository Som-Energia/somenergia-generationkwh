#!/usr/bin/env python
"""
Manages recipient contracts of kWh rights for a Generation-kWh investor.
"""

import erppeek
import datetime
from dateutil.relativedelta import relativedelta
import dbconfig
from yamlns import namespace as ns
from generationkwh.isodates import isodate

def parseArgumments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)

    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest='subcommand',
        )
    list = subparsers.add_parser('list',
        help="list assignments",
        )
    expire = subparsers.add_parser('expire',
        help="expire assignments",
        )
    default = subparsers.add_parser('default',
        help="create contract assignations following the by default criteria",
        )
    clear = subparsers.add_parser('clear',
        help="clear investments objects",
        )
    for sub in expire,:
        sub.add_argument('contract')
        sub.add_argument('member')
    for sub in default,:
        """
        sub.add_argument(
            '-n','--number',
            dest='idmode',
            action='store_const',
            const='number',
            default='memberid',
            help="select members by its member code number, "
                "instead member database id",
            )
        sub.add_argument(
            '-p','--partner',
            dest='idmode',
            action='store_const',
            const='partner',
            help="select members by its partner database id, "
                "instead member database id",
            )
        sub.add_argument(
            '--all',
            action='store_true',
            help='apply it to all members with investments',
            )
        sub.add_argument(
            '--force',
            action='store_true',
            help='create even without ',
            )
        """
        sub.add_argument(
            dest='members',
            action='append',
            nargs='*',
            help='investors of Generation-kWh (see --partner and --number)',
            )

    return parser.parse_args(namespace=ns())

def preprocessMembers(args):
    """Turns members in which ever format to the ones required by commands"""

def clear(**args):
    c.GenerationkwhAssignment.dropAll()

def list(csv=False,**args):
    """
        List active investments between start and stop, both included,
        for the member of for any member if member is None.
        If start is not specified, it lists activated before stop.
        If stop is not specified, it list activated and not deactivated
        before start.
        If neither start or stop are specified all investments are listed
        active or not.
    """
    def buildcsv(data):
        return u''.join((
            u"\t".join((
                unicode(c) for c in line
                ))+'\n'
            for line in data))

    csvdata = buildcsv([(
            'member id',
            'priority',
            'contract id',
            'contractref',
            'member name',
            'end_date'
        )]+[
        (
            r['member_id'][0],
            r['priority'],
            r['contract_id'][0],
            r['contract_id'][1],
            r['member_id'][1],
            r['end_date']
        ) for r in c.GenerationkwhAssignment.read([],[
            'member_id',
            'contract_id',
            'priority',
            'end_date'
            ],)
        ])
    if csv: return csvdata
    print csvdata

def expire(
        member=None,
        contract=None,
        **_):
    c.GenerationkwhAssignment.expire([(int(contract),int(member))])

def default(
        members=None,
        force=False,
        **_):
    if force: clear()
    c.GenerationkwhAssignment.createDefaultForMembers(members[0])


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



