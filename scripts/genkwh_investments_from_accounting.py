#!/usr/bin/env python
description = """
Generates investments from the accounting logs.
"""
waitingMonths = 12
returningYears = 25

import erppeek
import datetime
from dateutil.relativedelta import relativedelta
import dbconfig
from yamlns import namespace as ns

c = erppeek.Client(**dbconfig.erppeek)

def isodate(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S").date()

def clear():
    allinvestments = c.search('generationkwh.investments')
    c.unlink('generationkwh.investments', allinvestments)

def generate():
    paymentlines = c.read( 'payment.line',
        [('name','like','GKWH')],
#        order='partner_id',
        )

    for payment in paymentlines:
        payment = ns(payment)
        c.create('generationkwh.investments', dict(
            member_id=payment.partner_id[0],
            nshares=-payment.amount_currency//100,
            purchase_date=payment.create_date,
            activation_date=(
                None if waitingMonths is None else
                str(isodate(payment.create_date)
                    +relativedelta(months=waitingMonths))
                ),
            deactivation_date=(
                None if waitingMonths is None else
                None if returningYears is None else
                str(isodate(payment.create_date)
                    +relativedelta(
                        years=returningYears,
                        months=waitingMonths,
                        )
                    ),
                ),
            ))
            
clear()
generate()

