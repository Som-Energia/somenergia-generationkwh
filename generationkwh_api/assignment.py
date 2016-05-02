# -*- coding: utf-8 -*-

from osv import osv, fields
from .erpwrapper import ErpWrapper
import datetime
from yamlns import namespace as ns

# TODO: sort rights sources if many members assigned the same contract
# TODO: Filter out inactive contracts

def _sqlfromfile(sqlname):
    from tools import config
    import os
    sqlfile = os.path.join(
        config['addons_path'], 'generationkwh_api',
            'sql', sqlname+'.sql')
    with open(sqlfile) as f:
        return f.read()

class GenerationkWhAssignment(osv.osv):

    _name = 'generationkwh.assignment'

    _columns = dict(
        contract_id=fields.many2one(
            'giscedata.polissa',
            'Contract',
            required=True,
            help="Contract which gets rights to use generated kWh",
            ),
        member_id=fields.many2one(
            'somenergia.soci',
            'Member',
            required=True,
            help="Member who bought Generation kWh shares and assigns them",
            ),
        priority=fields.integer(
            'Priority',
            required=True,
            help="Assignment precedence. "
                "This assignment won't use rights generated on dates that "
                "have not been invoiced yet by assignments "
                "of the same member having higher priority "
                "(lower the value, higher the priority).",
            ),
        end_date=fields.date(
            'Expiration date',
            help="Date at which the rule is no longer active",
            ),
        )

    def add(self, cr, uid, assignments, context=None):
        for contract_id, member_id, priority in assignments:
            same_polissa_member = self.search(cr, uid, [
                '|', ('end_date', '<', str(datetime.date.today())),
                    ('end_date','=',False),
                ('contract_id', '=', contract_id),
                ('member_id', '=', member_id),
            ], context = context)
            if same_polissa_member:
                self.write(cr,uid,
                    same_polissa_member,
                    dict(
                        end_date=str(datetime.date.today()),
                    ),
                    context=context,
                )
            self.create(cr, uid, {
                'contract_id': contract_id,
                'member_id': member_id,
                'priority': priority,
            }, context=context)

    def expire(self, cr, uid, assignments, context=None):
        for contract_id, member_id in assignments:
            same_polissa_member = self.search(cr, uid, [
                '|', ('end_date', '<', str(datetime.date.today())),
                    ('end_date','=',False),
                ('contract_id', '=', contract_id),
                ('member_id', '=', member_id),
            ], context = context)
            if same_polissa_member:
                self.write(cr,uid,
                    same_polissa_member,
                    dict(
                        end_date=str(datetime.date.today()),
                    ),
                    context=context,
                )

    def createDefaultForMembers(self, cr, uid, member_ids, context=None):
        """ Creates default contract assignments for the given members.
        """
        contracts = self.sortedDefaultContractsForMember(cr, uid, member_ids, context)
        self.createOnePrioritaryAndManySecondaries(cr, uid, contracts, context)

    def sortedDefaultContractsForMember(self, cr, uid, member_ids, context=None):
        """ PRIVATE.
            Gets default contract to assign for a given member ids
            Criteria are:
            - Contracts the member being the payer first,
              then the ones the member is owner but not payer.
            - Within both groups the ones with more anual use first.
            - If all criteria match, use contract creation order
        """
        sql = _sqlfromfile('default_contracts_to_assign')
        cr.execute(sql, dict(socis=tuple(member_ids)))
        return [
            (contract,member)
            for contract,member,_,_ in cr.fetchall()
            if contract
            ]

    def createOnePrioritaryAndManySecondaries(self, cr, uid, assignments, context=None):
        """ PRIVATE.
            Creates assignments from a list of pairs of contract_id, member_id.
            The first pair of a member is the priority 0 and the 
            remaining contracts of the same member are inserted as priority zero.
            @pre contracts of the same member are together
            """
        formerMember=None
        members = list(set(member for contract,member in assignments))
        ids = self.search(cr, uid, [
            ('member_id','in',members),
            ],context=context)
        self.unlink(cr, uid, ids, context=context)
        for contract, member in assignments:
            self.create(cr, uid, dict(
                contract_id = contract,
                member_id = member,
                priority = 0 if member!=formerMember else 1,
                ), context=context)
            formerMember=member
    
    def dropAll(self, cr, uid, context=None):
        """Remove all records"""
        ids = self.search(cr, uid, [
            ],context=context)
        for a in self.browse(cr, uid, ids, context=context):
            a.unlink()


    def availableAssigmentsForContract(self, cursor, uid, contract_id, context=None):
        assignmentProvider = AssignmentProvider(self, cursor, uid, context)
        #Conversion of ns to dict in order to marshall to XML-RPC
        return [dict(assign) for assign in assignmentProvider.seek(contract_id)]


GenerationkWhAssignment()


class AssignmentProvider(ErpWrapper):

    def seek(self, contract_id):
        """
            Returns the sources available GenkWh rights sources for a contract
            and the earliest date you can use rights from it.
        """
        sql = _sqlfromfile('right_sources_for_contract')
        self.cursor.execute(sql, dict(contract_id=contract_id))
        return [
            ns(
                member_id=member_id,
                last_usable_date=last_usable_date,
            )
            for member_id, last_usable_date, _
            in self.cursor.fetchall()
            ]



