# -*- coding: utf-8 -*-
from osv import osv, fields
from yamlns import namespace as ns
import pooler
from osv.expression import OOQuery
import generationkwh.investmentmodel as gkwh
from generationkwh.isodates import isodate
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
import logging


class GenerationkwhInvestment(osv.osv):
    _name = 'somenergia.soci'
    _inherit = 'somenergia.soci'

    def send_emails_to_investors_with_savings_in_year(self, cursor, uid, year=None):
        """
        Send email to the partners with retencions.rendiment.gkwh report
        attached to certificat_retencio_rendiment_generationkwh poweremail template.
        Only partners with generationkwh.investment investments that had saving at
        given year.
        """
        if year is None:
            raise Exception("Year must have a value")

        pool = pooler.get_pool(cursor.dbname)
        Investment = pool.get('generationkwh.investment')

        first_day = str(year) + '-01-01'
        last_day = str(year) + '-12-31'

        all_investments_ids_in_year = Investment.search(cursor, uid, [('first_effective_date', '<=', last_day),
                                                                      ('last_effective_date', '>=', first_day),
                                                                      ('emission_id.type', '=', 'genkwh')])
        if all_investments_ids_in_year is None:
            raise Exception("No investments found at year {}".format(year))

        members = []
        for invest_id in all_investments_ids_in_year:
            investment = Investment.read(cursor, uid, invest_id, ['member_id'])
            members.append(investment['member_id'][0])

        members = set(members)
        email_params = RetencionsSobreRendimentGenerationKwh.get_email_params(cursor, uid, self)

        successfully_sent = 0
        for member_id in members:
            if RetencionsSobreRendimentGenerationKwh.send_email(cursor, uid, self, member_id, email_params) > 0:
                successfully_sent += 1
        return successfully_sent


    def generationkwh_amortization_data(self, cursor, uid, ids):
        if not ids:
            raise Exception("No member provided")

        member_id = ids[0]

        report = ns()
        pool = pooler.get_pool(cursor.dbname)
        Accounts = pool.get('poweremail.core_accounts')
        ResPartner = pool.get('res.partner')
        ResPartnerAdress = pool.get('res.partner.address')
        Soci = pool.get('somenergia.soci')
        som_partner_id = 1  # ResPartner.search(cursor, uid, [('vat','=','ESF55091367')])
        som_partner = ResPartner.read(cursor, uid, som_partner_id, ['name', 'vat', 'address'])
        som_address = ResPartnerAdress.read(cursor, uid, som_partner['address'][0], ['street', 'zip', 'city'])
        report.address_city = som_address['city']
        report.address_zip = som_address['zip']
        report.address_street = som_address['street']
        report.partner_name = som_partner['name']
        report.partner_vat = som_partner['vat']

        report.year = (datetime.now() - timedelta(days=365)).year

        accounts = Accounts.search(cursor, uid, [('name', 'ilike', 'Generation'), ('state', '=', 'approved')])

        if accounts:
            account_id = accounts[0]
            report.address_email = Accounts.read(cursor, uid, account_id, ['email_id'])['email_id']
        else:
            report.address_email = None

        partner_id = Soci.read(cursor, uid, member_id, ['partner_id'])['partner_id'][0]
        partner = ResPartner.read(cursor, uid, partner_id, ['vat', 'name', 'lang'])
        report.data_inici = date(report.year, 1, 1).isoformat()
        report.data_fi = date(report.year, 12, 31).isoformat()

        pool = pooler.get_pool(cursor.dbname)
        genln_obj = pool.get('generationkwh.invoice.line.owner')
        q = OOQuery(genln_obj, cursor, uid)

        search_params = [('owner_id.id', '=', partner_id),
                         ('factura_id.invoice_id.date_invoice', '>=', report.data_inici),
                         ('factura_id.invoice_id.date_invoice', '<=', report.data_fi)]

        sql = q.select(['saving_gkw_amount','factura_line_id']).where(search_params)
        cursor.execute(*sql)

        irpf_value_saving = 0
        irpf_value_retencio = 0

        result = cursor.dictfetchall()
        result = {d['factura_line_id']: d['saving_gkw_amount'] for d in result}

        if result:
            irpf_value_saving = sum(result.values())
            irpf_value_retencio = round(irpf_value_saving * gkwh.irpfTaxValue, 2)

        report.member_name = partner['name']
        report.member_vat = partner['vat'][2:]
        report.estalvi = irpf_value_saving
        report.retencio = irpf_value_retencio
        report.language = partner['lang']

        return dict(report)

GenerationkwhInvestment()


class RetencionsSobreRendimentGenerationKwh():
    @staticmethod
    def get_email_params(cursor, uid, _object):
        """
        Return email from poweremail template
        """
        ir_model_data = _object.pool.get('ir.model.data')
        account_obj = _object.pool.get('poweremail.core_accounts')
        power_email_tmpl_obj = _object.pool.get('poweremail.templates')

        template_id = ir_model_data.get_object_reference(
            cursor, uid, 'som_generationkwh', 'certificat_retencio_rendiment_generationkwh'
        )[1]
        template = power_email_tmpl_obj.read(cursor, uid, template_id)

        email_from = False
        template_name = 'Generation'

        if template.get(template_name):
            email_from = template.get('enforce_from_account')[0]

        if not email_from:
            email_from = account_obj.search(cursor, uid, [('name', 'ilike', template_name)])[0]

        email_params = dict({
            'email_from': email_from,
            'template_id': template_id
        })

        return email_params

    @staticmethod
    def send_email(cursor, uid, _object, member_id, email_params):
        logger = logging.getLogger('openerp.poweremail')

        try:
            wiz_send_obj = _object.pool.get('poweremail.send.wizard')
            ctx = {
                'active_ids': [member_id],
                'active_id': member_id,
                'template_id': email_params['template_id'],
                'src_model': 'somenergia.soci',
                'src_rec_ids': [member_id],
                'from': email_params['email_from'],
                'state': 'single',
                'priority': '0',
            }

            params = {'state': 'single', 'priority': '0', 'from': ctx['from']}
            wiz_id = wiz_send_obj.create(cursor, uid, params, ctx)
            wiz_send_obj.send_mail(cursor, uid, [wiz_id], ctx)
            return 1

        except Exception as e:
            logger.info(
                'ERROR sending email to member {member}: {exc}'.format(
                    member=member_id,
                    exc=e
                )
            )
            return -1

# vim: et ts=4 sw=4
