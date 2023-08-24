#!/usr/bin/env python

import erppeek
import datetime
from consolemsg import step, success, warn
from dateutil.relativedelta import relativedelta
from yamlns import namespace as ns
from generationkwh.isodates import isodate
import click
from generationkwh import __version__

c = None
def erp(config):
    global c
    if c: return
    if config:
        import imp
        dbconfig = imp.load_source('config',config)
    else:
        import dbconfig
    warn("Using server {server} as {user}", **dbconfig.erppeek)
    c = erppeek.Client(**dbconfig.erppeek)


@click.group()
@click.help_option()
@click.version_option(__version__)
@click.option(
    '-C', '--config',
    help="use that DBCONFIG.py as configuration file "
        "instead of default dbconfig.py at script location.",
    metavar='DBCONFIG.py',
    )
@click.pass_context
def cli(ctx, config):
    """
    Manages beneficiary contracts for a Generation kWh investor.
    """
    ctx.obj['cfg']=config



option_partner=click.option(
    '-p','--partner',
    'idmode',
    flag_value='partner',
    help="select members by its partner database id, "
        "instead of member database id",
    )

option_number=click.option(
    '-m','--member',
    'idmode',
    flag_value='memberid',
    default=True,
    help="select members by its member id",
    )

option_number=click.option(
    '-n','--number',
    'idmode',
    flag_value='code',
    help="select members by its member code number, "
        "instead of member database id",
    )

argument_member=click.argument(
    'member',
    type=int,
#    help="investor of Generation-kWh (see --partner and --number)",
    )

argument_members=click.argument(
    'members',
    type=int,
    nargs=-1,
#    help="investors of Generation-kWh (see --partner and --number)",
    )

option_ref=click.option(
    '-r','--ref',
    'contractMode',
    flag_value='ref',
    default='id',
    help="select contracts by its reference number, "
        "instead of contract database id",
    )

argument_contract=click.argument(
    'contract',
    type=int,
#    help="contract database id (see also --ref)",
    )



option_all=click.option(
    '--all',
    is_flag=True,
    help='apply it to all members with investments',
    )
option_effectiveon = click.option(
    '--effectiveon',
    type=isodate,
    metavar='YYYY-MM-DD',
    help="filter out investments still not effective at the indicated "
        "ISO date",
    )
option_purchaseduntil = click.option(
    '--purchaseduntil',
    type=isodate,
    metavar='YYYY-MM-DD',
    help="filter out investments purchased after "
        "the indicated ISO date",
    )
option_force = click.option(
    '--force',
    is_flag=True,
    help="even if an assigment already exists ",
    )
option_insist = click.option(
    '--insist',
    is_flag=True,
    help="even if the notification has been sent",
    )
option_mail = click.option(
    '--mail',
    is_flag=True,
    help='send notification email',
    )
argument_priority = click.argument(
    'priority',
    type=int,
#    help="a precedence number, ie. a contract with priority 2 "
#        "has to wait contracts with priority 1 to access "
#        "new production.",
    )


def preprocessMembers(members=None,idmode=None, all=None, effectiveon=None,
        purchaseduntil=None, force=False, insist=False):

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


@cli.command()
@click.confirmation_option(
    prompt="This will sublimate the all the assignments of all investments",
    )
@click.confirmation_option(
    prompt="Pero estas seguro de verdad de la buena?",
    )
def clear(**args):
    "clear assignment objects"
    c.GenerationkwhAssignment.dropAll()


@cli.command('list')
@argument_members
@option_partner
@option_number
@click.pass_context
def _list(ctx, members=None,idmode=None,csv=False):
    "list assignments"

    erp(ctx.obj['cfg'])
    members=preprocessMembers(members, idmode)
    assigments = []
    if members:
        assigments = c.GenerationkwhAssignment.search([
            ('member_id', 'in', tuple(members)),
            ])
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
    click.echo(csvdata)


@cli.command()
@option_partner
@option_number
@argument_member
@option_ref
@argument_contract
@click.pass_context
def expire(
        ctx,
        member=None,
        contract=None,
        idmode=None,
        contractMode=None,
        **_):
    "expire assignments"

    erp(ctx.obj['cfg'])
    contract = preprocessContracts([contract], contractMode)[0]
    member = preprocessMembers([member], idmode)[0]
    step("Markin as expired assignation between contract {} and member {}"
        .format(contract, member))
    c.GenerationkwhAssignment.expire(contract, member)
    success("Done.")


@cli.command()
@argument_members
@option_all
@option_partner
@option_number
@option_mail
@option_force
@option_insist
@option_effectiveon
@option_purchaseduntil
@click.pass_context
def prize(
        ctx,
        members=None,
        force=False,
        insist=False,
        idmode=None,
        all=None,
        mail=False,
        effectiveon=None,
        purchaseduntil=None,
        **_):
    erp(ctx.obj['cfg'])
    members=preprocessMembers(members, idmode, all, effectiveon, purchaseduntil, force, insist)
    if mail:
        step("Sending advanced effectiveness notification for members: {}".format(
            ','.join(str(i) for i in members)))
        c.GenerationkwhAssignment.notifyAdvancedEffectiveDate(members)
    else:
        step("(Simulating) Sending advanced effectiveness notification for members: {}".format(
            ','.join(str(i) for i in members)))
        step("Use --mail to send")
    success("Done.")



@cli.command()
@argument_members
@option_all
@option_partner
@option_number
@option_mail
@option_force
@option_insist
@option_effectiveon
@option_purchaseduntil
@click.pass_context
def default(
        ctx,
        members=None,
        force=False,
        insist=False,
        idmode=None,
        all=None,
        mail=False,
        effectiveon=None,
        purchaseduntil=None,
        **_):
    "create contract assignations using by default criteria"

    erp(ctx.obj['cfg'])
    members=preprocessMembers(members, idmode, all, effectiveon, purchaseduntil, force, insist)
    step("Generating default assignments for members: {}".format(
        ','.join(str(i) for i in members)))
    c.GenerationkwhAssignment.createDefaultForMembers(members)
    if mail:
        step("Sending notification mails for members: {}".format(
            ','.join(str(i) for i in members)))
        c.GenerationkwhAssignment.notifyAssignmentByMail(members)
    success("Done.")


@cli.command()
@option_partner
@option_number
@argument_member
@option_ref
@argument_contract
@argument_priority
@click.pass_context
def assign(ctx, member, contract, priority, idmode, contractMode):
    "set assignment"

    erp(ctx.obj['cfg'])
    print "contract:", contract

    member = preprocessMembers([member], idmode)[0]
    contract = preprocessContracts([contract], contractMode)[0]
    expire.callback(member=member,contract=contract)
    step("Assigning contract {} to member {}"
        .format(contract, member))
    result = c.GenerationkwhAssignment.create({
        'member_id': member,
        'contract_id': contract,
        'priority': priority
    })
    click.echo(result)


@cli.command()
@option_effectiveon
@option_purchaseduntil
@option_force
@option_insist
@click.pass_context
def unassigned(ctx, effectiveon=None, purchaseduntil=None, force=False, insist=False):
    "list members with investments but no assigments"

    erp(ctx.obj['cfg'])
    members=preprocessMembers(
        members=[],
        idmode='memberid',
        all=all,
        effectiveon=effectiveon,
        purchaseduntil=purchaseduntil,
        force=force,
        insist=force,
        )
    click.echo(u'\n'.join(str(i) for i in members))


@cli.command()
@click.pass_context
def clean_terminated(ctx):
    "delete assignments from terminated contracts"

    erp(ctx.obj['cfg'])
    assignment_ids = c.GenerationkwhAssignment.search([
        ('contract_id.state', '=', 'baixa')
    ], context={'active_test': False})
    assignments = c.GenerationkwhAssignment.browse(assignment_ids)
    for assignment in assignments:
        contract = assignment.contract_id
        if contract.data_baixa == contract.data_ultima_lectura:
            click.echo("Deleting assignment %s (polissa %s)"
                % (assignment.id, contract.name))
            c.GenerationkwhAssignment.unlink([assignment.id])

if __name__ == '__main__':
    cli(obj={})
    #main()



