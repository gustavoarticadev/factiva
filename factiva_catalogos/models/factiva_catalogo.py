# -*- coding: utf-8 -*-
from odoo import api, fields, models


class FactivaCatalogo(models.Model):
    _name = 'factiva.catalogo'
    _order = 'code asc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string=u'Descripción')
    code = fields.Char(string=u'Código')
    active = fields.Boolean(string=u'Activo')

    # Special behavior for this field: res.company.search() will only return
    # the companies available to the current user (should be the user's
    # companies?), when the user_preference context is set.
    company_id = fields.Many2one(
        'res.company', string='Company',
        required=True, default=_get_company,
        help='The company this user is currently working for.',
        context={'user_preference': True}
    )

    @api.multi
    @api.depends('code', 'name')
    def name_get(self):
        result = []
        for table in self:
            l_name = table.code and table.code + ' - ' or ''
            l_name += table.name
            result.append((table.id, l_name))
        return result


class FactivaCatalogo01(models.Model):
    _name = 'factiva.catalogo.01'
    _inherit = 'factiva.catalogo'
    _description = u'CÓDIGO DE TIPO DE DOCUMENTO'


class FactivaCatalogo05(models.Model):
    _name = 'factiva.catalogo.05'
    _inherit = 'factiva.catalogo'
    _description = u'CÓDIGOS DE TIPOS DE TRIBUTOS'

    descripcion = fields.Char(string=u'Descripción')
    codigo_internacional = fields.Char(
        string=u'Código Internacional de Impuesto')


class FactivaCatalogo06(models.Model):
    _name = 'factiva.catalogo.06'
    _inherit = 'factiva.catalogo'
    _description = u'CÓDIGOS DE TIPOS DE DOCUMENTOS DE IDENTIDAD'

    consulta_ws = fields.Boolean(
        string='Consulta por WS',
        help='Habilitado para consulta por WebService'
    )
    url_ws = fields.Char(string='URL WS')


class FactivaCatalogo07(models.Model):
    _name = 'factiva.catalogo.07'
    _inherit = 'factiva.catalogo'
    _description = u'CÓDIGOS DE TIPO DE AFECTACIÓN DEL IGV'

    no_onerosa = fields.Boolean(string=u'No onerosa')
    type = fields.Selection(
        [('gravado', 'Gravado'),
         ('exonerado', 'Exonerado'),
         ('inafecto', 'Inafecto')], string=u'Tipo'
    )


class FactivaCatalogo08(models.Model):
    _name = 'factiva.catalogo.08'
    _inherit = 'factiva.catalogo'
    _description = u'CÓDIGOS DE TIPOS DE SISTEMA DE CÁLCULO DEL ISC'


class FactivaCatalogo09(models.Model):
    _name = 'factiva.catalogo.09'
    _inherit = 'factiva.catalogo'
    _description = u'CÓDIGOS DE TIPO DE NOTA DE CRÉDITO ELECTRÓNICA'


class FactivaCatalogo10(models.Model):
    _name = 'factiva.catalogo.10'
    _inherit = 'factiva.catalogo'
    _description = u'CÓDIGOS DE TIPO DE NOTA DE DÉBITO ELECTRÓNICA'


class FactivaCatalogo16(models.Model):
    _name = 'factiva.catalogo.16'
    _inherit = 'factiva.catalogo'
    _description = u'CÓDIGOS – TIPO DE PRECIO DE VENTA UNITARIO'
