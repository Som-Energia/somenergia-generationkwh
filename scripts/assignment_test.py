# -*- coding: utf-8 -*-
import unittest
import datetime
dbconfig = None
from yamlns import namespace as ns
try:
    import dbconfig
    import erppeek
except ImportError:
    pass

@unittest.skipIf(not dbconfig, "depends on ERP")
class Assignment_Test(unittest.TestCase):

    def setUp(self):
        self.erp = erppeek.Client(**dbconfig.erppeek)
        self.Assignments = self.erp.GenerationkwhAssignments
        self.Assignments.dropAll()
        self.Helper = self.erp.GenerationkwhTesthelper

    def setupProvider(self,assignments=[]):
        self.Assignments.add(assignments)
    

    def assertAssignmentsSeekEqual(self, contract_id, expectation):
        result = self.Helper.assignments(contract_id)
        expectation=[dict(expect_elem) for expect_elem in expectation]
        self.assertEqual(result,expectation)

    def assertAllAssignmentsEqual(self, expectation):
        result = self.Assignments.browse([
            ])
        self.assertEqual( [
                [
                    r.contract_id.id,
                    r.member_id.id,
                    r.priority,
                    r.end_date,
                ]
                for r in result
            ],expectation)

    def assertAssignmentsEqual(self, expectation):
        result = self.Assignments.browse([])
        self.assertEqual([
            [
                r.contract_id.id,
                r.member_id.id,
                r.priority,
            ] for r in result],
            expectation)

    def tearDown(self):
        self.Assignments.dropAll()

    def test_no_assignments(self):
        self.setupProvider()
        self.assertAssignmentsEqual([])

    def test_default_values(self):
        member=self.erp.ResPartner.browse([],limit=1)[0]
        contract=self.erp.GiscedataPolissa.browse([], limit=1)[0]
        self.Assignments.create(dict(
            member_id = member,
            contract_id = contract,
            priority = 0,
            ))
        self.assertAllAssignmentsEqual([
            [contract.id, member.id, 0, False]
            ])

    def test_create_priorityRequired(self):
        member=self.erp.ResPartner.browse([],limit=1)[0]
        contract=self.erp.GiscedataPolissa.browse([], limit=1)[0]

        with self.assertRaises(Exception) as ctx:
            self.Assignments.create(dict(
                member_id = member,
                contract_id = contract,
                ))
        self.assertIn(
            'null value in column "priority" violates not-null constraint',
            str(ctx.exception))

    def test_create_contractRequired(self):
        member=self.erp.ResPartner.browse([],limit=1)[0]

        with self.assertRaises(Exception) as ctx:
            self.Assignments.create(dict(
                member_id = member,
                priority = 0,
                ))
        self.assertIn(
            'null value in column "contract_id" violates not-null constraint',
            str(ctx.exception))

    def test_create_memberRequired(self):
        contract=self.erp.GiscedataPolissa.browse([], limit=1)[0]

        with self.assertRaises(Exception) as ctx:
            self.Assignments.create(dict(
                contract_id = contract,
                priority = 0,
                ))
        self.assertIn(
            'null value in column "contract_id" violates not-null constraint',
            str(ctx.exception))

    def test_create_memberRequired(self):
        member=self.erp.ResPartner.browse([],limit=1)[0]
        contract=self.erp.GiscedataPolissa.browse([], limit=1)[0]

        with self.assertRaises(Exception) as ctx:
            self.Assignments.create(dict(
                contract_id = contract,
                priority = 0,
                ))
        self.assertIn(
            'null value in column "member_id" violates not-null constraint',
            str(ctx.exception))

    def test_one_assignment(self):
        member=self.erp.ResPartner.browse([],limit=1)[0]
        contract=self.erp.GiscedataPolissa.browse([], limit=1)[0]
        self.setupProvider([
            [contract.id,member.id,1],
            ])
        self.assertAssignmentsEqual([
            [contract.id,member.id,1]
            ])

    def test_no_duplication(self):
        member=self.erp.ResPartner.browse([], limit=1)[0]
        contract=self.erp.GiscedataPolissa.browse([],limit=1)[0]
        self.setupProvider([
            [contract.id, member.id, 1],
            [contract.id, member.id, 1],
            ])
        self.assertAllAssignmentsEqual([
            [contract.id, member.id, 1, str(datetime.date.today())],
            [contract.id, member.id, 1, False],
            ])
    
    def test_change_priority(self):
        member=self.erp.ResPartner.browse([], limit=1)[0]
        contract=self.erp.GiscedataPolissa.browse([],limit=1)[0]
        self.setupProvider([
            [contract.id,member.id,1],
            [contract.id,member.id,2],
            ])
        self.assertAllAssignmentsEqual([
            [contract.id, member.id, 1, str(datetime.date.today())],
            [contract.id,member.id,2, False]
            ])
        
    def test_three_member_three_polissas(self):
        members=self.erp.ResPartner.browse([],limit=3)
        contracts=self.erp.GiscedataPolissa.browse([], limit=3)
        self.setupProvider([
            [contract.id,member.id,1]
            for contract,member in zip(contracts,members)
            ])
        self.assertAssignmentsEqual([
            [contract.id,member.id,1]
            for contract,member in zip(contracts,members)
            ])

    def test_three_member_one_polissa(self):
        members=self.erp.ResPartner.browse([],limit=3)
        contract=self.erp.GiscedataPolissa.browse([], limit=1)[0]
        self.setupProvider([
            [contract.id,member.id,1]
            for member in members
            ])
        self.assertAssignmentsEqual([
            [contract.id,member.id,1]
            for member in members
            ])

    def test_one_member_three_polissas(self):
        member=self.erp.ResPartner.browse([],limit=1)[0]
        contracts=self.erp.GiscedataPolissa.browse([], limit=3)
        self.setupProvider([
            [gp_iter.id,member.id,1]
            for gp_iter in contracts
            ])
        self.assertAssignmentsEqual([
            [gp_iter.id,member.id,1]
            for gp_iter in contracts
            ])

    def test_seek_no_assignment(self):
        self.setupProvider()
        contract_id=self.erp.GiscedataPolissa.browse([], limit=1)[0].id
        self.assertAssignmentsSeekEqual(contract_id, [])
    
    def test_seek_one_assignment(self):
        contract_id=self.erp.GiscedataPolissa.browse([], limit=1)[0].id
        member_id=self.erp.ResPartner.browse([], limit=1)[0].id
        self.setupProvider([
            [contract_id,member_id,1]
        ])
        self.assertAssignmentsSeekEqual(contract_id, [
            ns(
                member_id=member_id,
            ),
        ])


            
if __name__ == '__main__':
    unittest.main()

