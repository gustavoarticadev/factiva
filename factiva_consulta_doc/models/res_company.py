# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models

from odoo.tools.translate import _
from odoo.exceptions import UserError
from . commons import *

_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = 'res.company'

    tipo_doc_id = fields.Many2one(
        'factiva.catalogo.06',
        string='Tipo Doc.',
        inverse='_inverse_tipo_doc_id'
    )

    def _inverse_tipo_doc_id(self):
        for company in self:
            company.partner_id.tipo_doc_id = company.tipo_doc_id

    @api.onchange('vat')
    def _onchange_vat(self):
        if (self.tipo_doc_id and self.tipo_doc_id.code == '6'
                and self.tipo_doc_id.consulta_ws and self.vat):
            self.validar_ruc(self.vat)
            if self.es_duplicado(self.vat, self.id, self.parent_id):
                raise UserError(_('Documento existente.'))
            url = self.tipo_doc_id.url_ws
            res = consulta_tipo_doc_ws(url, self.vat)
            if not res['error']:
                data = res['data'][0] if len(res['data']) > 0 else False
                if data:
                    if data['nRazonSocial'] != u'-':
                        self.name = data['nRazonSocial']
                    self.street = build_street_ws(data)
                    self.street2 = build_street2_ws(data)
                    dep, prov, dist = self.ubigeo_ws(data['ubigeo'])
                    self.country_id = self.env.user.company_id.country_id.id
                    self.departamento_id = dep.id
                    self.provincia_id = prov.id
                    self.distrito_id = dist.id
        if self.tipo_doc_id and self.tipo_doc_id.code == '1' and self.vat:
            self.validar_dni(self.vat)

    def es_duplicado(self, vat=False, _id=False, parent=False):
        if not _id:
            if not parent:
                if self.search_count([('vat', '=', vat)]) > 0:
                    return True
            elif vat != parent.vat:
                if self.search_count([('vat', '=', vat),
                                      '|', ('parent_id', '!=', parent.id),
                                      ('parent_id', '=', False)]) > 0:
                    return True
        else:
            if not parent:
                if self.search_count([('vat', '=', vat),
                                      ('id', '!=', _id)]) > 0:
                    return True
            elif self.search_count([('vat', '=', vat),
                                    ('id', '!=', _id),
                                    ('parent_id', '!=', parent.id)]):
                return True

    def validar_ruc(self, ruc):
        pattern_ruc = "^[0-9]{11}$"
        suma = 0
        count = 10
        multiplos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        if ruc:
            if re.match(pattern_ruc, ruc):
                band = False
                n = int(int(ruc)/10)
                while count > 0:
                    suma = suma+(n % 10)*multiplos[count-1]
                    n = int(n/10)
                    count = count-1
                val = 11-suma % 11
                ultimo_digito = int(ruc) % 10
                if val == 10:
                    if ultimo_digito == 0:
                        band = True
                else:
                    if val == 11:
                        if ultimo_digito == 1:
                            band = True
                    else:
                        if val == ultimo_digito:
                            band = True
                if band is False:
                    raise UserError(_('El R.U.C. ingresado no es válido.'))
            else:
                raise UserError(_('El R.U.C. es un valor '
                                  'numérico de 11 dígitos.'))

    def validar_dni(self, dni):
        pattern_dni = "^[0-9]{8}$"
        if dni:
            if not re.match(pattern_dni, dni):
                raise UserError(_('El DNI. es un valor '
                                  'numérico de 8 dígitos.'))

    def ubigeo_ws(self, ubigeo):
        if len(ubigeo) == 6:
            dep, prov, dist = ubigeo[:2], ubigeo[2:4], ubigeo[4:6]
            departento_obj = (
                    self.env['factiva.departamento'].search(
                        [('code', '=', dep)]
                    )
                    or False
            )
            provincia_obj = (
                    self.env['factiva.provincia'].search(
                        [('code', '=', prov),
                         ('departamento_id', '=', departento_obj.id)],
                        limit=1
                    )
                    or False
            )
            distrito_obj = (
                    self.env['factiva.distrito'].search(
                        [('code', '=', dist),
                         ('provincia_id', '=', provincia_obj.id)],
                        limit=1
                    )
                    or False
            )
            return departento_obj, provincia_obj, distrito_obj
