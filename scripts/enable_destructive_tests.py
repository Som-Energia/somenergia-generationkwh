#!/usr/bin/env python

"""
Sets the current platform as non-production for testing.
Destructive tests use this flag to prevent destructive
tests to be run in a production server by error.

DO NOT RUN IT AGAINST A PRODUCTION SERVER!!
"""

import erppeek
from yamlns import namespace as ns

def loadconfig(filename):
    if filename:
        import imp
        dbconfig = imp.load_source('config',filename)
    else:
        import dbconfig
    return dbconfig

def erp(dbconfig=None):
    if hasattr(erp,'value'):
        return erp.value
    erp.value = erppeek.Client(**dbconfig.erppeek)
    return erp.value

from consolemsg import step, success, error, warn
import click


@click.command(help=__doc__)
@click.option(
    '--config',
    '-C',
    metavar="dbconfig.py",
    default=None,
    help="Force a diferent config file than dbconfig.py",
    )
@click.option(
    '--disable',
    is_flag=True,
    help="Reverses the flag, marks it as production",
    )
def nonproduction(config, disable):
    dbconfig = loadconfig(config)
    O = erp(dbconfig)

    step(__doc__)
    step("Running with this config:\n"+ns(dbconfig.erppeek).dump())
    value = O._execute('res.config','get', 'destructive_testing_allowed', 'Not set')
    step("El flag destructive_testing_allowed ahora esta: {}".format(value))

    if not disable:
        warn("APRIETA CTRL-C SI POR LO QUE SEA ESTAS EN PRODUCCION!!!")
        ignoreme = raw_input("o return para continuar y cagarla: ")
        O.ResConfig.set('destructive_testing_allowed', True)
        success("Flag destructive_testing_allowed set to True")
    else:
        ignoreme = raw_input("Quitando el flag, apreta return para confirmar: ")
        O.ResConfig.set('destructive_testing_allowed', False)
        success("Flag destructive_testing_allowed set to False")
        

    




if __name__=='__main__':
    nonproduction()


