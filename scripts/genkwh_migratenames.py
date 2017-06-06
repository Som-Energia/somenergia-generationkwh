#!/usr/bin/env python
# -*- coding: utf8 -*-


import dbutils
from yamlns import namespace as ns

def getOrderLines(db, order_id):
    with db.cursor() as cr:
        cr.execute("""\
            select
                pl.*,
                po.date_done as order_sent_date,
                p.name as partner_name,
                false
            from
                payment_line as pl
            left join
                payment_order as po
            on
                po.id = pl.order_id
            left join
                res_partner as p
            on
               p.id = pl.partner_id
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
                ml.*,
                p.name as partner_name
            from
                account_move_line as ml
            left join
                account_account as ac
            on ac.id = ml.account_id
            left join
                res_partner as p
            on
               p.id = ml.partner_id
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
                inv.*,
                ml.name as mlname,
                ml.date_created as move_date_created,
                soci.partner_id,
                p.name as partner_name
            from
                generationkwh_investment as inv
            left join
                account_move_line as ml
            on
                inv.move_line_id = ml.id
            left join
                somenergia_soci as soci
            on
                soci.id = inv.member_id
            left join
                res_partner as p
            on
                p.id = soci.partner_id
            where
                inv.active and
                true
            order by inv.id
        """, dict(
        ))
        return dbutils.nsList(cr)


def lastInvestment(db):
    with db.cursor() as cr:
        cr.execute("""\
            select
                max(move_line_id)
            from
                generationkwh_investment as inv
            where
                inv.active and
                true
        """, dict(
        ))
        return dbutils.nsList(cr)[0].max


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
                    pm.name = 'GENERATION kWh' or
                    po.id = 1389 or -- has mode 'ENGINYERS'
                    false
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


def appendToKey(d, key, value):
    values = d.get(key, [])
    wasEmpty = bool(values)
    values.append(value)
    d[key] = values
    return wasEmpty

def getAndRemoveFirst(d, key):
    values = d.get(key, [])
    if not values: return None
    return values.pop(0)

import configdb
import psycopg2
from consolemsg import step, warn, success

with psycopg2.connect(**configdb.psycopg) as db:

    lastGeneratedMoveLine = lastInvestment(db)

    solvedMovelines = ns()

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
            appendToKey(orderLinesDict, key, line)
            
        for moveline in moveLines:
            key = (moveline.partner_id, moveline.credit)
            orderline = getAndRemoveFirst(orderLinesDict, key)
            if not orderline:
                repesca.append(moveline)
                continue
            False and success("{} {} {}".format(
                moveline.id, orderline.name, orderline.create_date))
            solvedMovelines[moveline.id] = ns(
                ref=orderline.name,
                order_date=orderline.create_date,
                partner_id = orderline.partner_id,
                )

        movelinesByPartnerId = {}
        for moveline in repesca:
            appendToKey(movelinesByPartnerId, moveline.partner_id, moveline)

        for key, options in orderLinesDict.items():
            for orderline in options:
                moveline = getAndRemoveFirst(movelinesByPartnerId, orderline.partner_id)
                if not moveline:
                    warn("Linia de Remesa sense parella: {name} id {id} {order_sent_date} {amount}€ {partner_name}"
                        .format(**orderline))
                    print key
                    continue
                success("Repescao {}".format( orderline.name))
                solvedMovelines[moveline.id] = ns(
                    ref=orderline.name,
                    order_date=orderline.create_date,
                    partner_id = orderline.partner_id,
                    )

        for partner_id, movelines in movelinesByPartnerId.items():
            for moveline in movelines:
                warn("Linia de Moviment sense parella id {id} {create_date} {credit}€ {partner_name}".format(**moveline))

    investments = getActiveInvestments(db)


    unmatchedMoveLines = list(solvedMovelines.keys())
    unmatchedInvestments = []

    for inv in investments:
        moveline_id = inv.move_line_id

        if moveline_id not in solvedMovelines.keys():
            warn("Missing moveline {move_line_id} "
                "for partner {partner_id} {nshares:03d} '{mlname}'"
                .format(**inv))
            #warn(inv.dump())
            unmatchedInvestments.append(inv.id)
        else:
            0 and success("{move_line_id} found".format(**inv))       
            if moveline_id not in  unmatchedMoveLines:
                warn("Dupped moveline {move_line_id} {partner_name}".format(**inv))
            else:
                unmatchedMoveLines.remove(moveline_id)

    ungenerated = [
        line_id
        for line_id in unmatchedMoveLines
        if line_id > lastGeneratedMoveLine
    ]

    unmatchedMoveLines = [
        line_id
        for line_id in unmatchedMoveLines
        if line_id <= lastGeneratedMoveLine
    ]

    print 'UNMATCHED INVESTMENTS', len(unmatchedInvestments), unmatchedInvestments
    print 'UNMATCHED MOVELINES', len(unmatchedMoveLines), unmatchedMoveLines
    print 'UNGENERATED MOVELINES', len(ungenerated), ungenerated


    orphanMoveLinesByPartner = {}

    for moveline_id in unmatchedMoveLines:
        moveline = solvedMovelines[moveline_id]

        wasEmpty = appendToKey(orphanMoveLinesByPartner, moveline.partner_id, moveline)
        if wasEmpty:
            warn("partner with two pending movements {} {}".format(moveline.partner_id, moveline_id))

    for inv in investments:
        if inv.id not in unmatchedInvestments:
            continue

        partner_id = inv.partner_id
        solution = getAndRemoveFirst(orphanMoveLinesByPartner, partner_id)
        if not solution:
            warn("No trobada moveline {move_line_id} {partner_name}".format(**inv))
            continue
        success("HOLA "+solution.dump())




    print ns(val=orphanMoveLinesByPartner).dump()








