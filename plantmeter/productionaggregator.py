class ProductionAggregator(object):

    def __init__(self,vplant):
        self.vplant=vplant
    
    def getFirstMeasurementDate(self):
        return self.vplant.firstMeasurementDate()

    def getWh(self, start, end):
        return self.vplant.getWh(start, end)

    def getLastMeasurementDate(self):
        return self.vplant.lastMeasurementDate()
