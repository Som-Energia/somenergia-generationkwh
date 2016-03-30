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
from plantmeter.resource import VirtualPlant, Plant, Meter 


class GenerationVirtualPlant(osv.osv):
    '''Implements generation virtual plant'''

    _name = 'generation.virtual.plant'

    def getWh(self, cursor, uid, pid, start, end, context=None):
        '''Get generation from virtual plant'''
   
        if not context:
            context = {}
        if isinstance(pid, list) or isinstance(pid, tuple):
            pid = pid[0]
        vplant = self.browse(cursor, uid, pid, context)

        def obj_to_dict(obj, attrs):
            return {attr: getattr(obj, attr) for attr in attrs}

        args = ['name', 'description', 'enabled']
        vplant = self.browse(cursor, uid, pid, context)

        _vplant = VirtualPlant(**obj_to_dict(vplant, args).update(
            {'plants': [Plant(**obj_to_dict(plant, args).update(
                {'meters': [Meter(**obj_to_dict(meter, args + ['uri']))
                for meter in plant.meters if meter.enabled]}))
            for plant in vplant.plants if plant.enabled]}))
        
        return _vplant.getWh(start, end)

    _columns = {
        'name': fields.char('Name', size=50),
        'description': fields.char('Description', size=150),
        'enabled': fields.boolean('Enabled'),
        'plants': fields.one2many('generation.plant', 'vplant_id', 'Plants')
    }

    _defaults = {
        'enabled': lambda *a: False
    }
GenerationVirtualPlant()


class GenerationPlant(osv.osv):

    _name = 'generation.plant'
    _columns = {
        'name': fields.char('Name', size=50),
        'description': fields.char('Description', size=150),
        'enabled': fields.boolean('Enabled'),
        'vplant_id': fields.many2one('generation.virtual.plant', 'Virtual Plant',
                                  required=True),
        'meters': fields.one2many('generation.meter', 'plant_id', 'Meters')
    }
    _defaults = {
        'enabled': lambda *a: False,
    }
GenerationPlant()


class GenerationMeter(osv.osv):

    _name = 'generation.meter'
    _columns = {
        'name': fields.char('Name', size=50),
        'description': fields.char('Description', size=150),
        'enabled': fields.boolean('Enabled'),
        'plant_id': fields.many2one('generation.plant'),
        'uri': fields.char('Host', size=150, required=True),
        }
    _defaults = {
        'enabled': lambda *a: False,
    }
GenerationMeter()


class GenerationMeasurement(osv_mongodb.osv_mongodb):

    _name = 'generation.measurement'
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
        return super(GenerationMeasurement,
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
GenerationMeasurement()
