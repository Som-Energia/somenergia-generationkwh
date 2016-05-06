# -*- coding: utf-8 -*-

import unittest


class Dealer_test(unittest.TestCase):

    def setUp(self):
        self.maxDiff=None
        import erppeek
        import dbconfig
        self.c = erppeek.Client(**dbconfig.erppeek)
        self.clearData()
        self.contract, self.contract2 = self.c.GiscedataPolissa.search([], limit=2)
        self.member = 1 # has 25 shares at the first investment wave
        self.partner = 2
        self.member2 = 469
        self.partner2 = 550

    def tearDown(self):
        self.clearData()

    def clearData(self):
        self.c.GenerationkwhAssignment.dropAll()
    
    def test_isActive_withBadContract(self):
        result = self.c.GenerationkwhDealer.is_active(99999999,False, False)
        self.assertEqual(result,False)
    

    def test_isActive_withoutAssignments(self):
        result = self.c.GenerationkwhDealer.is_active(self.contract,False, False)
        self.assertEqual(result,False)

    def test_isActive_withAssignments(self):
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=1))
        result = self.c.GenerationkwhDealer.is_active(self.contract,False, False)
        self.assertEqual(result,True)

if __name__ == '__main__':
    unittest.main()


