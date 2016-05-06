#!/usr/bin/env python
"""
Manages recipient contracts of kWh rights for a Generation-kWh investor.
"""

import erppeek
import datetime
from consolemsg import step, success
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
    assign = subparsers.add_parser('assign',
        help="set assignment",
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

    for sub in default, expire, assign:
        sub.add_argument(
            '-p','--partner',
            dest='idmode',
            action='store_const',
            const='partner',
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
    for sub in expire, assign:
        sub.add_argument(
            '-r','--ref',
            dest='contractMode',
            action='store_const',
            const='ref',
            default='id',
            help="select contracts by its reference number, "
                "instead of contract database id",
            )
    for sub in default,:
        """
        sub.add_argument(
            '--all',
            action='store_true',
            help='apply it to all members with investments',
            )
        """
        sub.add_argument(
            dest='members',
            nargs='*',
            help='investors of Generation-kWh (see --partner and --number)',
            )
    for sub in expire, assign,:
        sub.add_argument(
            'contract',
            type=int,
            help="contract database id (see also --ref)",
            )
        sub.add_argument(
            'member',
            type=int,
            help="investor of Generation-kWh (see --partner and --number)",
            )
    for sub in assign,:
        sub.add_argument(
            'priority',
            type=int,
            help="a precedence number, ie. a contract with priority 2 has to wait "
                " contracts with priority 1 to access new production.",
            )

    return parser.parse_args(namespace=ns())

def preprocessMembers(members=None,idmode=None):
    """Turns members in which ever format to the ones required by commands"""

    if idmode=="partner":
        idmap = dict(c.GenerationkwhDealer.get_members_by_partners(members))
        return idmap.values()

    if idmode=="code":
        idmap = dict(c.GenerationkwhDealer.get_members_by_codes(members))
        return idmap.values()

    return members

def preprocessContracts(contracts=None,contractMode=None):
    """Turns contracts format into the ones required by commands"""

    if contractMode=="ref":
        idmap = dict(c.GenerationkwhDealer.get_contracts_by_ref(contracts))
        return idmap.values()

    return contracts


def clear(**args):
    c.GenerationkwhAssignment.dropAll()

def list(csv=False,**args):
    """
        List existing assignments.
    """
    def buildcsv(data):
        return u''.join((
            u"\t".join((
                unicode(cell) for cell in line
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
        idmode=None,
        **_):
    member = preprocessMembers([member], idmode)[0]
    step("Markin as expired assignation between contract {} and member {}"
        .format(contract, member))
    c.GenerationkwhAssignment.expire(contract, member)
    success("Done.")

def default(
        members=None,
        force=False,
        idmode=None,
        **_):
    members=preprocessMembers(members, idmode)
    step("Generating default assignments for members: {}".format(
        ','.join(str(i) for i in members)))
    c.GenerationkwhAssignment.createDefaultForMembers(members)
    success("Done.")

def assign(member=None,contract=None,priority=None, idmode=None):
    member = preprocessMembers([member], idmode)[0]
    expire(member=member,contract=contract)
    c.GenerationkwhAssignment.create({
        'member_id': member,
        'contract_id': contract,
        'priority': priority
    })


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



