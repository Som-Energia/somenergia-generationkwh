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
        self.Assignment = self.erp.GenerationkwhAssignment
        self.Assignment.dropAll()

        (
            self.member,
            self.member2,
            self.member3,
        ) = self.erp.SomenergiaSoci.search([],limit=3)
        (
            self.contract,
            self.contract2,
            self.contract3,
        ) = self.erp.GiscedataPolissa.search([], limit=3)

    def setupProvider(self,assignments=[]):
        self.Assignment.add(assignments)
    

    def assertAllAssignmentsEqual(self, expectation):
        result = self.Assignment.browse([
            ])
        self.assertEqual( [
                (
                    r.contract_id.id,
                    r.member_id.id,
                    r.priority,
                    r.end_date,
                )
                for r in result
            ],expectation)

    def assertAssignmentsEqual(self, expectation):
        result = self.Assignment.browse([])
        self.assertEqual([
            (
                r.contract_id.id,
                r.member_id.id,
                r.priority,
            ) for r in result],
            expectation)

    def assertAssignmentsExpiredEqual(self, expectation):
        result = self.Assignment.browse([])
        self.assertEqual([
            (
                r.contract_id.id,
                r.member_id.id,
                r.priority,
                r.end_date
            ) for r in result],
            expectation)

    def tearDown(self):
        self.Assignment.dropAll()

    def test_no_assignments(self):
        self.setupProvider()
        self.assertAssignmentsEqual([])

    def test_default_values(self):
        self.Assignment.create(dict(
            member_id = self.member,
            contract_id = self.contract,
            priority = 0,
            ))
        self.assertAllAssignmentsEqual([
            (self.contract, self.member, 0, False),
            ])

    def test_create_priorityRequired(self):

        with self.assertRaises(Exception) as ctx:
            self.Assignment.create(dict(
                member_id = self.member,
                contract_id = self.contract,
                ))
        self.assertIn(
            'null value in column "priority" violates not-null constraint',
            str(ctx.exception))

    def test_create_contractRequired(self):

        with self.assertRaises(Exception) as ctx:
            self.Assignment.create(dict(
                member_id = self.member,
                priority = 0,
                ))
        self.assertIn(
            'null value in column "contract_id" violates not-null constraint',
            str(ctx.exception))

    def test_create_memberRequired(self):

        with self.assertRaises(Exception) as ctx:
            self.Assignment.create(dict(
                contract_id = self.contract,
                priority = 0,
                ))
        self.assertIn(
            'null value in column "contract_id" violates not-null constraint',
            str(ctx.exception))

    def test_create_memberRequired(self):

        with self.assertRaises(Exception) as ctx:
            self.Assignment.create(dict(
                contract_id = self.contract,
                priority = 0,
                ))
        self.assertIn(
            'null value in column "member_id" violates not-null constraint',
            str(ctx.exception))

    def test_one_assignment(self):
        self.setupProvider([
            (self.contract,self.member,1),
            ])
        self.assertAssignmentsEqual([
            (self.contract,self.member,1),
            ])

    def test_no_duplication(self):
        self.setupProvider([
            (self.contract, self.member, 1),
            (self.contract, self.member, 1),
            ])
        self.assertAllAssignmentsEqual([
            (self.contract, self.member, 1, str(datetime.date.today())),
            (self.contract, self.member, 1, False),
            ])
    
    def test_change_priority(self):
        self.setupProvider([
            (self.contract,self.member,1),
            (self.contract,self.member,2),
            ])
        self.assertAllAssignmentsEqual([
            (self.contract, self.member, 1, str(datetime.date.today())),
            (self.contract,self.member,2, False),
            ])
        
    def test_three_member_three_polissas(self):
        members=self.member, self.member2, self.member3
        contracts=self.contract,self.contract2,self.contract3
        self.setupProvider([
            (self.contract, self.member, 1),
            (self.contract2,self.member2,1),
            (self.contract3,self.member3,1),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 1),
            (self.contract2,self.member2,1),
            (self.contract3,self.member3,1),
            ])

    def test_three_member_one_polissa(self):
        members=self.member, self.member2, self.member3
        self.setupProvider([
            (self.contract,self.member, 1),
            (self.contract,self.member2,1),
            (self.contract,self.member3,1),
            ])
        self.assertAssignmentsEqual([
            (self.contract,self.member, 1),
            (self.contract,self.member2,1),
            (self.contract,self.member3,1),
            ])

    def test_one_member_three_polissas(self):
        contracts=self.contract,self.contract2,self.contract3
        self.setupProvider([
            (self.contract,  self.member,1),
            (self.contract2, self.member,1),
            (self.contract3, self.member,1),
            ])
        self.assertAssignmentsEqual([
            (self.contract , self.member,1),
            (self.contract2, self.member,1),
            (self.contract3, self.member,1),
            ])
    
    def test_expire_one_member_one_polissa(self):
        self.setupProvider([
            (self.contract, self.member,1),
            ])
        self.Assignment.expire([
            (self.contract, self.member),
        ])
        self.assertAssignmentsExpiredEqual([
            (self.contract, self.member,1,str(datetime.date.today())),
            ])

    def test_expire_one_member_two_polissa(self):
        self.setupProvider([
            (self.contract, self.member,1),
            (self.contract2, self.member,1),
            ])
        self.Assignment.expire([
            (self.contract, self.member),
        ])
        self.assertAssignmentsExpiredEqual([
            (self.contract, self.member,1,str(datetime.date.today())),
            (self.contract2, self.member,1,False),
            ])
        
    def test_expire_previously_expired_polissa(self):
        self.setupProvider([
            (self.contract, self.member,1),
            (self.contract, self.member,1),
            ])
        self.Assignment.expire([
            (self.contract, self.member),
        ])
        self.assertAssignmentsExpiredEqual([
            (self.contract, self.member,1,str(datetime.date.today())),
            (self.contract, self.member,1,str(datetime.date.today())),
            ])
        
@unittest.skipIf(not dbconfig, "depends on ERP")
class AssignmentProvider_Test(unittest.TestCase):

    def setUp(self):
        self.erp = erppeek.Client(**dbconfig.erppeek)
        self.Assignment = self.erp.GenerationkwhAssignment
        self.Assignment.dropAll()

        self.member, self.member2 = [
            m.id for m in self.erp.SomenergiaSoci.browse([], limit=2)]

        contract, contract2 = [ c for c in self.erp.GiscedataPolissa.browse(
                [('data_ultima_lectura','!=',False)],
                order='data_ultima_lectura',
                limit=2,
                )
            ]
        self.contract = contract.id
        self.contract2 = contract2.id
        self.contractLastInvoicedDate = contract.data_ultima_lectura
        self.contract2LastInvoicedDate = contract2.data_ultima_lectura

        newContract, = self.erp.GiscedataPolissa.browse(
                [('data_ultima_lectura','=',False),
                 ('state','=','activa')], limit=1)
        self.newContract = newContract.id
        self.newContractActivationDate = newContract.data_alta

        # pickup cases (commented out the original partner.id)
        self.member_noContracts = 537 # 629
        self.member_oneAsPayer = 4 # 5 
        self.member_asOwnerButNotPayer = 8899 # 13846
        self.member_aPayerAndAnOwnerContract = 107 # 120
        self.member_manyAsPayer = 54 # 61
        self.member_manyAsPayerAndManyAsOwner = 351 # 400

        # Sorted contracts for member_manyAsPayerAndManyAsOwner
        # TODO: Sort them by annual use programatically, if not is fragile,
        # since annual use depends on the database snapshot
        self.payerContracts= 44944,26010,3662
        self.ownerContracts= 150,149

    def setupAssignments(self, assignments):
        for contract, member, priority in assignments:
            self.Assignment.create(dict(
                contract_id=contract,
                member_id=member,
                priority=priority,
                ))

    def assertAssignmentsSeekEqual(self, contract_id, expectation):
        result = self.Assignment.availableAssigmentsForContract(contract_id)
        self.assertEqual([
            dict(
                member_id=member_id,
                last_usable_date=str(last_usable_date),
            )
            for member_id, last_usable_date in expectation
            ], result)

    def tearDown(self):
        self.Assignment.dropAll()


    def test_seek_noAssignment(self):
        self.setupAssignments([])
        self.assertAssignmentsSeekEqual(self.contract, [])
    
    def test_seek_oneAssignment_noCompetitors(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, datetime.date.today()),
            ])

    def test_seek_expiredAssignment_notRetrieved(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        self.Assignment.expire([(self.contract, self.member)])
        self.assertAssignmentsSeekEqual(self.contract, [
            ])

    def test_seek_assigmentsForOtherContracts_ignored(self):
        self.setupAssignments([
            (self.contract2, self.member, 1),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
        ])

    def test_seek_manyAssignments_noCompetitors(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract, self.member2, 0),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, datetime.date.today()),
            (self.member2, datetime.date.today()),
            ])

    def test_seek_competitorWithoutInvoices_takesActivationDate(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.newContract, self.member, 0),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.newContractActivationDate),
            ])

    def test_seek_competitorWithInvoices_takesLastInvoicedDate(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract2, self.member, 0),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.contract2LastInvoicedDate),
            ])

    def test_seek_competitor_expired_ignored(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract2, self.member, 0),
            ])
        self.Assignment.expire([(self.contract2, self.member)])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, datetime.date.today()),
            ])

    def test_seek_competitorWithEqualOrLowerPriority_ignored(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract2, self.member, 1), # equal
            (self.newContract, self.member, 2), # lower (higher number)
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, datetime.date.today()),
            ])

    def test_seek_manyCompetitors_earlierLastInvoicedPrevails(self):
        self.setupAssignments([
            (self.newContract,self.member,1),
            (self.contract,self.member,0),
            (self.contract2,self.member,0),
            ])
        self.assertAssignmentsSeekEqual(self.newContract, [
            (self.member, min(
                self.contractLastInvoicedDate,
                self.contract2LastInvoicedDate,
                )),
            ])
    def assertAllAssignmentsEqual(self,expectation):
        self.assertEqual([
            (record.contract_id.id, record.member_id.id, record.priority) 
            for record in self.Assignment.browse([], order='id')
            ], expectation)
        
    def test_createOnePrioritaryAndManySecondaries_oneAssignment(self):
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract, self.member),
            ])
        self.assertAllAssignmentsEqual([
            (self.contract, self.member, 0),
            ])
    def test_createOnePrioritaryAndManySecondaries_noAssignment(self):
        self.Assignment.createOnePrioritaryAndManySecondaries([
            ])
        self.assertAllAssignmentsEqual([
            ])
        
    def test_createOnePrioritaryAndManySecondaries_clearPrevious(self):
        self.setupAssignments([
            (self.contract2, self.member, 1),
            ])
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract, self.member),
            ])
        self.assertAllAssignmentsEqual([
            (self.contract, self.member, 0),
            ])

    def test_createOnePrioritaryAndManySecondaries_preserveOtherMembers(self):
        self.setupAssignments([
            (self.contract2, self.member2, 1),
            ])
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract,self.member),
            ])
        self.assertAllAssignmentsEqual([
            (self.contract2, self.member2, 1),
            (self.contract, self.member, 0),
            ])
    
    def test_createOnePrioritaryAndManySecondaries_manyMembers_singleContract(self):
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract,self.member),
            (self.contract2,self.member2),
            ])
        self.assertAllAssignmentsEqual([
            (self.contract, self.member, 0),
            (self.contract2, self.member2, 0),
            ])

    def test_createOnePrioritaryAndManySecondaries_sameMember_manyContracts(self):
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract, self.member),
            (self.contract2, self.member),
            ])
        self.assertAllAssignmentsEqual([
            (self.contract, self.member, 0),
            (self.contract2, self.member, 1),
            ])


    def assertContractForMember(self, member_id,expectation):
        if not isinstance(member_id,list):
            member_ids=[member_id]
        else:
            member_ids=member_id
        result=self.Assignment.sortedDefaultContractsForMember(
            member_ids
        )
        self.assertEqual([tuple(r) for r in result], expectation) 


    def test_sortedDefaultContractsForMember_withoutContracts(self):
        self.assertContractForMember(self.member_noContracts, [
            ])

    def test_sortedDefaultContractsForMember_oneAsPayer(self):
        self.assertContractForMember(self.member_oneAsPayer, [
            (4646, self.member_oneAsPayer),
            ])

    def test_sortedDefaultContractsForMember_oneAsOwnerButNotPayer(self):
        self.assertContractForMember(self.member_asOwnerButNotPayer, [
            (15212, self.member_asOwnerButNotPayer),
            ])

    def test_sortedDefaultContractsForMember_onePayerAndOneOwner_payerFirst(self):
        self.assertContractForMember([
            self.member_aPayerAndAnOwnerContract,
            ], [
            (50851, self.member_aPayerAndAnOwnerContract), # payer
            (43,    self.member_aPayerAndAnOwnerContract), # owner
            ])

    def test_sortedDefaultContractsForMember_manyAsPayer_biggerFirst(self):
        self.assertContractForMember([
            self.member_manyAsPayer,
            ], [
            (929, self.member_manyAsPayer), # payer bigger
            (21,  self.member_manyAsPayer), # payer smaller
            ])

    def test_sortedDefaultContractsForMember_manyAsPayerAndManyAsOwner(self):
        # TODO: Check the order is right
        self.assertContractForMember([
            self.member_manyAsPayerAndManyAsOwner,
            ], [
            (self.payerContracts[0], self.member_manyAsPayerAndManyAsOwner),
            (self.payerContracts[1], self.member_manyAsPayerAndManyAsOwner),
            (self.payerContracts[2], self.member_manyAsPayerAndManyAsOwner),
            (self.ownerContracts[0], self.member_manyAsPayerAndManyAsOwner),
            (self.ownerContracts[1], self.member_manyAsPayerAndManyAsOwner),
            ])

    def test_sortedDefaultContractsForMember_severalMembers_doNotBlend(self):
        # TODO: Check the order is right
        self.assertContractForMember([
            self.member_manyAsPayer,
            self.member_manyAsPayerAndManyAsOwner,
            ], [
            (929, self.member_manyAsPayer),
            (21, self.member_manyAsPayer),
            (self.payerContracts[0], self.member_manyAsPayerAndManyAsOwner),
            (self.payerContracts[1], self.member_manyAsPayerAndManyAsOwner),
            (self.payerContracts[2], self.member_manyAsPayerAndManyAsOwner),
            (self.ownerContracts[0], self.member_manyAsPayerAndManyAsOwner),
            (self.ownerContracts[1], self.member_manyAsPayerAndManyAsOwner),
            ])

if __name__ == '__main__':
    unittest.main()

