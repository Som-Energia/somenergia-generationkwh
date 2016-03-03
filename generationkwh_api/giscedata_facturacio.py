# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv
from tools.translate import _
import netsvc
from datetime import datetime


class GiscedataFacturacioFactura(osv.osv):
    """Afegim la funció de Generation kWh.
    """
    _name = 'giscedata.facturacio.factura'
    _inherit = 'giscedata.facturacio.factura'

    def get_gkwh_period(self, cursor, uid, product_id, context=None):
        """" Get's linked Generation kWh period
            product_id: product.product id
        """
        res = None
        per_obj = self.pool.get('giscedata.polissa.tarifa.periodes')

        per_id = self.get_fare_period(cursor, uid, product_id, context=None)

        if per_id:
            res = per_obj.read(
                cursor, uid, per_id, ['product_gkwh_id'], context=context
            )['product_gkwh_id'][0]

        return res

    def get_fare_period(self, cursor, uid, product_id, context=None):
        """" Get's fare period from line product
            product_id: product.product id
        """
        res = None
        per_obj = self.pool.get('giscedata.polissa.tarifa.periodes')

        if isinstance(product_id, (tuple, list)):
            product_id = product_id[0]

        per_ids = per_obj.search(
            cursor, uid, [('product_id', '=', product_id)], context=context
        )

        if per_ids:
            return per_ids[0]

        return res

    def apply_gkwh(self, cursor, uid, ids, context=None):
        """Apply gkwh transform"""
        if context is None:
            context = {}

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        inv_obj = self.pool.get('giscedata.facturacio.factura')
        invlines_obj = self.pool.get('giscedata.facturacio.factura.linia')
        pricelist_obj = self.pool.get('product.pricelist')
        partner_obj = self.pool.get('res.partner')

        gkwh_dealer_obj = self.pool.get('generationkwh.dealer')
        inv_fields = ['polissa_id', 'data_inici', 'data_final', 'llista_preu',
                      'tarifa_acces_id', 'linies_energia']

        line_fields = ['data_desde', 'data_fins', 'product_id', 'quantity',
                       'multi', 'tipus', 'name', 'price_unit_multi', 'tipus',
                       'uos_id', 'account_id', 'invoice_line_tax_id',
                       'uom_multi_id'
                       ]

        for inv_id in ids:
            # Test if contract is gkwh enabled
            inv_data = self.read(cursor, uid, inv_id, inv_fields, context)

            contract_id = inv_data['polissa_id'][0]
            start_date = inv_data['data_inici']
            end_date = inv_data['data_final']
            pricelist = inv_data['llista_preu'][0]

            is_gkwh = gkwh_dealer_obj.is_active(
                cursor, uid, contract_id, start_date, end_date, context=context
            )

            if not is_gkwh:
                return

            # Get energy periods
            for line_id in inv_data['linies_energia']:
                line_vals = False
                line_vals = invlines_obj.read(
                    cursor, uid, line_id, line_fields, context=context
                )
                line_product_id = line_vals['product_id'][0]

                # GkWh invoice line creation
                product_gkwh_id = self.get_gkwh_period(
                    cursor, uid, line_product_id, context=context
                )

                vals = line_vals.copy()

                if 'id' in vals:
                    del vals['id']

                invoice_line_tax_id = [
                    (6, 0, line_vals['invoice_line_tax_id'])
                ]

                price_unit = pricelist_obj.price_get(
                    cursor, uid, [pricelist], product_gkwh_id, 1,
                    context={'date': end_date}
                )[pricelist]

                # Get available gkwh rights
                # returns a list of rights x member
                fare = inv_data['tarifa_acces_id'][0]
                period = self.get_fare_period(
                    cursor, uid, line_product_id, context=context
                )
                line_quantity = line_vals['quantity']

                gkwh_quantity_dict = gkwh_dealer_obj.use_kwh(
                    cursor, uid, contract_id, start_date, end_date, fare,
                    period, line_quantity
                )

                vals.update({
                    'factura_id': inv_id,
                    'data_desde': line_vals['data_desde'],
                    'data_fins': line_vals['data_fins'],
                    'product_id': product_gkwh_id,
                    'price_unit_multi': price_unit,
                    'account_id': vals['account_id'][0],
                    'invoice_line_tax_id': invoice_line_tax_id,
                    'uos_id': line_vals['uos_id'][0],
                })
                # original line quantity counter
                new_quantity = line_quantity
                for gkwh_line in gkwh_quantity_dict:
                    gkwh_quantity = gkwh_line['kwh']
                    gwkh_owner_id = gkwh_line['member_id']

                    gwkh_owner_name = partner_obj.read(
                        cursor, uid, gwkh_owner_id, ['name'], context=context
                    )['name']

                    # substract from original line quantity
                    new_quantity -= gkwh_quantity

                    invlines_obj.write(
                        cursor, uid, line_id, {'quantity': new_quantity}
                    )

                    # create gkwh line
                    vals.update({
                        'quantity': gkwh_quantity,
                        'name': _(u'{0} GkWh de "{1}"').format(
                            line_vals['name'], gwkh_owner_name
                        ),
                    })
                    invlines_obj.create(cursor, uid, vals, context)

            inv_obj.button_reset_taxes(cursor, uid, [inv_id], context=context)

GiscedataFacturacioFactura()


class GiscedataFacturacioFacturador(osv.osv):
    """Sobreescrivim el mètode fact_via_lectures per aplicar GkWh.
    """
    _name = 'giscedata.facturacio.facturador'
    _inherit = 'giscedata.facturacio.facturador'

    def fact_via_lectures(self, cursor, uid, polissa_id, lot_id, context=None):
        factures = super(GiscedataFacturacioFacturador,
                         self).fact_via_lectures(cursor, uid, polissa_id,
                                                 lot_id, context)
        factura_obj = self.pool.get('giscedata.facturacio.factura')
        factura_obj.apply_gkwh(cursor, uid, factures, context)

        return factures

GiscedataFacturacioFacturador()
