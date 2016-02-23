# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv
import netsvc
from datetime import datetime


class GiscedataFacturacioFactura(osv.osv):
    """Afegim la funció de Generation kWh.
    """
    _name = 'giscedata.facturacio.factura'
    _inherit = 'giscedata.facturacio.factura'

    def apply_gkwh(self, cursor, uid, ids, context=None):
        """Apliquem l'operació del gkwh.
        """
        if context is None:
            context = {}

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        gkwh_dealer_obj = self.pool.get('generationkwh.dealer')
        inv_fields = ['polissa_id', 'data_inici', 'data_final']

        for inv_id in ids:
            # Test if contract is gkwh enabled

            inv_data = self.read(cursor, uid, inv_id, inv_fields, context)

            contract_id = inv_data['polissa_id'][0]
            start_date = inv_data['data_inici']
            end_date = inv_data['data_final']

            is_gkwh = gkwh_dealer_obj.is_active(
                cursor, uid, contract_id, start_date, end_date, context=None
            )

            if not is_gkwh:
                return


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
