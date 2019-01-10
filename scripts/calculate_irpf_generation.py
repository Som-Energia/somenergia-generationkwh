import dbconfig
import psycopg2
import dbutils
import contextlib
from yamlns import namespace as ns
from consolemsg import step, warn, success, error as consoleError, fail
import sys
import datetime
import ooop
import erppeek
import csv
import codecs

CONS_YEAR = 2018
CONS_IRPF = 0.19
"""
result = {
    partner_id = [kwgeneration, totalEGen, totalProfit, totalRetentionIRPF]
    ....
}
"""
O = erppeek.Client(**dbconfig.erppeek)

def writeCSV(result):
    with codecs.open('irpf_generation_' + str(CONS_YEAR) + '.csv', 'wb', 'utf-8') as csvfile:
         writer = csv.writer(csvfile, delimiter=';',
                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
         writer.writerow(['partner_id','kwgeneration', 'totalEGen','totalProfit','totalRetentionIRPF','soci', 'nifSoci'])

         for key, value in result.iteritems():
            row = [key] + value
            writer.writerow(row)

def getInvoiceLinesGen(cr, year):
    "Locates any investment yet to be generated"
    cr.execute("""\
        SELECT gff.polissa_id, ail.invoice_id, ail.product_id,  ail.price_unit, ail.quantity, ail.price_subtotal, ai.partner_id, ai.type 
        FROM account_invoice_line as ail, account_invoice as ai, giscedata_facturacio_factura as gff
        WHERE ail.invoice_id = ai.id AND
    	  gff.invoice_id = ai.id AND
          ai.date_invoice >= '""" + str(year) + """-01-01' AND ai.date_invoice < '""" + str(year + 1) + """-01-01' AND
        --  ai.date_invoice >= '2016-01-01' AND ai.date_invoice < '2019-01-01' AND
          ail.product_id IN (
            SELECT pp.id
            FROM product_category as pc, product_template as pt, product_product as pp
            WHERE pc.id = pt.categ_id AND
              pp.product_tmpl_id = pt.id AND
              pc.name like 'Generation kWh')
        """)
    return dbutils.nsList(cr)

def getUnitPriceFromInvoice(cr, invoice_id, product_id):
    cr.execute("""\
        SELECT price_unit
        FROM account_invoice_line as ail
        WHERE ail.invoice_id = %s AND
            ail.product_id = %s
        """ % (invoice_id, product_id))
    result = dbutils.nsList(cr)
    price = 0
    if result:
        for line in result:
            price = line.price_unit
    return price

def getPriceWithoutGeneration(cr, line):
    per_obj = O.GiscedataPolissaTarifaPeriodes
    gff_obj = O.GiscedataFacturacioFactura

    fare_period = gff_obj.get_fare_period(line.product_id)
    product_id_nogen = per_obj.read(fare_period, ['product_id'])['product_id'][0]

    return getUnitPriceFromInvoice(cr, line.invoice_id, product_id_nogen)

def getProfit(cr, line):
    if line.quantity == 0:
        return 0

    priceNoGen = getPriceWithoutGeneration(cr, line)
    profit = (priceNoGen - line.price_unit) * line.quantity
    return profit

def getInversor(cr, polissa_id):
    soci = {}
    cr.execute("""\
        SELECT ss.partner_id, rp.name, rp.vat
        FROM generationkwh_assignment as ga, somenergia_soci as ss, res_partner as rp
        WHERE 
          ga.member_id = ss.id AND
          ss.partner_id = rp.id AND
          ga.contract_id = """ + str(polissa_id) +  """
        LIMIT 1
        """)
    result = dbutils.nsList(cr)
    if result:
        soci['partner_id'] = result[0].partner_id
        soci['name'] = result[0].name
        soci['dni'] = result[0].vat
    else:
        print "Polissa no trobada: ", str(polissa_id)
        soci = {'dni': 'ES00000000A', 'partner_id': 1, 'name': polissa_id}

    return soci

def calculateProfit(cr, invoicesLinesGen, result):
    if invoicesLinesGen:
        for line in invoicesLinesGen:
            inversor = getInversor(cr, line.polissa_id)
            partner_id = inversor['partner_id']
            
            #Create array if not exist
            if partner_id not in result:
                result[partner_id] = [0,0,0,0,"nom", "dni"]
            
            #Check if AB invoice
            fact_type = 1
            if line.type == 'out_refund':
                fact_type = -1

            #Get array
            temp_array = result[partner_id]
            
            #Sum kwh generation
            temp_array[0] = temp_array[0] + (int(line.quantity) * fact_type)

            #Sum Euro generation
            temp_array[1] = round(temp_array[1] + (float(line.price_subtotal) * fact_type), 2)
            
            #Sum profit
            temp_array[2] = round(temp_array[2] + (float(getProfit(cr, line)) * fact_type), 2)

            #Calcul IRPF
            temp_array[3] = round(temp_array[2] * CONS_IRPF, 2)

            #Nom soci
            temp_array[4] = inversor['name']

            #NIF soci
            temp_array[5] = inversor['dni']

            #Save new array
            result[partner_id] = temp_array

def main(cr):
    invoicesLinesGen = getInvoiceLinesGen(cr, CONS_YEAR)
    result = {}
    calculateProfit(cr, invoicesLinesGen, result)
    writeCSV(result)

if __name__ == '__main__':
    with psycopg2.connect(**dbconfig.psycopg) as db:
        with db.cursor() as cr:
            main(cr)

# vim: et ts=4 sw=4
