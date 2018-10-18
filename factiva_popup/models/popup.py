# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MensajeEmergente(models.TransientModel):
    _name = "mensaje.emergente"

    tipo = fields.Char(
        string='Tipo',
        default=lambda self: self._context.get('tipo', False),
        readonly=True
    )
    mensaje = fields.Char(
        string='Mensaje',
        default=lambda self: self._context.get('mensaje', False),
        readonly=True
    )
    mensaje_detallado = fields.Char(
        string='Mensaje Detallado',
        default=lambda self: self._context.get('mensaje_detallado', False),
        readonly=True
    )

    def get_mensaje(self, tipo=False, mensaje=False, mensaje_detallado=False):
        form_id = self.env.ref('factiva_popup.mensaje_emergente_view').id
        domain = "[]"
        return {
            'type': 'ir.actions.act_window',
            'name': "Mensaje",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'mensaje.emergente',
            'view_id': False,
            'views': [(form_id, 'form')],
            'target': 'new',
            'nodestroy': True,
            'domain': domain,
            'context': {
                'tipo': _(tipo or ''),
                'mensaje': _(mensaje or ''),
                'mensaje_detallado': _(mensaje_detallado or ''),
            }
        }
