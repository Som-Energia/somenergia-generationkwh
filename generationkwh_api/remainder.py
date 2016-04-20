# -*- coding: utf-8 -*-

from osv import osv, fields
from .erpwrapper import ErpWrapper

from generationkwh.isodates import localisodate

class RemainderProvider(ErpWrapper):

    def get(self):
        Remainder=self.erp.pool.get('generationkwh.remainder')
        return Remainder.last(self.cursor,self.uid, context=self.context)


    def set(self,remainders):
        Remainder=self.erp.pool.get('generationkwh.remainder')
        Remainder.add(self.cursor,self.uid,remainders, context=self.context)


class GenerationkWhRemainder(osv.osv):
    """
    Remainders, in Wh, after dividing the aggregated
    production of the plants into a hourly curve of
    available kWh for a member with a given number of
    shares.
    """

    _name = "generationkwh.remainder"
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
        "Returns the latest remainder for each number of shares."""

        cr.execute("""
            SELECT o.n_shares,o.target_day,o.remainder_wh
                FROM generationkwh_remainder AS o
                LEFT JOIN generationkwh_remainder AS b
                    ON o.n_shares=b.n_shares
                    AND o.target_day < b.target_day
                WHERE b.target_day IS NULL
            """)
        result = [
            (
                n_shares,
                localisodate(target_day),
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

GenerationkWhRemainder()


class GenerationkWhRemainderTesthelper(osv.osv):
    '''Implements generationkwh remainder testhelper '''

    _name = "generationkwh.remainder.testhelper"

    def last(self, cr, uid, context=None):
        def toStr(date):
            return date.strftime('%Y-%m-%d')

        remainder = self.pool.get('generationkwh.remainder')
        remainders = remainder.last(cr, uid, context)
        return [(r[0], toStr(r[1]), r[2]) for r in remainders]

    def add(self, cr, uid, remainders, context=None):
        remainder = self.pool.get('generationkwh.remainder')
        remainder.add(cr, uid, remainders, context)

    def clean(self,cr,uid,context=None):
        remainder = self.pool.get('generationkwh.remainder')
        remainder.clean(cr, uid, context)

GenerationkWhRemainderTesthelper()

