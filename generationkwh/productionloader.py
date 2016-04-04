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

import datetime
def isodate(string):
    return datetime.datetime.strptime(string, '%Y-%m-%d').date()

class ProductionLoader(object):
    def __init__(self, productionAggregator=None):
        self.productionAggregator = productionAggregator

    def startPoint(self, startDateOfProduction, remainders):
        if not remainders:
            return startDateOfProduction
        return min(
            date
            for shares, date, remainderwh in remainders
            )
    def endPoint(self, intervalStart, curve):
        return intervalStart+datetime.timedelta(days=len(curve)//25)
 


    def doit(self):
        firstMeasurement = self.productionAggregator.getFirstMeasurementDate()
        remainders = self.remainderProvider.get()
        recomputeStart = self.startPoint(firstMeasurement, remainders)
        aggregatedProduction = self.productionAggregator.getWh(recomputeStart)
        recomputeStop = self.endPoint(recomputeStart, aggregatedProduction)
        activePlantShareCurve = self.activePlantShareCurver.get(recomputeStart, recomputeStop)
        userRightsProvider = UserRightsPerShare()
        for n, date, remainder in remainders:
            userRights, newRemainder = userRightsProvider.computeRights(
                aggregatedProduction, activePlantShareCurve, n, remainder)
            self.remainderProvider.set(n, recomputeStop, newRemainder)
            userRightsProvider.write(n, recomputeStart, userRights)
        

# vim: ts=4 sw=4 et
