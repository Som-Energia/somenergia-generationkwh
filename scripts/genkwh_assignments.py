#!/usr/bin/env python
"""
Manages recipient contracts of kWh rights for a Generation-kWh investor.
"""

import erppeek
import datetime
from consolemsg import step, success
from dateutil.relativedelta import relativedelta
from yamlns import namespace as ns
from generationkwh.isodates import isodate

def parseArgumments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        '-C', '--config',
        dest='config',
        metavar='DBCONFIG.py',
        help="use that DBCONFIG.py as configuration file "
            "instead of default dbconfig.py at script location.",
        )

    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest='subcommand',
        )
    unassigned = subparsers.add_parser('unassigned',
        help="list members with investments but no assigments",
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
        help="create contract assignations using by default criteria",
        )
    clear = subparsers.add_parser('clear',
        help="clear assignment objects",
        )
    price = subparsers.add_parser('price',
        help="sends the price mail to the pioneers",
        )

    for sub in default, expire, assign, list, price:
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
        sub.add_argument(
            '--all',
            action='store_true',
            help='apply it to all members with investments',
            )
    for sub in default,list,price:
        sub.add_argument(
            dest='members',
            type=int,
            nargs='*',
            help="investors of Generation-kWh (see --partner and --number)",
            )
    for sub in default, unassigned, price:
        sub.add_argument(
            '--effectiveon',
            type=isodate,
            metavar='YYYY-MM-DD',
            help="filter out investments still not effective at the indicated "
                "ISO date",
            )
        sub.add_argument(
            '--purchaseduntil',
            type=isodate,
            metavar='YYYY-MM-DD',
            help="filter out investments purchased after "
                "the indicated ISO date",
            )
        sub.add_argument(
            '--force',
            action='store_true',
            help="even if an assigment already exists ",
            )
        sub.add_argument(
            '--insist',
            action='store_true',
            help="even if the notification has been sent",
            )
    for sub in default,:
        sub.add_argument(
            '--mail',
            action='store_true',
            help='send notification email',
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
            help="a precedence number, ie. a contract with priority 2 "
                "has to wait contracts with priority 1 to access "
                "new production.",
            )

    return parser.parse_args(namespace=ns())

def preprocessMembers(members=None,idmode=None, all=None, effectiveon=None, purchaseduntil=None, force=False, insist=False):
    """Turns members in which ever format to the ones required by commands"""

    if all or effectiveon or purchaseduntil:
        return c.GenerationkwhAssignment.unassignedInvestors(
            effectiveon and str(effectiveon),
            purchaseduntil and str(purchaseduntil),
            force,
            insist,
            )

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

def list(csv=False,members=None,idmode=None,**args):
    """
        List existing assignments.
    """
    members=preprocessMembers(members, idmode)
    assigments = []
    if members:
        assigments = c.GenerationkwhAssignment.search(
            [ ('member_id', 'in', members) ],)
        if not assigments: assigments = [-1]

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
        ) for r in c.GenerationkwhAssignment.read(assigments,[
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
        insist=False,
        idmode=None,
        all=None,
        mail=False,
        effectiveon=None,
        purchaseduntil=None,
        **_):
    members=preprocessMembers(members, idmode, all, effectiveon, purchaseduntil, force, insist)
    step("Generating default assignments for members: {}".format(
        ','.join(str(i) for i in members)))
    c.GenerationkwhAssignment.createDefaultForMembers(members)
    if mail:
        step("Sending notification mails for members: {}".format(
            ','.join(str(i) for i in members)))
        c.GenerationkwhAssignment.notifyAssignmentByMail(members)
    success("Done.")

def assign(member=None,contract=None,priority=None, idmode=None, contractMode=None):
    member = preprocessMembers([member], idmode)[0]
    contract = preprocessContracts([contract], contractMode)[0]
    expire(member=member,contract=contract)
    step("Assigning contract {} to member {}"
        .format(contract, member))
    c.GenerationkwhAssignment.create({
        'member_id': member,
        'contract_id': contract,
        'priority': priority
    })

def unassigned(effectiveon=None, purchaseduntil=None, force=False, insist=False):
    members=preprocessMembers(
        members=[],
        idmode='memberid',
        all=all,
        effectiveon=effectiveon,
        purchaseduntil=purchaseduntil,
        force=force,
        insist=force,
        )
    print u'\n'.join(str(i) for i in members)

c = None

def main():
    import sys
    args = parseArgumments()
    print >> sys.stderr, args.dump()

    if args.config:
        import imp
        dbconfig = imp.load_source('config',args.config)
    else:
        import dbconfig
    del args.config

    global c
    c = c or erppeek.Client(**dbconfig.erppeek)

    # Calls the function homonymous to the subcommand
    # with the options as paramteres
    subcommand = args.subcommand
    del args.subcommand
    globals()[subcommand](**args)

if __name__ == '__main__':
    main()



