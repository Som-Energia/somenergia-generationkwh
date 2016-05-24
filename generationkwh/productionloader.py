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
    - _appendRightsPerShare with crossed lastDateToCompute and firstDateToCompute
    + _appendRightsPerShare with not enough production for the required days
    + _appendRightsPerShare with not enough plantshares for the required days

"""

from plantmeter.mongotimecurve import addDays, assertLocalDateTime, toLocal
from plantmeter.isodates import assertDate
from .productiontorightspershare import ProductionToRightsPerShare

import datetime
import numpy


class ProductionLoader(object):
    def __init__(self,
            productionAggregator=None, plantShareCurver=None,
            rightsPerShare=None, remainders=None):
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
            nshares, firstDateToCompute, lastRemainder,
            production, plantshares, lastDateToCompute):

        assertDate("firstDateToCompute", firstDateToCompute)
        assertDate("lastDateToCompute", lastDateToCompute)

        nDays = (lastDateToCompute-firstDateToCompute).days+1

        assert nDays > 0, "Empty interval"
        assert 25*nDays<=len(production), (
            "Not enough production data to compute such date interval")
        assert 25*nDays<=len(plantshares), (
            "Not enough plant share data to compute such date interval")

        startIndex=-25*nDays

        userRights, newRemainder = ProductionToRightsPerShare().computeRights(
                production[startIndex:], plantshares[startIndex:], nshares, lastRemainder)
        if self.remainders:
            self.remainders.updateRemainders([
                    [nshares, lastDateToCompute+datetime.timedelta(days=1), newRemainder]])
        if self.rightsPerShare:
            self.rightsPerShare.updateRightsPerShare(
                    nshares, lastDateToCompute, userRights)



    def computeAvailableRights(self):
        remainders = self.remainders.lastRemainders()
        recomputeStart, recomputeStop = self._recomputationInterval(remainders)
        aggregatedProduction = self.productionAggregator.getWh(recomputeStart, recomputeStop)
        plantShareCurve = self.plantShareCurver.hourly(recomputeStart, recomputeStop)
        for n, date, remainder in remainders:
            self._appendRightsPerShare(
                nshares=n,
                firstDateToCompute = date,
                lastRemainder = remainder,
                production = numpy.asarray(aggregatedProduction),
                plantshares = plantShareCurve,
                lastDateToCompute = recomputeStop,
                )

    def retrieveMeasuresFromPlants(self, start, end):
        return self.productionAggregator.updateWh(start, end)

# vim: ts=4 sw=4 et
