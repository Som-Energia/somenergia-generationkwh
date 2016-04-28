# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields
from tools.translate import _

from datetime import datetime, date

def field_function(ff_func):
    def string_key(*args, **kwargs):
        res = ff_func(*args, **kwargs)
        ctx = kwargs.get('context', None)
        if ctx or ctx is None:
            return res

        if not ctx.get('xmlrpc', False):
            return res

        return dict([(str(key), value) for key, value in res.tuples])

    return string_key


class SomenergiaSoci(osv.osv):
    """ Class to manage GkWh info in User interface"""

    _name = 'somenergia.soci'
    _inherit = 'somenergia.soci'

    @field_function
    def _ff_te_gkwh(self, cursor, uid, ids, field_name, args, context=None):
        """ Check's if a member any gkwh investment"""
        invest_obj = self.pool.get('generationkwh.investment')

        if context is None:
            context = {}

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        res = {}.fromkeys(ids, False)

        for member_vals in self.read(cursor, uid, ids, ['partner_id']):
            member_id = member_vals['id']
            partner_id = member_vals['partner_id'][0]
            investments = invest_obj.active_investments(
                cursor, uid, partner_id, None, None,
                context=context
            )
            res[member_id] = len(investments) > 0

        return res

    def _search_has_gkwh(self, cursor, uid, obj, field_name, args,
                         context=None):
        """ Search has_gkwh members"""
        sql = "SELECT  distinct(member_id) FROM generationkwh_investment"
        cursor.execute(sql)
        vals = [v[0] for v in cursor.fetchall()]

        return [('partner_id', 'in', vals)]

    _columns = {
        'has_gkwh': fields.function(
            _ff_te_gkwh, string='Te drets GkWh', readonly=True,
            fnct_search=_search_has_gkwh, type='boolean', method="True"
        ),
        #'investment_ids': one2many('member_id', )
        'gkwh_comments': fields.text('Observacions'),
    }

SomenergiaSoci()


class GenerationkWhkWhxShare(osv.osv):

    _name = "generationkwh.kwh.per.share"
    _order = "version_start_date DESC"

    def get_kwh_per_date(self, cursor, uid, date=None, context=None):
        """ Returns kwh on date
        :param date: date of calc. today if None
        :return: kwh per share on date
        """
        if date is None:
            date = datetime.today().strftime("%Y-%m-%d")

        v_ids = self.search(
            cursor, uid, [
                ('version_start_date', '<=', date)
            ], order='version_start_date desc'
        )
        return self.read(cursor, uid, v_ids[0], ['kwh'])['kwh']

    _columns = {
        'version_start_date': fields.date(u"Data Valor"),
        'kwh': fields.integer(u"kWh per acció"),
    }

GenerationkWhkWhxShare()
