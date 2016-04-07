# -*- coding: utf-8 -*-

"""
TODO:
- Llencar la lectura de dades de plantes
- Agafar la primera data de produccio
- Agafar els darrers remainders per cada numero d'accions
+ Calcular l'inici de l'interval de recalcul
+ Calcular la produccio aggregada en un interval (mockup)
+ Deduir la data de final de recalcul (de la longitud de l'anterior)
- Agafar les accions actives de planta a l'interval
- Calcular els rights per share
- Actualitzar els remainders
- Actualitzar els use rights per share

- Calcular la produccio aggregada en un interval (mockup)
"""
from plantmeter.mongotimecurve import addDays
from .userightspershare import UserRightsPerShare

import datetime
def isodate(string):
    return datetime.datetime.strptime(string, '%Y-%m-%d').date()

class ProductionLoader(object):
    def __init__(self, productionAggregator=None, plantShareCurver=None, rightsPerShareProvider=None, userRightsProvider=None, remainderProvider=None):
        self.productionAggregator = productionAggregator
        self.plantShareCurver = plantShareCurver
        self.rightsPerShareProvider = rightsPerShareProvider
        self.userRightsProvider = UserRightsPerShare()
        self.remainderProvider = remainderProvider

    def startPoint(self, startDateOfProduction, remainders):
        if not remainders:
            return startDateOfProduction
        return min(
            date
            for shares, date, remainderwh in remainders
            )
    
    def endPoint(self, intervalStart, curve):
        return intervalStart+datetime.timedelta(days=len(curve)//25)
 
    def getRecomputeStart(self):
        firstMeasurement = self.productionAggregator.getFirstMeasurementDate()
        remainders = self.remainderProvider.get()
        return (self.startPoint(firstMeasurement, remainders), remainders)
        
    def appendRightsPerShare(self,
            nshares, lastComputedDate, lastRemainder, production, plantshares, lastProductionDate):
        import numpy
        userRights, newRemainder = self.userRightsProvider.computeRights(
            production, plantshares, nshares, lastRemainder)
        recomputeStop = addDays(lastComputedDate, len(production)//25)
        self.remainderProvider.set(nshares, recomputeStop, newRemainder)
        self.rightsPerShareProvider.updateRightsPerShare(
            nshares, addDays(lastComputedDate,1), userRights)



    def doit(self):
        recomputeStop = self.productionAggregator.getLastMeasurementDate()
        recomputeStart, remainders = self.getRecomputeStart()
        aggregatedProduction = self.productionAggregator.getWh(recomputeStart, recomputeStop)
        plantShareCurve = self.plantShareCurver.hourly(recomputeStart, recomputeStop)
        for n, date, remainder in remainders:
            self.appendRightsPerShare(
                nshares=n,
                lastComputedDate = date,
                lastRemainder = remainder,
                production = aggregatedProduction[:],
                plantshares = plantShareCurve[:],
                lastProductionDate = recomputeStop,
                )

            userRights, newRemainder = self.userRightsProvider.computeRights(
                aggregatedProduction, plantShareCurve, n, remainder)
            self.remainderProvider.set(n, recomputeStop, newRemainder)
            self.rightsPerShareProvider.updateRightsPerShare(n, recomputeStart, userRights)
    

# vim: ts=4 sw=4 et
