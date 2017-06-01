#!/usr/bin/env python
# -*- coding: utf8 -*-


import dbutils
from yamlns import namespace as ns

def getOrderLines(db, order_id):
    with db.cursor() as cr:
        cr.execute("""\
            select
                *
            from
                payment_line as pl
            where
                pl.order_id = %(order_id)s
            order by pl.id
        """, dict(
            order_id=order_id,
        ))
        return dbutils.nsList(cr)

def getMoveLines(db, move_id):
    with db.cursor() as cr:
        cr.execute("""\
            select
                ml.*
            from
                account_move_line as ml
            left join
                account_account as ac
            on ac.id = ml.account_id
            where
                ac.code ilike '1635%%' and
                ml.move_id = %(move_id)s
            order by ml.id
        """, dict(
            move_id=move_id,
        ))
        return dbutils.nsList(cr)

def getActiveInvestments(db):
    with db.cursor() as cr:
        cr.execute("""\
            select
                *
            from
                generationkwh_investment as inv
            where
                active=true and
                true
            order by inv.id
        """, dict(
        ))
        return dbutils.nsList(cr)

def investmentOrderAndMovements(db, modeName='GENERATION kWh'):
    with db.cursor() as cr:
        cr.execute("""\
            select
                o.id as order_id,
                m.move_id as move_id,
                o.n_lines as order_nlines,
                m.nlines as move_nlines,
                o.date_done as order_sent_date,
                m.date_created as move_create_date
            from
            (
                select
                    po.id,
                    po.n_lines,
                    po.date_done,
                    true
                from
                    payment_order as po
                left join
                    payment_mode as pm
                on
                    pm.id = po.mode
                where
                    pm.name = 'GENERATION kWh' and
                    true
            ) as o
            full outer join (
                select
                    l.move_id,
                    count(l.id) as nlines,
                    l.date_created
                from
                    account_move_line as l
                left join
                    account_account as a
                on
                    l.account_id=a.id
                where
                    a.code ilike '1635%%' and
                    l.name = '/' and
                    true
                group by
                    move_id,
                    l.date_created
                order by
                    l.date_created
            ) as m
                on o.date_done = m.date_created
            order by
                m.date_created
            ;
            """)
        return dbutils.nsList(cr)






import configdb
import psycopg2
from consolemsg import step, warn, success

with psycopg2.connect(**configdb.psycopg) as db:

    solved = ns()

    for data in investmentOrderAndMovements(db):
        step("{move_create_date}".format(**data))

        if not data.move_id:
            warn("{}: Order without movement. Id {}, with {} entries" .format(
                data.order_sent_date or "not yet",
                data.order_id,
                data.order_nlines,
                ))
            continue
        if not data.order_id:
            warn("{}: Movement without order. Id {}, with {} entries".format(
                data.move_create_date or "not yet",
                data.move_id,
                data.move_nlines,
                ))
            continue
        if data.move_nlines != data.order_nlines:
            warn("{}: Different number of lines. Payment order {}, Movement {}".format(
                data.move_create_date,
                data.order_nlines,
                data.move_nlines,
                ))

        orderLines = getOrderLines(db, data.order_id)
        moveLines = getMoveLines(db, data.move_id)

        if len(orderLines) != data.order_nlines:
            warn("Got different number of lines {} than reported {} in Order"
                .format(len(orderLines), data.order_nlines))

        if len(moveLines) != data.move_nlines:
            warn("Got different number of lines {} than reported {} in Move"
                .format(len(orderLines), data.order_nlines))

        orderLinesDict = ns()
        repesca = []

        for line in orderLines:
            key = (line.partner_id, -line.amount)
            value = orderLinesDict.get(key, [])
            value.append(line)
            orderLinesDict[key] = value
            
        for moveline in moveLines:
            key = (moveline.partner_id, moveline.credit)
            options = orderLinesDict.get(key, [])
            if not options:
                warn("Linia de Moviment sense parella")
                print key
                repesca.append(moveline)
                continue
            orderline = options.pop(0)
            False and success("{} {} {}".format(
                moveline.id, orderline.name, orderline.create_date))
            solved[moveline.id] = ns(
                ref=orderline.name,
                order_date=orderline.create_date,
                )

        for key, options in orderLinesDict.items():
            for option in options:
                warn("Linia de Remesa sense parella: {name} {create_date}"
                    .format(**option))
                print key

    investments = getActiveInvestments(db)

    for inv in investments:
        moveline_id = inv.move_line_id

        if moveline_id not in solved.keys():
            warn("Missing moveline {move_line_id} for partner {member_id}"
                .format(**inv))
        else:
            0 or success("{move_line_id} found".format(**inv))       

