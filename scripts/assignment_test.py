# -*- coding: utf-8 -*-
import unittest
dbconfig = None
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
        self.tearDown()
    
    def setupProvider(self,assignments=[]):
        self.Assignments.add(assignments)
    
    def assertAllAssignmentsEqual(self, expectation):
        result = self.Assignments.browse(['|', ('active', '=', False), ('active', '=', True)])
        self.assertEqual([
                            [r.active, 
                            r.polissa_id.id, 
                            r.member_id.id, 
                            r.priority]
                            for r in result], 
                         expectation)

    def assertAssignmentsEqual(self, expectation):
        result = self.Assignments.browse([])
        self.assertEqual([
                            [r.active, 
                            r.polissa_id.id, 
                            r.member_id.id, 
                            r.priority]
                            for r in result], 
                         expectation)
    def tearDown(self):
        for a in self.Assignments.browse(['|', ('active', '=', False), ('active', '=', True)]):
            a.unlink()
    def test_no_assignments(self):
        self.setupProvider()
        self.assertAssignmentsEqual([])

    def test_one_assignment(self):
        rp=self.erp.ResPartner.browse([],limit=1)[0]
        gp=self.erp.GiscedataPolissa.browse([], limit=1)[0]
        self.setupProvider([[True,gp.id,rp.id,1]])
        self.assertAssignmentsEqual([[True,gp.id,rp.id,1]])

    def test_no_duplication(self):
        rp=self.erp.ResPartner.browse([], limit=1)[0]
        gp=self.erp.GiscedataPolissa.browse([],limit=1)[0]
        self.setupProvider([[True,gp.id,rp.id,1],[True,gp.id,rp.id,1]])
        self.assertAllAssignmentsEqual([[False, gp.id, rp.id, 1], [True,gp.id,rp.id,1]])
    
    def test_change_priority(self):
        rp=self.erp.ResPartner.browse([], limit=1)[0]
        gp=self.erp.GiscedataPolissa.browse([],limit=1)[0]
        self.setupProvider([[True,gp.id,rp.id,1],[True,gp.id,rp.id,2]])
        self.assertAllAssignmentsEqual([[False, gp.id, rp.id, 1], [True,gp.id,rp.id,2]])
        
    def test_three_member_three_polissas(self):
        rp=self.erp.ResPartner.browse([],limit=3)
        gp=self.erp.GiscedataPolissa.browse([], limit=3)
        self.setupProvider([[True,gp_iter.id,rp_iter.id,1] for gp_iter,rp_iter in zip(gp,rp)])
        self.assertAssignmentsEqual([[True,gp_iter.id,rp_iter.id,1] for gp_iter,rp_iter in zip(gp,rp)])

    def test_three_member_one_polissa(self):
        rp=self.erp.ResPartner.browse([],limit=3)
        gp=self.erp.GiscedataPolissa.browse([], limit=1)[0]
        self.setupProvider([[True,gp.id,rp_iter.id,1] for rp_iter in rp])
        self.assertAssignmentsEqual([[True,gp.id,rp_iter.id,1] for rp_iter in rp])

    def test_one_member_three_polissas(self):
        rp=self.erp.ResPartner.browse([],limit=1)[0]
        gp=self.erp.GiscedataPolissa.browse([], limit=3)
        self.setupProvider([[True,gp_iter.id,rp.id,1] for gp_iter in gp])
        self.assertAssignmentsEqual([[True,gp_iter.id,rp.id,1] for gp_iter in gp])

if __name__ == '__main__':
    unittest.main()
        
