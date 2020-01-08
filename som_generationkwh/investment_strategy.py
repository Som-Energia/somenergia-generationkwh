# -*- coding: utf-8 -*-

from erpwrapper import ErpWrapper
from generationkwh.isodates import isodate
import generationkwh.investmentmodel as gkwh
from generationkwh.investmentstate import InvestmentState
from datetime import datetime, date

class InvestmentActions(ErpWrapper):

    def create_from_form(self, cursor, uid, partner_id, order_date, amount_in_euros, ip, iban,
            emission=None, context=None):
        print "Estic a InvestmentActions.create_from_form()"
        GenerationkwhInvestment = self.erp.pool.get('generationkwh.investment')

        if amount_in_euros <= 0 or amount_in_euros % gkwh.shareValue > 0:
                raise Exception("Invalid amount")
        iban = GenerationkwhInvestment.check_iban(cursor, uid, iban)

        if not iban:
                raise Exception("Wrong iban")
        if not emission:
            emission = 'emissio_genkwh'

        imd_model = self.erp.pool.get('ir.model.data')
        emission_id = imd_model.get_object_reference(
            cursor, uid, 'som_generationkwh', emission
        )[1]
        Soci = self.erp.pool.get('somenergia.soci')
        member_ids = Soci.search(cursor, uid, [
                ('partner_id','=',partner_id)
                ])
        if not member_ids:
            raise Exception("Not a member")

        bank_id = GenerationkwhInvestment.get_or_create_partner_bank(cursor, uid,
                    partner_id, iban)
        ResPartner = self.erp.pool.get('res.partner')
        ResPartner.write(cursor, uid, partner_id, dict(
            bank_inversions = bank_id,),context)


class GenerationkwhActions(InvestmentActions):

    def create_from_form(self, cursor, uid, partner_id, order_date, amount_in_euros, ip, iban,
            emission=None, context=None):
        super(GenerationkwhActions, self).create_from_form(cursor, uid, partner_id, order_date, amount_in_euros, ip, iban,emission, context)

        print "Estic a GenerationkwhActions.get()"
        GenerationkwhInvestment = self.erp.pool.get('generationkwh.investment')
        ResUser = self.erp.pool.get('res.users')                            
        user = ResUser.read(cursor, uid, uid, ['name'])                 
        IrSequence = self.erp.pool.get('ir.sequence')                       
        name = IrSequence.get_next(cursor,uid,'som.inversions.gkwh')    
                                                                        
        inv = InvestmentState(user['name'], datetime.now())             
        inv.order(                                                      
            name = name,                                                
            date = order_date,                                          
            amount = amount_in_euros,                                   
            iban = iban,                                                
            ip = ip,                                                    
            )                                                           
        investment_id = GenerationkwhInvestment.create(cursor, uid, dict(                  
            inv.erpChanges(),                                           
            member_id = member_ids[0],                                  
            emission_id = emission_id,                                  
        ), context)                                                     
                                                                        
        GenerationkwhInvestment.get_or_create_payment_mandate(cursor, uid,                 
            partner_id, iban, gkwh.mandateName, gkwh.creditorCode)      
                                                                        
        GenerationkwhInvestment.send_mail(cursor, uid, investment_id,                      
            'generationkwh.investment', 'generationkwh_mail_creacio')   

        return investment_id


class AportacionsActions(InvestmentActions):

    def create_from_form(self, cursor, uid, partner_id, order_date, amount_in_euros, ip, iban,
            emission=None, context=None):
        super(AportacionsActions, self).create_from_form(cursor, uid, partner_id, order_date, amount_in_euros, ip, iban,emission, context)

        print "Estic a AportacionsActions.get()"
        GenerationkwhInvestment = self.erp.pool.get('generationkwh.investment')

        if not emission:
            emission = 'emissio_apo'

        IrModelData = self.erp.pool.get('ir.model.data')
        emission_id = IrModelData.get_object_reference(
            cursor, uid, 'som_generationkwh', emission
        )[1]

        Soci = self.erp.pool.get('somenergia.soci')
        member_ids = Soci.search(cursor, uid, [
                ('partner_id','=',partner_id)
                ])
        ResUser = self.erp.pool.get('res.users')
        user = ResUser.read(cursor, uid, uid, ['name'])
        IrSequence = self.erp.pool.get('ir.sequence')
        name = IrSequence.get_next(cursor,uid,'seq.som.aportacions')

        inv = InvestmentState(user['name'], datetime.now())
        inv.order(
            name = name,
            date = order_date,
            amount = amount_in_euros,
            iban = iban,
            ip = ip,
            )
        investment_id = GenerationkwhInvestment.create(cursor, uid, dict(
            inv.erpChanges(),
            member_id = member_ids[0],
            emission_id = emission_id,
        ), context)

        Emission = self.erp.pool.get('generationkwh.emission')
        emi_obj = Emission.read(cursor, uid, emission_id)
        GenerationkwhInvestment.get_or_create_payment_mandate(cursor, uid,
            partner_id, iban, emi_obj['mandate_name'], gkwh.creditorCode)

        GenerationkwhInvestment.send_mail(cursor, uid, investment_id,
            'investment.aportacio', 'aportacio_mail_creacio')

        return investment_id
