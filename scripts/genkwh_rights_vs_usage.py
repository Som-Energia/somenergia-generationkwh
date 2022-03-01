#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Displays time series from Mongo
"""

import erppeek
import io
import datetime
from consolemsg import step, success, warn, error, fail
import dbconfig
from yamlns import namespace as ns

import click

def erp():
    if not hasattr(erp, 'inner'):
        erp.inner = erppeek.Client(**dbconfig.erppeek)
    return erp.inner

@click.group()
def mtc():
    """
    Retrieves time series from mongo.
    """
    privateconfig = ns(dbconfig.erppeek)
    del privateconfig.password
    warn("Using the following configuration {}:\n\n{}\n", dbconfig.__file__, privateconfig.dump())

def get_right_in_invoice(date_from, date_to, partner_id=None):
    #TODO: cridar la Custom Search
    pass

def do():
    #Comprovar si hi ha partner
    #Comprovar si hi ha inversions actives i llistar-les
    #Comprovar si té assignacions a contractes i si estan actius (llista)
    #Comprovar drets gastats a Mongo
    #Comprovar drets gastats a les factures

if __name__ == '__main__':
    do(obj={})


# vim: et ts=4 sw=4
