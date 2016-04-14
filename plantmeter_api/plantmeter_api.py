# -*- coding: utf-8 -*-

import os
from osv import osv, fields
from mongodb_backend import osv_mongodb
from mongodb_backend.mongodb2 import mdbpool

from datetime import datetime
from plantmeter.resource import ProductionAggregator, ProductionPlant, ProductionMeter 
from plantmeter.mongotimecurve import MongoTimeCurve,tz

def isodate(string):
    return tz.localize(datetime.strptime(string, "%Y-%m-%d"))

class GenerationkwhProductionAggregator(osv.osv):
    '''Implements generationkwh production aggregation '''

    _name = 'generationkwh.production.aggregator'


    def getWh(self, cursor, uid, pid, start, end, context=None):
        '''Get production aggregation'''
   
        if not context:
            context = {}
        if isinstance(pid, list) or isinstance(pid, tuple):
            pid = pid[0]

        aggr = self.browse(cursor, uid, pid, context)
        _aggr = self._createAggregator(aggr, ['name', 'description', 'enabled'])
        return _aggr.getWh(isodate(start), isodate(end)).tolist()

    def updateWh(self, cursor, uid, pid, start, end, context=None):
        '''Update Wh measurements'''

        if not context:
            context = {}
        if isinstance(pid, list) or isinstance(pid, tuple):
            pid = pid[0]

        args = ['name', 'description', 'enabled']
        aggr = self.browse(cursor, uid, pid, context)
        _aggr = self._createAggregator(aggr, args)
        return _aggr.updateWh(start, end)

    def firstMeasurementDate(self, cursor, uid, pid, context=None):
        '''Get first measurement date'''

        if not context:
            context = {}
        if isinstance(pid, list) or isinstance(pid, tuple):
            pid = pid[0]

        args = ['name', 'description', 'enabled']
        aggr = self.browse(cursor, uid, pid, context)
        _aggr = self._createAggregator(aggr, args)
        return _aggr.firstMeasurementDate()

    def lastMeasurementDate(self, cursor, uid, pid, context=None):
        '''Get last measurement date'''

        if not context:
            context = {}
        if isinstance(pid, list) or isinstance(pid, tuple):
            pid = pid[0]

        args = ['name', 'description', 'enabled']
        aggr = self.browse(cursor, uid, pid, context)
        _aggr = self._createAggregator(aggr, args)
        return _aggr.lastMeasurementDate()

    def _createAggregator(self, aggr, args):
        def obj_to_dict(obj, attrs):
            return {attr: getattr(obj, attr) for attr in attrs}

        curveProvider = MongoTimeCurve(mdbpool.get_db(),
                'generationkwh.production.measurement')

        # TODO: Clean initialization method
        return ProductionAggregator(**dict(obj_to_dict(aggr, args).items() + 
            dict(plants=[ProductionPlant(**dict(obj_to_dict(plant, args).items() +
                dict(meters=[ProductionMeter(**dict(obj_to_dict(meter, args + ['uri']).items() +
                    dict(curveProvider=curveProvider).items()))
                for meter in plant.meters if meter.enabled]).items()))
            for plant in aggr.plants if plant.enabled]).items()))

    _columns = {
        'name': fields.char('Name', size=50),
        'description': fields.char('Description', size=150),
        'enabled': fields.boolean('Enabled'),
        'plants': fields.one2many('generationkwh.production.plant', 'aggr_id', 'Plants')
    }

    _defaults = {
        'enabled': lambda *a: False
    }
GenerationkwhProductionAggregator()


class GenerationkwhProductionPlant(osv.osv):

    _name = 'generationkwh.production.plant'
    _columns = {
        'name': fields.char('Name', size=50),
        'description': fields.char('Description', size=150),
        'enabled': fields.boolean('Enabled'),
        'aggr_id': fields.many2one('generationkwh.production.aggregator', 'Production aggregator',
                                  required=True),
        'meters': fields.one2many('generationkwh.production.meter', 'plant_id', 'Meters')
    }
    _defaults = {
        'enabled': lambda *a: False,
    }
GenerationkwhProductionPlant()


class GenerationkwhProductionMeter(osv.osv):

    _name = 'generationkwh.production.meter'
    _columns = {
        'name': fields.char('Name', size=50),
        'description': fields.char('Description', size=150),
        'enabled': fields.boolean('Enabled'),
        'plant_id': fields.many2one('generationkwh.production.plant'),
        'uri': fields.char('Host', size=150, required=True),
        }
    _defaults = {
        'enabled': lambda *a: False,
    }
GenerationkwhProductionMeter()


class GenerationkwhProductionMeasurement(osv_mongodb.osv_mongodb):

    _name = 'generationkwh.production.measurement'
    _order = 'timestamp desc'

    def search(self, cursor, uid, args, offset=0, limit=0, order=None,
               context=None, count=False):
        '''Exact match for name.
        In mongodb, even when an index exists, not exact
        searches for fields scan all documents in collection
        making it extremely slow. Making name exact search
        reduces dramatically the amount of documents scanned'''

        new_args = []
        for arg in args:
            if not isinstance(arg, (list, tuple)):
                new_args.append(arg)
                continue
            field, operator, value = arg
            if field == 'name' and operator != '=':
                operator = '='
            new_args.append((field, operator, value))
        return super(GenerationkwhProductionMeasurement,
                     self).search(cursor, uid, new_args,
                                  offset=offset, limit=limit,
                                  order=order, context=context,
                                  count=count)

    _columns = {
        'name': fields.integer('Plant identifier'), # NOTE: workaround due mongodb backend
        'create_at': fields.datetime('Create datetime'),
        'datetime': fields.datetime('Exported datetime'),
        'daylight': fields.char('Exported datetime daylight',size=1),
        'ae': fields.float('Exported energy (kWh)')
    }
GenerationkwhProductionMeasurement()

# vim: ts=4 sw=4 et
