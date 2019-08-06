# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields

class GiscedataPolissaTarifaPeriodes(osv.osv):
    """Periodes de les Tarifes."""
    _name = 'giscedata.polissa.tarifa.periodes'
    _inherit = 'giscedata.polissa.tarifa.periodes'

    _columns = {
        'product_gkwh_id': fields.many2one(
            'product.product', 'Generation kWh', ondelete='restrict'
        ),
    }

GiscedataPolissaTarifaPeriodes()

class GiscedataPolissa(osv.osv):

   _name = 'giscedata.polissa'
   _inherit = 'giscedata.polissa'


   def _search_is_gkwh(self, cursor, uid, obj, name, args, context=None):
       """Search function for is_gkwh"""
       cursor.execute(
           'SELECT distinct contract_id FROM generationkwh_assignment'
       )

       gkwh_ids = [t[0] for t in cursor.fetchall()]
       return [('id', 'in', gkwh_ids)]

   def _ff_is_gkwh(self, cursor, uid, ids, field_name, arg, context=None):
       """Returns true if contract has gkwh lines"""
       if not ids:
           return []
       res = dict([(i, False) for i in ids])

       vals = self.read(cursor, uid, ids, ['gkwh_linia_ids'])
       for val in vals:
           res.update({val['id']: bool(val['gkwh_linia_ids'])})

       return res

   _columns = {
       'gkwh_linia_ids': fields.one2many(
           'generationkwh.assignment', 'contract_id',
           'Contractes benefeciats per Generation kWH', readonly=True
       ),
       'is_gkwh': fields.function(
           _ff_is_gkwh,
           method=True,
           string='Te Generation', type='boolean',
           fnct_search=_search_is_gkwh
       )
   }

GiscedataPolissa()
