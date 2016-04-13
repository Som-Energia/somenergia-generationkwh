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
        for a in self.Assignments.browse([]):
            a.unlink()
    def test_no_assignments(self):
        self.setupProvider()
        self.assertAssignmentsEqual([])

    def test_one_assignment(self):
        rp=self.erp.ResPartner.browse([])[0]
        gp=self.erp.GiscedataPolissa.browse([])[0]
        self.setupProvider([[True,gp.id,rp.id,1]])
        self.assertAssignmentsEqual([[True,gp.id,rp.id,1]])
if __name__ == '__main__':
    unittest.main()
        
