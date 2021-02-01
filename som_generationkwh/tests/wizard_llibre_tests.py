# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
import json


class TestsWizard(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        self.maxDiff = None

    def tearDown(self):
        self.txn.stop()

    def get_object_id(self, module, obj_ref):
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        irmd_o = pool.get('ir.model.data')
        object_id = irmd_o.get_object_reference(cursor, uid, module, obj_ref)[1]
        return object_id

    def test_get_soci_values(self):
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        soci_o = pool.get('somenergia.soci')
        wiz_o = pool.get('wizard.llibre.registre.socis')
        soci_id = self.get_object_id('som_generationkwh', 'soci_aportacions')

        values = wiz_o.get_soci_values(cursor, uid, soci_id)

        self.assertEqual(values, {'adreca': u'Esperan\xe7a, 8',
	     'cp': u'43580',
	     'data_alta': False,
	     'data_baixa': False,
	     'dni': u'16405474B',
	     'email': u'',
	     'municipi': False,
	     'nom': u'Alina An\xedssimova',
	     'num_soci': u'S202003',
	     'provincia': False,
	     'tipus': 'Consumidor'})

    def test_get_aportacions_obligatories_values(self):
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        soci_o = pool.get('somenergia.soci')
        wiz_o = pool.get('wizard.llibre.registre.socis')
        soci_id = self.get_object_id('som_generationkwh', 'soci_aportacions')
        soci_o.write(cursor, uid, soci_id, {'date': '2017-01-01'})

        values = wiz_o.get_aportacions_obligatories_values(cursor, uid, soci_id)

        self.assertEqual(values, [{'concepte': u'Aportaci\xf3n obligatoria',
             'data_compra': '2017-01-01',
             'import': 100}])


    def test_get_aportacions_voluntaries_values(self):
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        soci_o = pool.get('somenergia.soci')
        wiz_o = pool.get('wizard.llibre.registre.socis')
        soci_id = self.get_object_id('som_generationkwh', 'soci_aportacions')

        values = wiz_o.get_aportacions_voluntaries_values(cursor, uid, soci_id)

        self.assertEqual(values, [{'concepte': u'Aportaci\xf3n voluntaria',
        'data_compra': '2020-03-12',
        'data_venda': False,
        'import': 1000,
        'import_amortitzat': 0.0}])
