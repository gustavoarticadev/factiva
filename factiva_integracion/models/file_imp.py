# -*- coding: utf-8 -*-

from odoo import api, fields, models


class FileImp(models.TransientModel):
    _name = 'file.imp'

    filecontent = fields.Binary(string='Impresión')
