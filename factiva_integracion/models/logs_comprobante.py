# -*- coding: utf-8 -*-
from odoo import api, fields, models

from . commons import *


class LogsComprobante(models.Model):
    _name = 'logs.comprobante'
    _order = 'fecha,id'

    invoice_id = fields.Many2one('account.invoice', readonly=True)
    fecha = fields.Datetime(string='Fecha')
    descripcion = fields.Char(string='Descripción')
    estado_ini = fields.Selection(ESTADOS_INTEGRACION, string='Estado Inicial')
    estado_fin = fields.Selection(ESTADOS_INTEGRACION, string='Estado Final')
    descripcion_detallada = fields.Text("Descripción Detallada")
    json_envio = fields.Text(string='Json Envio')
    json_rpta = fields.Text(string='Json Rpta')