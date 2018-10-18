# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Departamento(models.Model):
    _name = 'factiva.departamento'

    country_id = fields.Many2one('res.country', string=u'País')
    code = fields.Char(string=u'Código')
    name = fields.Char(string=u'Nombre')


class Provincia(models.Model):
    _name = 'factiva.provincia'

    departamento_id = fields.Many2one(
        'factiva.departamento',
        string='Departamento'
    )
    code = fields.Char(string=u'Código')
    name = fields.Char(string=u'Nombre')


class Distritos(models.Model):
    _name = 'factiva.distrito'

    provincia_id = fields.Many2one('factiva.provincia', string='Provincia')
    code = fields.Char(string=u'Código')
    name = fields.Char(string=u'Nombre')
