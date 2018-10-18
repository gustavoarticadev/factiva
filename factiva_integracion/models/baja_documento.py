# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

from . commons import *

_logger = logging.getLogger(__name__)


class BajaDocumento(models.Model):
    _name = 'baja.documento'

    def _default_name(self):
        if 'name' in self._context:
            return self._context.get('name')

    def _default_fecha(self):
        if 'fecha' in self._context:
            return self._context.get('fecha')
        else:
            return fields.Datetime.now()

    def _default_resp_estado_emision(self):
        if 'resp_estado_emision' in self._context:
            return self._context.get('resp_estado_emision')
        else:
            return 'xenviar'

    def _default_user_id(self):
        if 'user_id' in self._context:
            return self._context.get('user_id')
        else:
            return self.env.user

    name = fields.Char(
        string='Código',
        default=_default_name
    )
    invoice_id = fields.Many2one(
        'account.invoice',
        string='Doc. Ref',
        default=lambda self: self._context.get('invoice_id', False)
    )
    fecha = fields.Datetime(
        string='Fecha Generación',
        default=_default_fecha
    )
    motivo = fields.Char(
        string='Motivo',
        default=lambda self: self._context.get('motivo', False)
    )
    json_envio = fields.Text(string='Json envío')

    resp_id_resumen = fields.Char(
        string='ID. Resumen',
        default=lambda self: self._context.get('resp_id_resumen', False)
    )
    resp_id_ticket = fields.Char(
        string='ID. Ticket',
        default=lambda self: self._context.get('resp_id_ticket', False)
    )
    resp_estado_emision = fields.Selection(
        ESTADOS_INTEGRACION,
        default=_default_resp_estado_emision,
        string='Estado Emisión'
    )
    resp_observaciones = fields.Text(
        string='Observaciones',
        default=lambda self: self._context.get('resp_observaciones', False)
    )
    company_id = fields.Many2one(
        'res.company',
        related='invoice_id.company_id',
        string='Compañía',
    )
    json_resp = fields.Text(string='Json Respuesta')
    user_id = fields.Many2one(
        'res.users',
        default=_default_user_id,
        string='Usuario'
    )

    consulta_id = fields.Char(string='ID de Consulta', compute='_compute_consulta_id')

    @api.depends('company_id', 'resp_id_resumen')
    def _compute_consulta_id(self):
        if self.company_id and self.resp_id_resumen:
            return (self.company_id.tipo_doc_id.code
                    + self.company_id.vat
                    + self.resp_id_resumen)
        return False

    @api.multi
    def action_comm_baja(self):
        access_token = token(self.company_id.url_endpoint,
                             self.company_id.api_key,
                             self.company_id.api_secret)
        documento = self.invoice_id
        if self.company_id:
            seq = self.env['ir.sequence'].with_context(
                force_company=self.company_id.id
            ).next_by_code('seq.baja.documento') or ''
        else:
            seq = self.env['ir.sequence'].next_by_code('seq.baja.documento')\
                  or ''
        _logger.info(documento)
        _logger.info(seq)
        serie, correlativo = documento.number.split('-')
        detalle = [{
            'serie': serie,
            'motivo': self.motivo,
            'correlativo': int(correlativo),
            'tipoDocumento': documento.journal_id.tipo_doc_id.code,
        }]
        resumen = {
            'id': self.id,
            'nombreEmisor': self.company_id.name,
            'numDocEmisor': self.company_id.vat,
            'tipoDocEmisor': self.company_id.tipo_doc_id.code,
            'fechaReferente': documento.date_invoice,
        }
        data = {
            'detalle': detalle,
            'resumen': resumen,
            'tipoResumen': 'RA',
            'idTransaccion': 'RA' + '-' + self.company_id.vat + seq,
            'fechaGeneracion': self.fecha[:10],
        }
        self.name = 'RA' + '-' + self.company_id.vat + seq
        _logger.info(json.dumps(data, indent=4))

        self.json_envio = data
        rpta = send(
            self.company_id.url_endpoint,
            json.dumps(data, indent=4),
            access_token,
            self.company_id.url_summaries
        )
        _logger.info(rpta)

        if 'error' in rpta:
            data_rpta = rpta['data'].json()
            _logger.info(json.dumps(data_rpta, indent=4))
            if 'errors' in data_rpta:
                errors = data_rpta.get('errors')[0]
                return self.env['mensaje.emergente'].get_mensaje(
                    'Factur@ctiva',
                    'Solicitud de Baja Rechazada',
                    ('Status: ' + str(errors.get('status')) + ' '
                     + 'Code: ' + errors.get('code') + ' '
                     + 'Detalle: ' + errors.get('detail'))
                )
        else:
            _logger.info(json.dumps(rpta.json(), indent=4))
            data_rpta = rpta.json().get('data')
            self.json_resp = data_rpta
            if 'idResumen' in data_rpta:
                self.resp_id_resumen = data_rpta.get('idResumen')
            if 'idTicket' in data_rpta:
                self.resp_id_ticket = data_rpta.get('idTicket')
            if 'observaciones' in data_rpta:
                obs = data_rpta.get('observaciones')
                self.resp_observaciones = obs if len(obs) < 501 else obs[:500]
            if ('idResumen', 'idTicket', 'observaciones') in data_rpta:
                self.resp_id_resumen = data_rpta.get('idResumen')
                self.resp_id_ticket = data_rpta.get('idTicket')
                obs = data_rpta.get('observaciones')
                self.resp_observaciones = obs if len(obs) < 501 else obs[:500]
            if 'estadoEmision' in data_rpta:
                if data_rpta.get('estadoEmision') == u'E':
                    self.resp_estado_emision = 'acep_factiva'
                    self.env['logs.comprobante'].create(
                        {
                            'invoice_id': documento.id,
                            'fecha': fields.Datetime.now(),
                            'descripcion': 'En proceso de Baja',
                            'estado_ini': documento.estado_envio,
                            'estado_fin': 'proc_baja',
                            'json_envio': data,
                            'json_rpta': data_rpta,
                        }
                    )
                    self.invoice_id.write({'estado_envio': 'proc_baja'})
                return self.env['mensaje.emergente'].get_mensaje(
                            'Factur@ctiva', 'Enviado a SUNAT', False)
        return True

    def consultar_baja(self, baja, access_token):
        rpta = get(
            baja.company_id.url_endpoint,
            json.dumps({'id': baja.consulta_id}, indent=4),
            access_token,
            baja.company_id.url_summaries
        )
        return rpta

    def procesar_rpta(self, baja, rpta):
        if 'error' in rpta:
            data_rpta = rpta['data'].json()
            if 'estadoEmision' in data_rpta:
                est_emision = data_rpta.get('estadoEmision')
                return 'baja_rechaz_sunat'
        else:
            _logger.info(json.dumps(rpta.json(), indent=4))
            data_rpta = rpta.json().get('data')
            if 'estadoEmision' in data_rpta:
                est_emision = data_rpta.get('estadoEmision')
                return est_emision
    @api.multi
    def _cron_consulta_estado_baja(self, cron=False):
        self.ensure_one()
        access_token = token(self.company_id.url_endpoint,
                             self.company_id.api_key,
                             self.company_id.api_secret)
        if cron:
            res_company = self.env['res.company'].search([])
            for company in res_company:
                baja_ids = self.search(
                    [('resp_estado_emision', '=', 'acep_factiva'),
                     ('company_id', '=', company.id)])
                acep_ids = []
                rech_ids = []
                reenv_ids = []
                for baja in baja_ids:
                    response = self.consultar_baja(baja, access_token)
                    rpta = self.procesar_rpta(response)


    @api.model
    def _cron_restart_sequence(self, sequence_code):
        """
            Cron de reinicio de secuencial de la secuencia, por día debe
            reiniciarse a 1.
        :param: sequence_code, código de la secuencia a reiniciar.
        :return: None
        """
        res_company = self.env['res.company'].search([])
        for company in res_company:
            seq_id = self.env['ir.sequence'].search(
                [('code', '=', sequence_code),
                 ('company_id', 'in', [company.id, False])],
                order='company_id'
            )
            seq_id.number_next_actual = 1
            seq_id._set_number_next_actual()
            _logger.info("Reinicio de la secuencia '%s' para la "
                         "compañía: '%s' a '%s'." %
                         (sequence_code, company.name,
                          seq_id.number_next_actual))
