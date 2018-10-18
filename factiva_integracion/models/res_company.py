# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    url_endpoint = fields.Char(string='URL Endpoint')
    api_key = fields.Char(string='Api Key')
    api_secret = fields.Char(string='Api Secret')

    url_documentos = fields.Char(string='Documentos',
                                 default='emission/documents')
    url_summaries = fields.Char(string='Resúmenes',
                                default='emission/summaries')
    url_download = fields.Char(string='Descarga Docs.',
                               default='download/documents')
