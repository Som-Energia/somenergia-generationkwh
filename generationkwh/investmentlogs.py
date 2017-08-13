# -*- coding: utf-8 -*- 
''' Functions to write logs from Investment'''

def log_formfilled(data):
    return (
        u'[{create_date} {user}] '
        u"FORMFILLED: Formulari omplert des de la IP {ip}, Quantitat: {amount} €, IBAN: {iban}\n"
        .format(
            **data
        ))

def log_corrected(data):
    return (
        u'[{create_date} {user}] '
        u'CORRECTED: Quantitat canviada abans del pagament de {oldamount} € a {newamount} €\n'
        .format(
            **data
        ))

def log_charged(data):
    return (
        u'[{create_date} {user}] '
        u"PAID: Pagament de {amount} € remesat al compte {iban} [{move_line_id}]\n"
        .format(
            **data
        ))

def log_refunded(data):
    return (
        u'[{create_date} {user}] '
        u'REFUNDED: Devolució del pagament remesat de {amount} € [{move_line_id}]\n'
        .format(
            **data
        ))

def log_banktransferred(data):
    return (
        u'[{create_date} {user}] '
        u'REPAID: Pagament de {amount} € rebut per transferència bancària [{move_line_id}]\n'
        .format(
            **data
        ))

def log_returned(data):
    return (
        u'[{create_date} {user}] '
        u'RETURNED: Desinversió total\n'
        .format(
            **data
        ))


# vim: et ts=4 sw=4   
