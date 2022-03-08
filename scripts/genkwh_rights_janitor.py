# -*- coding: utf-8 -*-

"""
Displays time series from Mongo
"""

import erppeek
import io, os, json
from os import path
import datetime
from consolemsg import step, success, warn, error, fail
import dbconfig
from yamlns import namespace as ns
from plantmeter.isodates import localisodate, toLocal, asUtc, addDays
import pymongo
from bson.son import SON

c = erppeek.Client(**dbconfig.erppeek)
mongoClient = pymongo.MongoClient(**dbconfig.mongo)
soci_o = c.model('somenergia.soci')
rul_o = c.model('generationkwh.right.usage.line')

D_DAY = '2022-02-23' #TODO: posar dia i hora (22/02 a les 20h aprox)
PREV_RIGHTS_FOLDER = './2022022220_memberRights'
START_DATE = '2021-01-01'

def get_mongo_rights(member_id, consultation_date=None, start=START_DATE):
    mongodb = mongoClient.somenergia
    start = localisodate(start)

    filters = {
        'datetime': {
            '$gte': start,
        },
        "name": member_id,
    }
    if consultation_date:
        filters.update({"create_at": {
            '$lt': localisodate(consultation_date)
        }})
    pipeline = [
        {"$match":
            filters,
        },
        {"$sort": SON([
            ("datetime", 1),
            ("name", 1),
            ("create_at", -1),
        ])},
        {"$group": {
            '_id': {
                "datetime": '$datetime',
                'name': '$name',
            },
            "datetime": {'$first': '$datetime'},
            "usage_kwh": {'$first': "$usage_kwh"}
        }},
        {"$group": {
            '_id': '$datetime',
         'datetime': {'$first': '$datetime'},
            'usage_kwh': {'$sum': '$usage_kwh'},
        }},
    ]
    toLocalDateString = lambda x: datetime.datetime.strftime(toLocal(asUtc(x)), '%Y-%m-%d %H:%M:%S')
    return {
        toLocalDateString(x['datetime']): x['usage_kwh']
        for x in mongodb.memberrightusage.aggregate(pipeline,cursor={},allowDiskUse=True)
    }

def get_or_create_DAYD_member_rights(member_id):
    member_filepath = "{}/{}.json".format(PREV_RIGHTS_FOLDER, member_id)
    data = ''
    if path.exists(member_filepath):
        with open(member_filepath, 'r') as f:
            data = json.load(f)
        return data

    data = get_mongo_rights(member_id, consultation_date=D_DAY)
    with open(member_filepath, 'w') as f:
        f.write(json.dumps(data))

    return data

def get_rights_invoices(partner_id):
    rul_ids = rul_o.search([('owner_id', '=', partner_id)])
    result = {}
    if not rul_ids:
        return result
    for rul in rul_o.read(rul_ids):
        if not rul['datetime'] in result:
            result[rul['datetime']] = 0
        result[rul['datetime']] += rul['quantity']

    return result

def get_difference_DDay_now_mongo(member_id):
    """
    Aquesta funció retorna tres diccionaris:
    - before_d_day_mongo: quins drets hi havia marcats a mongo justa abans de tenir dades a l'ERP
    - today_mongo: quins drets hi ha marcats a mongo avui
    - differences: canvis entre els dos diccionaris anteriors, que estaran reflexats a l'ERP.
    """

    before_d_day_mongo = get_or_create_DAYD_member_rights(member_id)
    today_mongo = get_mongo_rights(member_id)
    differences = today_mongo.copy()

    for k,v in before_d_day_mongo.iteritems():
        if k in differences:
            differences[k] -= v
        else:
            differences[k] = -v

    return before_d_day_mongo, today_mongo, differences

def get_incoherent_rights(member_id):
    """
    Comprovem que els canvis del diccionari differences estiguin reflexats a l'ERP.
    En cas contrari, creem una acció per:
    marcar a mongo per a cada dret: (QUANTITAT USADA ANTERIOR A LA MILLORA) + (INCREMENT QUE FIGURA A L'ERP)
    """

    partner_id = soci_o.read(member_id, ['partner_id'])['partner_id'][0]
    before_d_day_mongo, today_mongo, differences = get_difference_DDay_now_mongo(member_id)
    today_invoices = get_rights_invoices(partner_id)

    accions = {}
    total = 0
    for k,v in differences.iteritems():
        if k in today_invoices:
            if v != today_invoices[k]:
                diff = v - today_invoices[k]
                before_d_day_value = before_d_day_mongo[k] if k in before_d_day_mongo else 0
                new_value = max(before_d_day_value+today_invoices[k], 0)
                warn("Dret {} -> diferència (mongo-erp): {}. Escrivim {}:{}".format(k, diff, k, new_value))
                accions.update({k:new_value})
                #(Volem rectificar-lo) Crear dret k i valor erp
                total += diff
        elif v != 0:
            before_d_day_value = before_d_day_mongo[k] if k in before_d_day_mongo else 0
            new_value = before_d_day_value
            warn("Dret {} -> ERROR: només hi és al mongo: {}. Escrivim {}:{}".format(k, v, k, new_value))
            accions.update({k:new_value})
            total += v
            #cal tenir en compte que si no hi ha diferències entre el dia D i avui, vol dir que tot ok.
            #(Volem anular-lo) Crear dret k amb valor 0

    if accions:
        error("El partner {} ha desquadrat per un total de {} drets (mongo - erp).".format(str(member_id), str(total)))
    return accions

def main():
    if not os.path.exists(PREV_RIGHTS_FOLDER):
        os.makedirs(PREV_RIGHTS_FOLDER)

    step("Connectat a {}".format(c))

    member_obj = c.model('somenergia.soci')
    members = member_obj.search([('has_gkwh','=',True), ('active','=',True)])

    step("Consultant per cada una de les {} sòcies la diferència de drets a mongo (entre actualment i abans del dia D)...".format(len(members)))

    member_actions = {}
    for i, member_id in enumerate(members):
        try:
            step("Member {}/{}".format(str(i), str(len(members))))
            member_actions[member_id] = get_incoherent_rights(member_id)
        except KeyboardInterrupt as e:
            break
        except Exception as e:
            error("Member {}, error: {}".format(member_id, str(e)))

    filename = "{}/{}-{}.json".format(PREV_RIGHTS_FOLDER, 'actions', datetime.datetime.today())
    success("Consulta acabada. Es guardaran les accions al fitxer {}".format(filename))

    with open(filename, 'w') as f:
        f.write(json.dumps(member_actions))

    success("Sortint...")

if __name__ == '__main__':
    main()
