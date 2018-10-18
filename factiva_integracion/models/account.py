# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    es_electronica = fields.Boolean(string='Es Electrónica', default=False)
    tipo_doc_id = fields.Many2one('factiva.catalogo.01',
                                  domain=[('active', '=', True)],
                                  string='Tipo Doc. SUNAT')
    tipo_doc_code = fields.Char(related='tipo_doc_id.code',
                                string='Tipo Doc. Code')
    tipo_doc_rel_id = fields.Many2one('factiva.catalogo.01',
                                  domain=[('active', '=', True)],
                                  string='Tipo Doc. Rel. SUNAT')
    tipo_doc_rel_code = fields.Char(related='tipo_doc_rel_id.code',
                                string='Tipo Doc. Rel. Code')


class AccountTax(models.Model):
    _inherit = 'account.tax'

    tipo_imp_sunat = fields.Many2one('factiva.catalogo.05',
                                     string="Código Impuesto SUNAT")
    afect_igv = fields.Many2one('factiva.catalogo.07',
                                string="Código Afectación de IGV")
