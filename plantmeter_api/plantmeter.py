# -*- coding: utf-8 -*-

import os
from osv import osv, fields
from mongodb_backend import osv_mongodb
import netsvc
import pooler
import time
from tools.translate import _
from tools import config

from datetime import datetime
from plantmeter.resource import ProductionAggregator, ProductionPlant, ProductionMeter 


class GenerationkwhProductionAggregator(osv.osv):
    '''Implements generationkwh production aggregation '''

    _name = 'generationkwh.production.aggregator'

    def getWh(self, cursor, uid, pid, start, end, context=None):
        '''Get production aggregation'''
   
        if not context:
            context = {}
        if isinstance(pid, list) or isinstance(pid, tuple):
            pid = pid[0]

        def obj_to_dict(obj, attrs):
            return {attr: getattr(obj, attr) for attr in attrs}

        args = ['name', 'description', 'enabled']
        aggr = self.browse(cursor, uid, pid, context)

        _aggr = ProductionAggregator(**obj_to_dict(aggr, args).update(
            {'plants': [ProductionPlant(**obj_to_dict(plant, args).update(
                {'meters': [ProductionMeter(**obj_to_dict(meter, args + ['uri']))
                for meter in plant.meters if meter.enabled]}))
            for plant in aggr.plants if plant.enabled]}))
        
        return _aggr.getWh(start, end)

    _columns = {
        'name': fields.char('Name', size=50),
        'description': fields.char('Description', size=150),
        'enabled': fields.boolean('Enabled'),
        'plants': fields.one2many('generationkwh.plant', 'aggr_id', 'Plants')
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
        'aggr_id': fields.many2one('generationkwh.production.plant', 'Production aggregator',
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
        'plant_id': fields.many2one('generatiokwh.production.plant'),
        'uri': fields.char('Host', size=150, required=True),
        }
    _defaults = {
        'enabled': lambda *a: False,
    }
GenerationkwhProdctionMeter()


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
