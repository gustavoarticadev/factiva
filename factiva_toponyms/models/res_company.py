# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    departamento_id = fields.Many2one(
        'factiva.departamento',
        string=u'Departamento',
        inverse='_inverse_departamento_id'
    )
    provincia_id = fields.Many2one(
        'factiva.provincia',
        string=u'Provincia',
        inverse='_inverse_provincia_id'
    )
    distrito_id = fields.Many2one(
        'factiva.distrito',
        string=u'Distrito',
        inverse='_inverse_distrito_id'
    )

    def _inverse_departamento_id(self):
        for company in self:
            company.partner_id.departamento_id = company.departamento_id

    def _inverse_provincia_id(self):
        for company in self:
            company.partner_id.provincia_id = company.provincia_id

    def _inverse_distrito_id(self):
        for company in self:
            company.partner_id.distrito_id = company.distrito_id

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if not self.country_id \
                or self.departamento_id.country_id != self.country_id:
            self.departamento_id = False
            self.provincia_id = False
            self.distrito_id = False

    @api.onchange('departamento_id')
    def _onchange_departamento_id(self):
        if not self.departamento_id \
                or self.provincia_id.departamento_id != self.departamento_id:
            self.provincia_id = False
            self.distrito_id = False

    @api.onchange('provincia_id')
    def _onchange_provincia_id(self):
        if not self.provincia_id \
                or self.distrito_id.provincia_id != self.provincia_id:
            self.distrito_id = False

    # Funcion reemplazada para considerar los nuevos campos en el onchange
    @api.model
    def _address_fields(self):
        """ Returns the list of address fields that are synced from the parent
        when the `use_parent_address` flag is set. """
        address_fields = (
            'street', 'street2', 'zip', 'city', 'departamento_id',
            'country_id', 'provincia_id', 'distrito_id'
        )
        return list(address_fields)

    # Onchange para actualizar el codigo de distrito
    @api.onchange('distrito_id')
    def onchange_distrito_id(self):
        if self.distrito_id:
            state = self.distrito_id.provincia_id.departamento_id.code \
                    + self.distrito_id.provincia_id.code \
                    + self.distrito_id.code
            self.zip = state
        else:
            self.zip = False

    @api.multi
    def _display_address(self, without_company=False):
        res = super(Company, self)._display_address()
        address_format = (
            "%(street)s"
            "\n%(street2)s"
            "\n%(department_name)s-%(province_name)s-%(district_name)s %(zip)s"
            "\n%(country_name)s"
        )
        args = {
            # 'district_code': self.distrito_id.code or '',
            'district_name': self.distrito_id.name or '',
            # 'province_code': self.provincia_id.code or '',
            'province_name': self.provincia_id.name or '',
            # 'state_code': self.departamento_id.code or '',
            'department_name': self.departamento_id.name or '',
            # 'country_code': self.country_id.code or '',
            'country_name': self.country_id.name or '',
            'company_name': self.parent_name or '',
        }
        for field in self._address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args
