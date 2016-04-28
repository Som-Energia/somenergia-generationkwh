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

    def setupProvider(self,assignments=[]):
        self.Assignment.add(assignments)
    

    def assertAllAssignmentsEqual(self, expectation):
        result = self.Assignment.browse([
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
        result = self.Assignment.browse([])
        self.assertEqual([
            [
                r.contract_id.id,
                r.member_id.id,
                r.priority,
            ] for r in result],
            expectation)

    def tearDown(self):
        self.Assignment.dropAll()

    def test_no_assignments(self):
        self.setupProvider()
        self.assertAssignmentsEqual([])

    def test_default_values(self):
        member=self.erp.ResPartner.browse([],limit=1)[0]
        contract=self.erp.GiscedataPolissa.browse([], limit=1)[0]
        self.Assignment.create(dict(
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
            self.Assignment.create(dict(
                member_id = member,
                contract_id = contract,
                ))
        self.assertIn(
            'null value in column "priority" violates not-null constraint',
            str(ctx.exception))

    def test_create_contractRequired(self):
        member=self.erp.ResPartner.browse([],limit=1)[0]

        with self.assertRaises(Exception) as ctx:
            self.Assignment.create(dict(
                member_id = member,
                priority = 0,
                ))
        self.assertIn(
            'null value in column "contract_id" violates not-null constraint',
            str(ctx.exception))

    def test_create_memberRequired(self):
        contract=self.erp.GiscedataPolissa.browse([], limit=1)[0]

        with self.assertRaises(Exception) as ctx:
            self.Assignment.create(dict(
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
            self.Assignment.create(dict(
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


@unittest.skipIf(not dbconfig, "depends on ERP")
class AssignmentProvider_Test(unittest.TestCase):

    def setUp(self):
        self.erp = erppeek.Client(**dbconfig.erppeek)
        self.Assignment = self.erp.GenerationkwhAssignment
        self.Assignment.dropAll()

        self.member, self.member2 = [
            m.id for m in self.erp.ResPartner.browse([], limit=2)]

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

        # pickup cases (commented out the soci.id)
        self.member_noContracts = 629 # 537
        self.member_oneAsPayer = 5 # 4

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
            for record in self.Assignment.browse([])
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
        expectation = [list(e) for e in expectation]
        self.assertEqual(result, expectation) 

    def test_sortedDefaultContractsForMember_manyPayers_manyOwners(self):
        self.assertContractForMember(
            400,
            [
                (44944,   400), # Member payer. Annual use: 2500
                (26010,   400), # Member payer. Annual use: 800
                (3662,    400), # Member payer. Annual use: 700
                (149,     400), # Member owner. Annual use: 1800 (polissa_id <)
                (150,     400), # Member owner. Annual use: 1800
            ]
        )
    
    def test_sortedDefaultContractsForMember_onePayer_oneOwner(self):
        self.assertContractForMember(
            4320,
            [
                (22309,  4320), # Member payer. Annual use: 1900
                (22502,  4320), # Member owner. Annual use: 1500
            ]
        )
    def test_sortedDefaultContractsForMember_onePayer_oneOwner_ownerMoreUse(self):
        self.assertContractForMember(
            3743,
            [
                (1579,   3743), # Member payer. Annual use: 2000  
                (56153,  3743), # Member payer. Annual use: 484
                (56149,  3743), # Member owner. Annual use: 4222
            ]
        )
    
    def test_sortedDefaultContractsForMember_oneOwner(self):
        self.assertContractForMember(
            13846,
            [
                (15212, 13846), # Member owner. Annual use: 3500
            ]
        )
    
    def test_sortedDefaultContractsForMember_onePayer(self):
        self.assertContractForMember(
            10283,
            [
                (12652, 10283), # Member payer. Annual use: 4576
            ]
        )

    def test_sortedDefaultContractsForMember_manyPayers(self):
        self.assertContractForMember(
            24500,
            [
                (32327, 24500), # Member payer. Annual use: 150044
                (32325, 24500), # Member payer. Annual use: 2100
            ]
        )

    def test_sortedDefaultContractsForMember_withoutContracts(self):
        self.assertContractForMember(self.member_noContracts, [
            ])

    def test_sortedDefaultContractsForMember_oneAsPayer(self):
        self.assertContractForMember(self.member_oneAsPayer, [
            (4646, self.member_oneAsPayer)
            ])

    def test_sortedDefaultContractsForMember_manyOwners(self):
        self.assertContractForMember(
            32922,
            [
                (50606, 32922), # Member owner. Annual use: 12000
                (45653, 32922), # Member owner. Annual use: 2880
            ]
        )

    def test_sortedDefaultContractsForMember_oneMember(self):
        self.assertContractForMember(
            12992,
            [
                #Contracts as member are not shown
            ]
        )

    def  test_sortedDefaultContractsForMember_noInversions(self):
        self.assertContractForMember(
            3,
            [
                #The member has no generation so none is shown
            ]
        )
 
    def  test_sortedDefaultContractsForMember_noContracts(self):
        self.assertContractForMember(
            629,
            [
                #The member has generation but no contracts
            ]
        )
    def  test_sortedDefaultContractsForMember_manyMembers(self):
        self.assertContractForMember(
            [13846,10283],
            [
                (12652, 10283), # Member payer. Annual use: 4576
                (15212, 13846), # Member owner. Annual use: 3500
            ]
        )
        
        
if __name__ == '__main__':
    unittest.main()

