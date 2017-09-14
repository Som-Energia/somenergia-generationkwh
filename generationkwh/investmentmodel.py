#-*- coding: utf8 -*-

"""
Parameters for the Generation kWh investment model
"""

shareValue = 100 # price in € for a sigle GkWh share

# Must decide which constant survives in the next refactor
waitYears = 1 # number of years until a Gkwh investment comes effective
waitingDays = 365 # number of days until a Gkwh investment comes effective

expirationYears = 25 # number of active years for a Gkwh investment 
mandateName = "PRESTEC GENERATION kWh"
creditorCode = 'ES24000F55091367'
journalCode = 'GENKWH'

investmentProductCode = 'GENKWH_AE'
amortizationProductCode = 'GENKWH_AMOR'
investmentPaymentMode = 'GENERATION kWh'
amortizationPaymentMode = 'GENERATION kWh AMOR'
bridgeAccountCode = '555000000004' # Bridge account to concile payments to the bank


# vim: et sw=4 ts=4
