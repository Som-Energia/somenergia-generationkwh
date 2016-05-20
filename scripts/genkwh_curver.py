#! /usr/bin/env python
# -*- coding: utf-8 -*-
from plantmeter.mongotimecurve import MongoTimeCurve
from generationkwh.isodates import isodate
from generationkwh.memberrightsusage import MemberRightsUsage
import pymongo
import csv
from yamlns import namespace as ns
import erppeek
import dbconfig

dbname='generationkwh_test'
def _getter(method,member,start,stop,file):
    curve=method(member,start,stop)
    with open(file, 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(range(1,26)*((isodate(stop)-isodate(start)).days+1))
        spamwriter.writerow(curve)

def usage_getter(member,start,stop,file,idmode):
    erp=erppeek.Client(**dbconfig.erppeek)
    method=erp.GenerationkwhTesthelper.usage
    member= preprocessMembers(erp,[member], idmode=idmode)[0]
    _getter(method,member,start,stop,file)

def curver_getter(member,start,stop,file,idmode):
    erp=erppeek.Client(**dbconfig.erppeek)
    method=erp.GenerationkwhTesthelper.rights_kwh
    member= preprocessMembers(erp,[member], idmode=idmode)[0]
    _getter(method,member,start,stop,file)

def parseArguments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest="subcommand",
        )
    curver = subparsers.add_parser('curver')
    usage = subparsers.add_parser('usage')
    for sub in curver,usage:
        sub.add_argument(
            '-s','--start',
            type=str,
            help="Start date",
            )
        sub.add_argument(
            '-e','--end',
            type=str,
            help="End date",
            )
        sub.add_argument(
            '-f','--file',
            type=str,
            help="Output file",
            )
        sub.add_argument(
            'member',
            type=int,
            help="investor of Generation-kWh (see --partner and --number)",
            )
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
    if args.subcommand == "usage":
        usage_getter(args.member,args.start,args.end,args.file,args.idmode)
    else:
        curver_getter(args.member,args.start,args.end,args.file,args.idmode)

if __name__ == '__main__':
    main()
