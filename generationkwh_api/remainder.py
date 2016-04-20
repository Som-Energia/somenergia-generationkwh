# -*- coding: utf-8 -*-

from osv import osv, fields
from .erpwrapper import ErpWrapper

class RemainderProvider(ErpWrapper):

    def get(self):
        remainders=self.erp.pool.get('generationkwh.remainders')
        return remainders.last(self.cursor,self.uid, context=self.context)

    # TODO: FIX: 'remainders' parameter aliased here!!!
    def set(self,remainders):
        remainders=self.erp.pool.get('generationkwh.remainders')
        remainders.add(self.cursor,self.uid,remainders, context=self.context)


class GenerationkWhRemainders(osv.osv):
    """
    Remainders, in Wh, after dividing the aggregated
    production of the plants into a hourly curve of
    available kWh for a member with a given number of
    shares.
    """

    _name = "generationkwh.remainders"
    _columns = dict(
        n_shares=fields.integer(
            required=True,
            help="Number of shares"
        ),
        target_day=fields.date(
            required=True,
            help="Day after the last day computed. The one to carry the remainder on."
        ),
        remainder_wh=fields.integer(
            required=True,
            help="Remainder in Wh"
        )
    )

    _sql_constraints = [(
        'unique_n_shares_target_day', 'unique(n_shares,target_day)',
            'Only one remainder of last date computed and number of shares '
            'is allowed'
        )]

    def last(self, cr, uid, context=None):
        cr.execute("""
            SELECT o.n_shares,o.target_day,o.remainder_wh
                FROM generationkwh_remainders AS o
                LEFT JOIN generationkwh_remainders AS b
                    ON o.n_shares=b.n_shares
                    AND o.target_day < b.target_day
                WHERE b.target_day IS NULL
            """)
        result = [
            (
                n_shares,
                target_day,
                remainder_wh,
            ) for n_shares, target_day, remainder_wh in cr.fetchall()
        ]
        return result

    def add(self, cr, uid, remainders, context=None):
        for n,pointsDate,remainder in remainders:
            same_date_n_id=self.search(cr, uid, [
                ('n_shares','=',n),
                ('target_day','=', pointsDate),
            ], context=context)
            if same_date_n_id:
                self.unlink(
                    cr, uid,
                    same_date_n_id, context=context
                )
            self.create(cr,uid,{
                'n_shares': n,
                'target_day': pointsDate,
                'remainder_wh': remainder
            }, context=context)

    def clean(self,cr,uid,context=None):
        ids=self.search(cr,uid, [], context=context)
        self.unlink(cr,uid,ids)

GenerationkWhRemainders()

