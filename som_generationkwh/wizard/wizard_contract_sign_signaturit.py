from datetime import date

from osv import osv, fields
from tools.translate import _


class WizardContractSignSignaturit(osv.osv_memory):

    _name = 'wizard.generation.sign.signaturit'

    def start_request(self, cursor, uid, ids, context=None):
        """ Do selected action"""
        if context is None:
            context = {}
        print("Printazooo!")


WizardContractSignSignaturit()