# -*- coding: utf-8 -*- 
''' Functions to write logs from Investment'''

def log_formfilled(data):
    return (
        u'[{create_date} {user}] '
        u"FORMFILLED: Formulari omplert des de la IP {ip}, Quantitat: {amount} €, IBAN: {iban}\n"
        .format(
            **data
        ))

def log_charged(data):
    return (
        u'[{create_date} {user}] '
        u"PAYED: Pagament de {amount} € remesat al compte {iban}\n"
        .format(
            **data
        ))

# vim: et ts=4 sw=4   
