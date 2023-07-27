#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Displays time series from Mongo
python genkwh_rights_vs_usage.py --member-code S036734 --date-from 2017-01-01 --date-to 2090-12-31
"""

from erppeek import Client
import sys
import traceback
from consolemsg import step, success, error
import dbconfig
import argparse
from genkwh_mtc import *
from plantmeter.isodates import localisodate

c = Client(**dbconfig.erppeek)


def showInvestmentData(investment_ids):
    success("Inversions trobades")
    for inv_id in investment_ids:
        inv = c.GenerationkwhInvestment.browse(inv_id)
        step("Inversió {} vàlida des de {} a {} i té {} accions ".format(inv.name, inv.first_effective_date, inv.last_effective_date, inv.nshares))

def showAssignmentsData(assignments_ids):
    success("Assignacions trobades")
    for ass in c.GenerationkwhAssignment.browse(assignments_ids):
        step("Assignació al contracte {} (en estat {}) amb una prioritat de {}".format(ass.contract_id.name, ass.contract_id.state, ass.priority))

def getCurveMongo(member_id, date_from, date_to):
    curve = getMongoTimeCurve('somenergia', 'memberrightusage', member_id, date_from, date_to)
    return sum(curve)

def getInvoiceKwh(member_code, date_from, date_to):
    custom_id = c.IrModelData.get_object_reference(
            'som_generationkwh', 'suma_drets_en_factures_generationkwh'
        )[1]
    member_cs_id = c.IrModelData.get_object_reference(
            'som_generationkwh', 'suma_drets_en_factures_generationkwh_param_0'
        )[1]
    from_cs_id = c.IrModelData.get_object_reference(
            'som_generationkwh', 'suma_drets_en_factures_generationkwh_param_1'
        )[1]
    to_cs_id = c.IrModelData.get_object_reference(
            'som_generationkwh', 'suma_drets_en_factures_generationkwh_param_2'
        )[1]

    c.CustomSearchParam.write(member_cs_id, {'value': member_code})
    c.CustomSearchParam.write(from_cs_id, {'value': date_from})
    c.CustomSearchParam.write(to_cs_id, {'value': date_to})
    result = []
    try:
        # CustomSearchResults read doesn't use the IDs, but if not provided ERPPeek fails
        # in the read. So we put a dummy list to make it work :)
        result = c.CustomSearchResults.read([1, 2, 3], [], context={'search_id': custom_id})
    except:
        warn("No hem trobat factures amb Generationkwh")
        return 0

    return sum([x['kWh assignats'] for x in result])

def  main(member_code, date_from, date_to):
    #Comprovar si hi ha partner
    member_id = c.SomenergiaSoci.search([('ref','=',member_code)])
    if not member_id:
        raise Exception("No s'ha atrobat el codi indicat")
    member_id = member_id[0]

    #Comprovar si hi ha inversions actives i llistar-les
    investment_ids = c.GenerationkwhInvestment.search([('member_id','=',member_id),('emission_id.type','=','genkwh')])
    if not investment_ids:
        raise Exception("No s'han trobat inversions")
    showInvestmentData(investment_ids)

    #Comprovar si té assignacions a contractes i si estan actius (llista)
    assgnments_id = c.GenerationkwhAssignment.search([('member_id','=',member_id)], context={'active_test': False})
    if not assgnments_id:
        warn("No s'han trobat assignacions a contractes")
    else:
        showAssignmentsData(assgnments_id)

    #Comprovar drets gastats a Mongo
    filter = {
        "name": long(member_id),
        "regularization": {
            "$exists": False
        }
    }
    kwh_gastats = getCurveMongo(filter, localisodate(date_from), localisodate(date_to))

    #Comprovar drets gastats a les factures
    kwh_invoices = getInvoiceKwh(member_code, date_from, date_to)

    #La resta
    success("A Mongo s'han marcat com a gastats {} kWh, però a les factures hem trobat {} kWh. Desquadra de {} kWh.".format(kwh_gastats, kwh_invoices, (kwh_gastats-kwh_invoices)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description="Obtenir diferènia de drets gastats i utilitzats"
    )

    parser.add_argument(
        '--member-code',
        dest='member_code',
        #required=True,
        type=str,
        help="Número de persona sòcia. P.ex: S00001",
    )
    parser.add_argument(
        '--date-from',
        dest='date_from',
        default='2017-01-01',
        type=str,
        help="Data des de la que buscaran factures",
    )
    parser.add_argument(
        '--date-to',
        dest='date_to',
        default='2099-12-31',
        type=str,
        help="Data fins que es buscaran les factures",
    )

    args = parser.parse_args()
    try:
        main(args.member_code, args.date_from, args.date_to)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalitzat")

# vim: et ts=4 sw=4