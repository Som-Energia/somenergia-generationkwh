# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
import netsvc
import time
import random

class InvestmentTests(testing.OOTestCase):
    def test_mark_as_signed(self):
        """
        Checks if signed_date change
        :return:
        """
        pool = self.openerp.pool
        investment_obj = pool.get('generationkwh.investment')
        imd_obj = pool.get('ir.model.data')

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = imd_obj.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            inv_0001 = investment_obj.browse(cursor, uid, inv_id)
            self.assertEquals(inv_0001.signed_date, False)

            investment_obj.mark_as_signed(cursor, uid, inv_id, '2017-01-06')

            inv_0001 = investment_obj.browse(cursor, uid, inv_id)
            self.assertEquals(inv_0001.signed_date, '2017-01-06')

    def test_mark_as_signed_apo(self):
        """
        Checks if signed_date change
        :return:
        """
        pool = self.openerp.pool
        investment_obj = pool.get('generationkwh.investment')
        imd_obj = pool.get('ir.model.data')
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = imd_obj.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            inv_0001 = investment_obj.browse(cursor, uid, inv_id)
            self.assertEquals(inv_0001.signed_date, False)

            investment_obj.mark_as_signed(cursor, uid, inv_id, '2017-01-06')

            inv_0001 = investment_obj.read(cursor, uid, inv_id)
            inv_0001.pop('actions_log')
            inv_0001.pop('log')
            inv_0001.pop('id')
            id_emission, name_emission = inv_0001.pop('emission_id')
            self.assertEqual(name_emission, "Aportacions")
            self.assertEquals(inv_0001,
                {
                    'first_effective_date': False,
                    'move_line_id': False,
                    'last_effective_date': False,
                    'nshares': 10,
                    'signed_date': '2017-01-06',
                    'draft': True,
                    'purchase_date': False,
                    'member_id': (1, u'Gil, Pere'),
                    'active': True,
                    'order_date': '2019-10-01',
                    'amortized_amount': 0.0,
                    'name': u'APO00001'
                })

    def test_create_from_form_apo(self):
        """
        Checks if investment aportacio is created
        :return:
        """
        pool = self.openerp.pool
        investment_obj = pool.get('generationkwh.investment')
        imd_obj = pool.get('ir.model.data')
        partner_obj = pool.get('res.partner')
        mailmockup = pool.get('generationkwh.mailmockup')
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            mailmockup.activate(cursor, uid)
            partner_id = imd_obj.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]

            inv_id = investment_obj.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-06',
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo')
            inv_0001 = investment_obj.read(cursor, uid, inv_id)
            inv_0001.pop('actions_log')
            inv_0001.pop('log')
            inv_0001.pop('id')
            id_emission, name_emission = inv_0001.pop('emission_id')
            self.assertEqual(name_emission, "Aportacions")
            self.assertEquals(inv_0001,
                {
                    'first_effective_date': False,
                    'move_line_id': False,
                    'last_effective_date': False,
                    'nshares': 40,
                    'signed_date': False,
                    'draft': True,
                    'purchase_date': False,
                    'member_id': (1, u'Gil, Pere'),
                    'active': True,
                    'order_date': '2017-01-06',
                    'amortized_amount': 0.0,
                    'name': u'APO005000'
                })
            mailmockup.deactivate(cursor, uid)

# vim: et ts=4 sw=4