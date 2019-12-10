# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools import config


class WizardComputeMod193Invoice(osv.osv_memory):

    _name = 'wizard.aeat193.from.gkwh.invoices'

    def get_year(self, cursor, uid, context=None):
        if context is None:
            context = {}

        report_obj = self.pool.get('l10n.es.aeat.mod193.report')
        report_id = context.get('active_id')

        report = report_obj.browse(cursor, uid, report_id, context)

        return {
            'name': report.fiscalyear_id.name,
            'start': report.fiscalyear_id.date_start,
            'end': report.fiscalyear_id.date_stop
        }

    def _default_info(self, cursor, uid, context=None):
        if context is None:
            context = {}

        txt = u"Calculant la retenció de IRPF per a les factures amb " \
              u"Generation kWh de l'any {name} ({start} -> {end})"

        dates = self.get_year(cursor, uid, context)

        res = txt.format(**dates)

        return res

    def do_action(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz_id = ids[0]
        wiz = self.browse(cursor, uid, wiz_id, context)

        report_obj = self.pool.get('l10n.es.aeat.mod193.report')
        record_obj = self.pool.get('l10n.es.aeat.mod193.record')
        report_id = context.get('active_id')

        report = report_obj.browse(cursor, uid, report_id, context)

        dates = self.get_year(cursor, uid, context)

        txt = u"Calculant linies del model 193 de la AEAT " \
              u"per l'any fiscal {name}\n" \
              u"Buscarem les factures entre les dates " \
              u"{start} i {end}".format(**dates)

        common_vals = {
            'report_id': report.id,
            'lr_vat': '',
            'mediator': False,
            'code_key': '1',
            'code_value': report.company_vat,
            'incoming_key': 'B',
            'nature': '03',
            'payment': '1',
            'code_type': False,
            'code_bank': '',
            'pending': ' ',
            'fiscal_year_id': report.fiscalyear_id.id,
            'incoming_type': '1'
        }

        query_file = (u"%s/som_generationkwh/sql/aeat193_from_gkwh_invoices_query.sql" % config['addons_path'])
        query = open(query_file).read()
        cursor.execute(query, dict(start=dates['start'], end=dates['end']))

        new_linies = 0
        updated_lines = 0
        for data in cursor.fetchall():
            partner_vat = data[1]
            search_params = {
                'partner_vat': partner_vat,
                'report_id': report.id,
                'tax_percent': wiz.tax_id.amount * 100
            }

            vals = common_vals.copy()
            amount = float(data[2])
            vals.update({
                'partner_id': data[0],
                'partner_vat': partner_vat,
                'amount': amount,
                'amount_base': amount,
                'amount_tax': amount * wiz.tax_id.name,
                'tax_percent': wiz.tax_id.amount * 100
            })

            record_ids = record_obj.search(cursor, uid, search_params)
            if record_ids:
                if len(record_ids) > 1:
                    raise osv.except_osv("Error",
                                         _(u"S'ha trobat més d'una línia per al client amb VAT '{0}'. I per la taxa"
                                           u"Revisin les dades si us plau.").
                                         format(partner_vat))
                record_vals = record_obj.read(cursor, uid, record_ids[0], ['amount', 'amount_base', 'amount_tax'])
                record_vals.pop('id')
                for key, value in record_vals:
                    record_vals[key] = value + vals[key]
                record_obj.write(cursor, uid, record_ids[0], record_vals)
                updated_lines += 1
            else:
                record_obj.create(cursor, uid, vals)
                new_linies += 1

        txt += u'\nAfegides {} línies al model 193 i modificades {} de les existents'.format(new_linies, updated_lines)

        wiz.write({'info': txt, 'state': 'done'})

    _columns = {
        'tax_id': fields.many2one(
            'account.tax', 'Retenció a aplicar', required=True,
            help='Retenció IRPF a aplicar', domain=[('name', 'like', 'IRPF')]
        ),
        'info': fields.text('Info'),
        'state': fields.char('State', size=16),
    }

    _defaults = {
        'info': _default_info,
        'state': lambda *a: 'init',
    }


WizardComputeMod193Invoice()
