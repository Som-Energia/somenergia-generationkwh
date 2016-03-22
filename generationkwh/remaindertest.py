# -*- coding: utf-8 -*-
import unittest
import datetime
import ooop
import config

def isodate(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()
class RemainderProviderErpTest(object):
    def __init__(self):
        self.erp=ooop.OOOP(**config.ooop)
    def get(self):
        Remainders = self.erp.GenerationkwhRemainders
        ids = Remainders.search([])
        return [
            (
                r['n_shares'],
                r['last_day_computed'],
                r['remainder_wh']
            ) for r in Remainders.read(ids, ['n_shares','last_day_computed','remainder_wh'])
        ]
    def set(self, n, pointsDate, remainder):
        Remainders = self.erp.GenerationkwhRemainders
        Remainders.create({'n_shares': n,'last_day_computed': pointsDate, 'remainder_wh':remainder})

    def clean(self):
        Remainders = self.erp.GenerationkwhRemainders
        Remainders.all().delete()

class RemainderProviderMockup(object):
    def __init__(self, remainders=[]):
        if remainders:
            self.set(*remainders)
        else:
            self.remainders=[]
    def get(self):
        if not self.remainders:
            return []
        max_nshares=max(self.remainders,key=lambda x:x[0])[0]
        remainders=[]
        for i in range(1,max_nshares+1):
            remainders.append(sorted([
            remainder for remainder in self.remainders 
                        if remainder[0]==i],reverse=True,key=lambda x:isodate(x[1])
                            )[0])
        return remainders
    def set(self, n, pointsDate, remainder_wh):
        self.remainders.append((n,pointsDate,remainder_wh))

class Remainder_Test(unittest.TestCase):

    def setupProvider(self,remainders=[]):
        provider=RemainderProviderMockup()
        for remainder in remainders:
            provider.set(*remainder)
        return provider

    def test_no_remainders(self):
        remainders=self.setupProvider()
        self.assertEqual([],remainders.get())

    def test_one_remainder(self):
        remainders=self.setupProvider([
                (1,'2016-02-25',3)
                ])
        self.assertEqual([
            (1,'2016-02-25',3)
            ],remainders.get())

    def test_two_remainder(self):
        remainders=self.setupProvider([
                (1,'2016-02-25',3),
                (2,'2016-02-25',1)
                ])
        self.assertEqual([
            (1,'2016-02-25',3),
            (2,'2016-02-25',1)
            ],remainders.get())
    
    def test_dup_dates_remainder(self):
        remainders=self.setupProvider([
                (1,'2016-02-25',3),
                (2,'2016-02-25',1),
                (1,'2016-01-24',2),
                (2,'2016-02-27',4),
                ])
        self.assertEqual([
                (1,'2016-02-25',3),
                (2,'2016-02-27',4),
        ],remainders.get())
    

@unittest.skip("depends on ERP")
class Remainder_ERP_Test(Remainder_Test):

    def tearDown(self):
        self.provider.clean()

    def setupProvider(self,remainders=[]):
        self.provider=provider=RemainderProviderErpTest()
        provider.clean()
        for remainder in remainders:
            provider.set(*remainder)
        return provider


