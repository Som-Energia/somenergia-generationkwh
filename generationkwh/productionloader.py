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
- Protecting against weird cases
    + _appendRightsPerShare receives not a local datetime
    - _appendRightsPerShare with crossed lastProductionDate and lastComputedDate
    - _appendRightsPerShare with not enough production for the required days
    - _appendRightsPerShare with not plantshares production for the required days
- IMPORTANT: Review: set semantics for the date in remainders (either last computed or
    next to be computed) and ensure all the code is consequent.
    My bet (DGG) is that "next to be computed" is more convenient.
    - Starting a new line for nshares by setting a 0 reminder at a given date
    - Finding the start date to retrieve production on order to recompute
    - Finding the production slice to consider on the recompute for a given nshare
    - Setting the new reminder date
    - lastComputedDate is not consistent semantics

"""

from plantmeter.mongotimecurve import addDays, assertLocalDateTime
from .productiontorightspershare import ProductionToRightsPerShare

import datetime
def isodate(string):
    return datetime.datetime.strptime(string, '%Y-%m-%d').date()

class ProductionLoader(object):
    def __init__(self, productionAggregator=None, plantShareCurver=None, rightsPerShare=None, remainders=None):
        self.productionAggregator = productionAggregator
        self.plantShareCurver = plantShareCurver
        self.rightsPerShare = rightsPerShare
        self.remainders = remainders

    def startPoint(self, startDateOfProduction, remainders):
        if not remainders:
            return startDateOfProduction
        return min(
            date
            for shares, date, remainderwh in remainders
            )
    
    def endPoint(self, intervalStart, curve):
        return intervalStart+datetime.timedelta(days=len(curve)//25)

    def _recomputationInterval(self, remainders):
        """
            Returns the first and last day of production required to
            recompute rights given the remainders which have information
            of the last computed rights date for each given number of shares.
        """
        firstMeasurement = self.productionAggregator.getFirstMeasurementDate()
        return (
            self.startPoint(firstMeasurement, remainders), 
            self.productionAggregator.getLastMeasurementDate()
            )


    def _appendRightsPerShare(self,
            nshares, lastComputedDate, lastRemainder,
            production, plantshares, lastProductionDate):

        assertLocalDateTime("lastProductionDate", lastProductionDate)
        assertLocalDateTime("lastComputedDate", lastComputedDate)

        startIndex=-25*(lastProductionDate.date()-lastComputedDate.date()).days
        userRights, newRemainder = ProductionToRightsPerShare().computeRights(
                production[startIndex:], plantshares[startIndex:], nshares, lastRemainder)
        self.remainders.set(nshares, lastProductionDate, newRemainder)
        self.rightsPerShare.updateRightsPerShare(
            nshares, addDays(lastComputedDate,1), userRights)



    def computeAvailableRights(self):
        remainders = self.remainders.get()
        recomputeStart, recomputeStop = self._recomputationInterval(remainders)
        aggregatedProduction = self.productionAggregator.getWh(recomputeStart, recomputeStop)
        plantShareCurve = self.plantShareCurver.hourly(recomputeStart, recomputeStop)
        for n, date, remainder in remainders:
            self._appendRightsPerShare(
                nshares=n,
                lastComputedDate = date,
                lastRemainder = remainder,
                production = aggregatedProduction,
                plantshares = plantShareCurve,
                lastProductionDate = recomputeStop,
                )

    def retrieveMeasuresFromPlants(self):
        "TODO"





# vim: ts=4 sw=4 et
