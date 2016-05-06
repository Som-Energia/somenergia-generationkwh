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
    
    def test_isActive_noActiveContracts(self):
        result = self.c.GenerationkwhDealer.is_active(99999999,False, False)
        self.assertEqual(result,False)
    
    def test_isActive_ActiveOtherContract(self):
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=1))
        result = self.c.GenerationkwhDealer.is_active(99999999, False, False)
        self.assertEqual(result,False)

    def test_isActive_ActiveOneContract(self):
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=1))
        result = self.c.GenerationkwhDealer.is_active(self.contract,False, False)
        self.assertEqual(result,True)

    def test_isActive_ExpiredContract(self):
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=1))
        self.c.GenerationkwhAssignment.expire(self.contract,self.member)
        result = self.c.GenerationkwhDealer.is_active(self.contract, False, False)
        self.assertEqual(result,False)
        
    def test_isActive_ExpiredAndActiveContract(self):
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=1))
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=1))
        result = self.c.GenerationkwhDealer.is_active(self.contract, False, False)
        self.assertEqual(result,True)

    def test_isActive_OtherExpiredActiveContract(self):
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=1))
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract2, member_id=self.member2, priority=1))
        self.c.GenerationkwhAssignment.expire(self.contract,self.member)
        result = self.c.GenerationkwhDealer.is_active(self.contract2, False, False)
        self.assertEqual(result,True)
        
    def test_isActive_OtherActiveExpiredContract(self):
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=1))
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract2, member_id=self.member2, priority=1))
        self.c.GenerationkwhAssignment.expire(self.contract,self.member)
        result = self.c.GenerationkwhDealer.is_active(self.contract, False, False)
        self.assertEqual(result,False)
if __name__ == '__main__':
    unittest.main()
