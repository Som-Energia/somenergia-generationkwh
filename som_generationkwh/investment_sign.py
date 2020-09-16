# -*- coding: utf-8 -*-

import json, logging
from osv import osv, fields
from datetime import datetime, date
from tools.translate import _


class GenerationkwhInvestmentSign(osv.osv):

    _name = 'generationkwh.investment'
    _inherit = 'generationkwh.investment'

    def invoice_sign_request(self, cursor, uid, ids, invoice_ids, context=None):
        if not isinstance(invoice_ids, (list, tuple)):
            invoice_ids = [invoice_ids]

        logger = logging.getLogger()
        signatura_doc_obj = self.pool.get('giscedata.signatura.documents')
        signatura_proc_obj = self.pool.get('giscedata.signatura.process')
        inv_obj = self.pool.get('account.invoice')

        errors = []
        signatura_procs = []
        for inv_id in invoice_ids:
            investment_name = inv_obj.read(cursor, uid, inv_id, ['origin'])['origin']
            doc_ids = signatura_doc_obj.search(cursor, uid, [('model', '=', 'account.invoice,{}'.format(inv_id))])
            if doc_ids:
                proc_ids = [
                    doc['process_id'][0]
                    for doc in signatura_doc_obj.read(cursor, uid, doc_ids,['process_id'])
                ]
                not_failed_procs = signatura_proc_obj.search(cursor, uid, [('id', 'in', proc_ids),
                                                                   ('status', 'in', ['wait', 'doing', 'completed'])])
                if not_failed_procs:  #ja té un procés en iniciat o complert
                    error_message = 'La inversió {} té un procés de signatura actiu o finalitzat'.format(investment_name)
                    errors.append(error_message)
                    logger.error(error_message)
                    continue
            try:
                investment_id = self.search(cursor, uid, [('name', '=', investment_name)])[0]
                self.investment_sign_request(cursor, uid, investment_id)
            except Exception as e:
                error_message = 'La inversió {} ha generat un error en iniciar la signatura, error: {}'.\
                              format(investment_name, e)
                errors.append(error_message)
                logger.error(error_message)
            else:
                signatura_procs.append(investment_name)

        return signatura_procs, errors

            #TODO:
            #- Cos del missatge "False"
            #- Canviar nom variable config

    def investment_sign_request(self, cursor, uid, gen_ids, context=None):
        if not isinstance(gen_ids, (list, tuple)):
            gen_ids = [gen_ids]

        if context is None:
            context = {}

        for item_id in gen_ids:
            invest = self.browse(cursor, uid, item_id)
            email = None
            address_id = None

            address_id = invest.member_id.address[0].id
            email = invest.member_id.address[0].email
            lang = invest.member_id.lang
            if not email:
                raise osv.except_osv(
                    _('Error!'),
                    _(u"""Es necessita una adreça de correu electrònic per enviar el document a signar.""")
                )
            if not lang:
                raise osv.except_osv(
                    _('Error!'),
                    _(u"""El soci no té cap idioma assignat.""")
                )
            else:
                acc_inv_obj = self.pool.get('account.invoice')
                conf_obj = self.pool.get('res.config')
                imd_obj = self.pool.get('ir.model.data')
                attach_obj = self.pool.get('ir.attachment')
                add_obj = self.pool.get('res.partner.address')
                pro_obj = self.pool.get('giscedata.signatura.process')

                max_signable_documents = int(conf_obj.get(
                    cursor, uid, 'signature_signaturit_max_signable_documents', '2'))

                generation_report_id = imd_obj.get_object_reference(
                    cursor, uid, 'som_inversions', 'report_generationkwh_doc'
                )[1]

                invoice_categ = attach_obj.get_category_for(
                    cursor, uid, 'invoice', context=context)

                data = json.dumps({
                    'callback_method': 'generationkwh_signed',
                    'gen_id': item_id,
                })

                subject = 'Firma del contracte GenerationKWh amb identificador ' + self.read(cursor, uid, item_id, ['name'])['name']
                files = []

                acc_inv_id = acc_inv_obj.search(cursor, uid, [("origin", "=", invest.name)])

                if len(acc_inv_id) == 0:
                    raise osv.except_osv(
                        _('Error!'),
                        _(u"No hi ha cap factura per a aquest préstec de generation!")
                    )

                doc_file = (0, 0, {
                    'model': 'account.invoice,{}'.format(acc_inv_id[0]),
                    'report_id': generation_report_id,
                    'category_id': invoice_categ
                })
                files.append(doc_file)

                recipients = [
                    (0, 0, {
                        'partner_address_id': address_id,
                        'name': invest.member_id.name,
                        'email': email
                    })
                ]

                values = {
                    'subject': subject,  # Titulo del correo electronico
                    'delivery_type': 'email',  # Metodo de envio
                    'recipients': recipients,  # Personas que deberan firmar
                    'reminders': 0,
                    'type': 'advanced',
                    'data': data,
                    'all_signed': False,  # Ver esquema
                    'files': files,  # Documentos
                    'lang': lang
                }

                process_id = pro_obj.create(cursor, uid, values, context=context)
                pro_obj.start(cursor, uid, [process_id], context=context)

        return process_id

    def generationkwh_signed(self, cursor, uid, gen_id, context=None):
        if not isinstance(gen_id, (list, tuple)):
            gen_id = [gen_id]
        today = datetime.now().strftime('%Y-%m-%d')
        return self.write(cursor, uid, gen_id, {'signed_date': today})

GenerationkwhInvestmentSign()


class AccountInvoice(osv.osv):

    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def process_signature_callback(self, cursor, uid, ids, context=None):
        if not context:
            context = {}
        process_data = context.get('process_data', False)
        if process_data:
            method_name = process_data.get('callback_method', False)
            if method_name == 'generationkwh_signed':
                inv_obj = self.pool.get('generationkwh.investment')
                ids = process_data.get('gen_id', False)
                method = getattr(inv_obj, method_name)
            else:
                method = getattr(self, method_name)
            if method:
                method(cursor, uid, ids, context=context)

AccountInvoice()
