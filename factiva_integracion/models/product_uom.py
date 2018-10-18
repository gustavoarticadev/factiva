# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models


class ProductUoM(models.Model):
    _inherit = 'product.uom'

    code = fields.Char(string='Código Internacional')
