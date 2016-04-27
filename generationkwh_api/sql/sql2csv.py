#!/usr/bin/env python
#-*- coding: utf8 -*-

import psycopg2
import config
import dbutils
import sys
from consolemsg import step, error, fail, warn
from yamlns import namespace as ns


def main():
    cliargs = ns()
    keyarg = None
    args = []
    for arg in sys.argv[1:]:
        if keyarg:
            cliargs[keyarg]=arg
            continue
        if arg.startswith('--'):
            keyarg = arg[2:]
            continue
        args.append(arg)

    if not args:
        fail("Argument required. Usage:\n"
        "{} <sqlfile> [<yamlfile>] [--<var1> <value1> [--<var2> <value2> ..] ]".format(sys.argv[0]))

    step("Loading {}...".format(args[0]))
    with open(args[0]) as sqlfile:
        query = sqlfile.read()

    variables = ns()
    if len(args)>=2:
        step("Loading variables...".format(args[1]))
        variables = ns.load(args[1])
        warn(variables.dump())
    variables.update(cliargs)

    step("Connecting to the database...")
    db = psycopg2.connect(**config.psycopg)

    with db.cursor() as cursor :
        try:
            cursor.execute(query, variables)
        except KeyError as e:
            fail("Missing variable '{key}'. Specify it in the YAML file or by using the --{key} option"
                .format(key=e.args[0]))
        print dbutils.csvTable(cursor)


main()




