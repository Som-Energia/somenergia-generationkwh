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

from .isodates import assertDate
from .productiontorightspershare import ProductionToRightsPerShare

import datetime
import numpy


class RightsGranter(object):
    def __init__(self,
            productionAggregator=None, plantShareCurver=None,
            rightsPerShare=None, remainders=None, rightsCorrection=None):
        self.productionAggregator = productionAggregator
        self.plantShareCurver = plantShareCurver
        self.rightsPerShare = rightsPerShare
        self.remainders = remainders
        self.rightsCorrection = rightsCorrection

    def _olderRemainder(self, remainders):
        if not remainders: return None
        return min(
            date
            for shares, date, remainderwh in remainders
            )

    def _updatableInterval(self, remainders):
        """
            Returns the first and last day of production required to
            recompute rights given the remainders which have information
            of the last computed rights date for each given number of shares.
        """
        return (
            self._olderRemainder(remainders) or
                self.productionAggregator.getFirstMeasurementDate(),
            self.productionAggregator.getLastMeasurementDate()
            )


    def _appendRightsPerShare(self,
            nshares, firstDateToCompute, lastRemainder,
            production, plantshares, lastDateToCompute):

        assertDate("firstDateToCompute", firstDateToCompute)
        assertDate("lastDateToCompute", lastDateToCompute)

        nDays = (lastDateToCompute-firstDateToCompute).days+1

        assert nDays > 0, (
            "Empty interval starting at {} and ending at {}"
                .format(firstDateToCompute, lastDateToCompute))
        assert 25*nDays<=len(production), (
            "Not enough production data to compute such date interval")
        assert 25*nDays<=len(plantshares), (
            "Not enough plant share data to compute such date interval")

        startIndex=-25*nDays

        userRights, newRemainder = ProductionToRightsPerShare().computeRights(
                production[startIndex:], plantshares[startIndex:], nshares, lastRemainder)

        return userRights, newRemainder


    def _updateRights(self, nshares, rights, firstDate, lastDate, remainder, rightsCorrection=None):
        if self.remainders:
            self.remainders.updateRemainders([
                    [nshares, lastDate+datetime.timedelta(days=1), remainder]])
        if self.rightsPerShare:
            self.rightsPerShare.updateRightsPerShare(
                    nshares, firstDate, rights)
        if self.rightsCorrection and rightsCorrection is not None:
            self.rightsCorrection.updateRightsCorrection(
                    nshares, firstDate, rightsCorrection)

    def computeAvailableRights(self,lastDateToCompute=None):
        """
        Recompute pending available rights whenever we have new production
        readings.
        """
        remainders = self.remainders.lastRemainders()
        recomputeStart, recomputeStop = self._updatableInterval(remainders)
        if lastDateToCompute:
            recomputeStop = lastDateToCompute
        aggregatedProduction = self.productionAggregator.get_kwh(recomputeStart, recomputeStop)
        plantShareCurve = self.plantShareCurver.hourly(recomputeStart, recomputeStop)
        log = []
        for n, date, remainder in remainders:
            log.append(
                "Computing rights for members with {} shares from {} to {}"
                .format(n, date, recomputeStop))
            rights, newremainder = self._appendRightsPerShare(
                nshares=n,
                firstDateToCompute = date,
                lastDateToCompute = recomputeStop,
                lastRemainder = remainder,
                production = numpy.asarray(aggregatedProduction),
                plantshares = plantShareCurve,
                )
            self._updateRights(n, rights, date, recomputeStop, newremainder)
            log.append(
                "- {} Wh of remainder from previous days\n"
                "- {} kWh granted\n"
                "- {} Wh of remainder for the next days"
                .format(remainder, sum(rights), newremainder))
        return '\n'.join(log)

    def recomputeRights(self, firstDate, lastDate):
        """
        Recompute pending available rights whenever we have new production
        readings.
        """
        remainders = self.remainders.lastRemainders()
        aggregatedProduction = self.productionAggregator.get_kwh(firstDate, lastDate)
        plantShareCurve = self.plantShareCurver.hourly(firstDate, lastDate)
        log = []
        for n, date, remainder in remainders:
            log.append(
                "Recomputing rights for members with {} shares from {} to {}"
                .format(n, firstDate, lastDate))
            wantedRights, remainder = self._appendRightsPerShare(
                nshares=n,
                firstDateToCompute = firstDate,
                lastDateToCompute = lastDate,
                lastRemainder = 0, # TODO: Should we take the 
                production = numpy.asarray(aggregatedProduction),
                plantshares = plantShareCurve,
                )
            original = self.rightsPerShare.rightsPerShare(n, firstDate, lastDate)
            rights, error = ProductionToRightsPerShare().rectifyRights(original, wantedRights)
            correction = rights - wantedRights
            log.append(
                "- {} kWh granted\n"
                "- {} kWh added\n"
                "- {} kWh kept above the real production\n"
                "- {} kWh of those could be compensated\n"
                "- {} kWh substracted as Wh to the next remainder.\n"
                .format(
                    sum(rights),
                    sum(rights-original),
                    sum(correction[correction>0]),
                    sum(correction[correction<0]),
                    error)
                )
            self._updateRights(n, rights, firstDate, lastDate, remainder-error*1000, correction)
        return '\n'.join(log)









# vim: ts=4 sw=4 et
