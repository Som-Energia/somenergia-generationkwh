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
        erp = erppeek.Client(**dbconfig.erppeek)
        self.Assignments = erp.GenerationkwhAssignments
        # TODO: Clean database
    
    def setupProvider(self,assignments=[]):
        pass
        #self.Assignments.add(assignments)

    def assertAssignmentsEqual(self, expectation):
        result = self.Assignments.browse([])
        self.assertEqual([
                            [r.active, 
                            r.polissa_id, 
                            r.partner_id, 
                            r.priority]
                            for r in result], 
                         expectation)

    def test_no_assignments(self):
        self.setupProvider()
        self.assertAssignmentsEqual([])

if __name__ == '__main__':
    unittest.main()
        
