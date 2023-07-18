#-*- coding: utf8 -*-

"""
Parameters for the Generation kWh investment model
"""

shareValue = 100 # price in € for a sigle GkWh share
maxAmountInvested = 100000 # Max amount invested per parnter

# Must decide which constant survives in the next refactor
waitYears = 1 # number of years until a Gkwh investment comes effective
waitingDays = 365 # number of days until a Gkwh investment comes effective
waitDaysBeforeDivest = 30 #no allow divest before 30 deays from payment_date
irpfTaxValue = 0.19

expirationYears = 25 # number of active years for a Gkwh investment 
mandateName = "PRESTEC GENERATION kWh"
creditorCode = 'ES24000F55091367'
journalCode = 'GENKWH'

investmentProductCode = 'GENKWH_AE'
irpfProductCode = 'GENKWH_IRPF'
investmentPaymentMode = 'GENERATION kWh'
amortizationPaymentMode = 'GENERATION kWh AMOR'
amortizationReceivablePaymentMode = 'GENERATION kWh AMOR Cobrar'
bridgeAccountCode = '555000000004' # Bridge account to concile payments to the bank

amountForlegalAtt = 5000

mandatePurposeAmorCobrar = "AMORTITZACIO COBRAR GENERATION kWh"
# vim: et sw=4 ts=4
