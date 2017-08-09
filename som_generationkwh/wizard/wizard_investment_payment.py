# -*- coding: utf-8 -*-

from datetime import date

from osv import osv, fields
from tools.translate import _


class WizardInvestmentPayment(osv.osv):

    _name = 'wizard.generationkwh.investment.payment'

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': lambda *a: 'Aquesta acció crearà les factures inicials de'
                           ' la inversió, les obrirà i les posarà dintre de'
                           ' la remesa \n Condicions per a que es crear les'
                           ' factures:\n'
                           '  - Les inversions no han de tenir data de compra \n'
                           '  - No han de tenir una factura ja creada \n'
                           '  - Han de tenir bank associat a la persona sòcia \n'
    }


    def do_payment(self, cursor,uid, ids, context=None):
        Investment = self.pool.get('generationkwh.investment')
        wiz = self.browse(cursor, uid, ids[0], context)
        inv_ids = context.get('active_ids', [])

        errors = Investment.investment_payment(cursor, uid, inv_ids)

        if errors:
            info =  "ERRORS DURANT EL PROCÉS: \n"
            for error in errors:
                info += " -  " + str(error) + "\n"
        else:
            info = "No hi ha hagut errors durant el procés"

        wiz.write(dict(
            info= info,
            state = 'Done',
            ))
        return True

WizardInvestmentPayment()