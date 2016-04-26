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

    def init(self, nSharesToInit):
        """
            Creates a initial remainder with 0Wh for the many nSharesToInit
            received at the same date than the first remainder for 1-shares.
            If there is no remainder with nshares = 1 then...
        """


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
            SELECT r.n_shares,r.target_day,r.remainder_wh
                FROM generationkwh_remainder AS r
                LEFT JOIN generationkwh_remainder AS r2
                    ON r.n_shares=r2.n_shares
                    AND r.target_day < r2.target_day
                WHERE r2.target_day IS NULL
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

    def newRemaindersToTrack(self,cr,uid,nshares,context=None):
        """
            Add an startup remainder for each number of shares
            provided, with 0Wh and the date of the first 1-share
            remainder.
            If no 1-share remainder exists, it has no effect.
        """
        cr.execute("""
            SELECT r.n_shares,r.target_day,r.remainder_wh
            FROM generationkwh_remainder AS r
            WHERE n_shares = 1
            ORDER BY r.target_day ASC LIMIT 1
            """)

        first1ShareRemainder = cr.fetchone()
        if first1ShareRemainder is None: return
        _,date,_ = first1ShareRemainder
        for n in nshares:
            self.add(cr,uid,[(n,date,0)],context)
        

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

