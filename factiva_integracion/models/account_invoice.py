# -*- coding: utf-8 -*-
import logging
import pytz
import voluptuous
from voluptuous import Schema, Required, All, Length, ALLOW_EXTRA, Coerce
from dateutil.relativedelta import relativedelta
import re

from odoo import api, fields, models

from . commons import *
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


# mapping invoice type to journal type
TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}

# mapping invoice type to refund type
TYPE2REFUND = {
    'out_invoice': 'out_refund',        # Customer Invoice
    'in_invoice': 'in_refund',          # Vendor Bill
    'out_refund': 'out_invoice',        # Customer Credit Note
    'in_refund': 'in_invoice',          # Vendor Credit Note
}

PATTERN_SERIE_CORRELATIVO = "^\w{4}\-\w+$"


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount',
                 'currency_id', 'global_descuento')
    def _compute_total_amount_sunat(self):
        round_curr = self.currency_id.round
        total_gravado = 0.0
        total_exonerado = 0.0
        total_inafecto = 0.0
        for line in self.invoice_line_ids:
            for tax in line.invoice_line_tax_ids:
                if tax.afect_igv.type == u'gravado':
                    total_gravado += line.quantity * line.price_unit
                elif tax.afect_igv.type == u'exonerado':
                    total_exonerado += line.price_subtotal
                elif tax.afect_igv.type == u'inafecto':
                    total_inafecto += line.price_subtotal
        if self.global_descuento:
            total_gravado = (total_gravado
                             * (100.0 - self.global_descuento)
                             / 100.0)
        self.total_descuentos = sum(
            [line.quantity * line.price_unit * line.discount / 100
             for line in self.invoice_line_ids]
        )
        self.total_descuento_global = (
                (
                    (total_gravado + self.amount_tax)
                    / (1 - self.global_descuento / 100)
                 ) * self.global_descuento / 100)
        self.total_amount_gravado = total_gravado
        self.total_amount_exonerado = total_exonerado
        self.total_amount_inafecto = total_inafecto
        self.total_tax_discount = sum(
            round_curr(line.amount)
            for line in self.tax_line_ids
        ) * self.global_descuento / 100

    @api.model
    def _default_journal(self):
        res = super(AccountInvoice, self)._default_journal()
        # _logger.warning(res)
        if self._context.get('default_journal_id', False):
            return self.env['account.journal'].browse(
                self._context.get('default_journal_id'))
        inv_type = self._context.get('type', 'out_invoice')
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id',
                                       self.env.user.company_id.id)
        domain = [
            ('type', 'in',
             [TYPE2JOURNAL[ty] for ty in inv_types if ty in TYPE2JOURNAL]),
            ('company_id', '=', company_id),
        ]
        if 'out_invoice' in inv_type:
            domain.append(('tipo_doc_code', 'in', ['01', '03', '08']))
        elif 'out_refund' in inv_type:
            domain.append(('tipo_doc_code', 'in', ['07']))
        # _logger.warning(domain)
        # _logger.warning(self.env['account.journal'].search(domain, limit=1))
        return self.env['account.journal'].search(domain, limit=1)

    journal_id = fields.Many2one(
        domain="[('type', 'in', {'out_invoice': ['sale'], "
               "'out_refund': ['sale'], 'in_refund': ['purchase'], "
               "'in_invoice': ['purchase']}.get(type, [])),"
               "('tipo_doc_code', 'in',{'out_invoice': ['01','03','08'],"
               "'out_refund': ['07']}.get(type,[])), "
               "('company_id', '=', company_id)]")
    tipo_doc_id = fields.Char(related='journal_id.tipo_doc_code',
                              string='Code Doc. SUNAT')

    tipo_doc_rel_code = fields.Char(related='journal_id.tipo_doc_rel_code',
                                    string='Code Doc. Rel. SUNAT')

    estado_envio = fields.Selection(
        ESTADOS_INTEGRACION,
        default='xenviar',
        string='Estado Envio SUNAT',
        copy=False
    )
    global_descuento = fields.Float(
        string='Desc. Global (%)',
        default=0.0,
    )
    total_amount_gravado = fields.Monetary(
        string='Total Op. Gravadas',
        default=0.0,
        compute='_compute_total_amount_sunat'
    )
    total_amount_exonerado = fields.Monetary(
        string='Total Op. Exoneradas',
        default=0.0,
        compute='_compute_total_amount_sunat'
    )
    total_amount_inafecto = fields.Monetary(
        string='Total Op. Inafectas',
        default=0.0,
        compute='_compute_total_amount_sunat'
    )
    total_descuentos = fields.Monetary(
        string="Total Descuentos",
        default=0.0,
        compute='_compute_total_amount_sunat'
    )
    total_descuento_global = fields.Monetary(
        string="Total Descuentos Global",
        default=0.0,
        compute='_compute_total_amount_sunat'
    )
    total_tax_discount = fields.Monetary(
        string='Total Descuento Impuesto',
        default=0.0,
        compute='_compute_total_amount_sunat'
    )
    # Nota de Crédito
    tipo_nota_doc_id = fields.Many2one(
        'factiva.catalogo.09',
        string='Tipo Nota Crédito'
    )

    # Nota de Débito
    inv_ndeb_rel_id = fields.Many2one(
        'account.invoice',
        string='Doc. Relacionado'
    )
    tipo_ndeb_id = fields.Many2one(
        'factiva.catalogo.10',
        string='Tipo N. Débito.'
    )
    tipo_ndeb_code = fields.Char(
        related='tipo_ndeb_id.code'
    )
    sustento_ndeb = fields.Char(string='Sustento N. Débito')

    fa_consulta_id = fields.Char(string='Id de consulta F@ctiva',
                                 compute='_compute_fa_consulta_id',
                                 store=True)

    @api.depends('company_id', 'journal_id', 'number')
    def _compute_fa_consulta_id(self):
        for inv in self:
            if inv.company_id and inv.journal_id and inv.number:

                if re.match(PATTERN_SERIE_CORRELATIVO, inv.number):
                    serie, correlativo = inv.number.split('-')
                    formatt = '%(tipo_doc_emisor)s-%(ruc)s-' \
                              '%(tipo_doc_cmp)s-%(serie)s-%(correlativo)s'
                    args = {
                        'tipo_doc_emisor': inv.company_id.tipo_doc_id.code,
                        'ruc': inv.company_id.vat,
                        'tipo_doc_cmp': inv.journal_id.tipo_doc_id.code,
                        'serie': serie,
                        'correlativo': correlativo
                    }
                    # _logger.warning(formatt % args)
                    inv.fa_consulta_id = formatt % args
                else:
                    inv.fa_consulta_id = False
            else:
                inv.fa_consulta_id = False

    def get_direc(self, partner):
        pattern = ''
        args = {}
        if partner.street:
            pattern = pattern + '%(street)s'
            args['street'] = partner.street
        if partner.street2:
            pattern = pattern + ' %(street2)s'
            args['street2'] = partner.street2
        if partner.departamento_id:
            pattern = pattern + ' %(department_name)s'
            args['department_name'] = partner.departamento_id.name
        if partner.provincia_id:
            pattern = pattern + ' - %(province_name)s'
            args['province_name'] = partner.provincia_id.name
        if partner.distrito_id:
            pattern = pattern + ' - %(district_name)s'
            args['district_name'] = partner.distrito_id.name
        direccion = (pattern % args)
        if len(pattern) > 0:
            return str(pattern % args)
        else:
            return str("-")

    @api.multi
    def action_open_logs(self):
        """
            Método que abre una nueva ventana que contiene
            los LOGS de un documento
        """
        tree_id = self.env.ref('factiva_integracion.log_tree_view').id
        id_activo = self.id

        logs_ids = self.env['logs.comprobante'].search(
                [('invoice_id', '=', id_activo)]).ids
        domain = "[('id','in',[" + ','.join(map(str, logs_ids)) + "])]"

        return {
            'type': 'ir.actions.act_window',
            'name': "Listado Logs",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'logs.comprobante',
            'views': [(tree_id, 'tree')],
            'view_id': tree_id,
            'target': 'new',
            'domain': domain,
            'context': {}
        }

    @api.multi
    def action_invoice_open(self):
        super(AccountInvoice, self).action_invoice_open()
        if self.type in ('out_invoice', 'out_refund'):
            return self.action_invoicing()
        else:
            return True

    def validate(self, tipo_doc, data):
        doc = Schema({
            Required('serie'): All(str, Length(min=4, max=4)),
            Required('correlativo'): All(str, Length(min=1, max=8)),
            Required('nombreEmisor'): All(str, Length(min=1, max=100)),
            Required('tipoDocEmisor'): All(str, Length(min=1, max=2),
                                           msg='El tipo de Doc. Emisor debe '
                                               'tener un tamaño entre 1 y 2'),
            Required('numDocEmisor'): All(str, Length(min=1, max=25)),
            'direccionOrigen': All(str, Length(min=1, max=100)),
            'direccionUbigeo': All(str, Length(min=6, max=6)),
            Required('tipoDocReceptor'): All(str, Length(min=1, max=2)),
            Required('numDocReceptor'): All(str, Length(min=1, max=25)),
            Required('nombreReceptor'): All(str, Length(min=1, max=100)),
            # TODO: Verificar si hay problemas en el orden
            Required('tipoMoneda'): All(str, Length(min=3, max=3)),
            'mntNeto': Coerce(float),
            'mntTotalIgv': Coerce(float),
            'mntTotal': Coerce(float),
            'fechaVencimiento': All(str, Length(min=10, max=10)),
            'tipoFormatoRepresentacionImpresa': All(str,
                                                    Length(min=1, max=100)),
        })

        if tipo_doc in '03':
            # Boletas
            doc = doc.extend({
                'direccionDestino': All(str, Length(min=1, max=100)),
            })
        if tipo_doc in ('07', '08'):
            # Nota Crédito
            doc = doc.extend({
                Required('sustento'): All(str, Length(min=1, max=100)),
                Required('tipoMotivoNotaModificatoria'):
                    All(str, Length(min=2, max=2))
            })

        impuesto = Schema(All([{
            'codImpuesto': All(str, Length(min=1, max=4)),
            'montoImpuesto': Coerce(float),
            'tasaImpuesto': Coerce(float),
        }]))
        detalle = Schema(All([{
            Required('cantidadItem'): Coerce(float),
            Required('unidadMedidaItem'): All(str, Length(min=1, max=3)),
            'codItem': All(str, Length(min=1, max=30)),
            Required('nombreItem'): All(str, Length(min=1, max=250)),
            # TODO: No debe ser obligatorio para Notas
            Required('precioItem'): Coerce(float),
            Required('precioItemSinIgv'): Coerce(float),
            Required('montoItem'): Coerce(float),
            # TODO-FIN
            'descuentoMonto': Coerce(float),
            Required('codAfectacionIgv'): All(str, Length(min=2, max=2)),
            'tasaIgv': Coerce(float),
            'montoIgv': Coerce(float),
            Required('idOperacion'): All(str, Length(min=1, max=80))
        }], Length(min=1)))
        descuento = Schema(All({
            'mntTotalDescuentos': Coerce(float),
        }))

        schema = Schema({
            Required('documento'): doc,
            Required('tipoDocumento'): All(str, Length(min=2, max=2)),
            Required('fechaEmision'): All(str, Length(min=10, max=10)),
            Required('idTransaccion'): All(str, Length(min=1)),
            'correoReceptor': str,
            Required('impuesto'): impuesto,
            Required('detalle'): detalle,
            'descuento': descuento,
        })
        if tipo_doc in ('07', '08'):
            referencia = Schema(All([{
                'tipoDocumentoRef': All(str, Length(min=1, max=2)),
                'serieRef': All(str, Length(min=4, max=4)),
                'correlativoRef': All(str, Length(min=1, max=8)),
                'fechaEmisionRef': All(str, Length(min=10, max=10)),
            }]))

            schema = schema.extend({
                'referencia': referencia,
            })
        return schema(data)

    @api.multi
    def action_invoicing(self):

        access_token = token(self.company_id.url_endpoint,
                             self.company_id.api_key,
                             self.company_id.api_secret)
        # _logger.warning('Access Token: %s', access_token.json())

        emisor = self.env.user.company_id
        receptor = self.partner_id

        tipo_doc = self.journal_id.tipo_doc_id.code
        ruc_emisor = emisor.vat
        # Fecha de emision Localizada
        user_tz = pytz.timezone(
            self.env.context.get('tz') or self.env.user.tz or 'UTC')
        today = user_tz.localize(
            fields.Datetime.from_string(self.date_invoice + ' 00:00:00'))
        # today = today.astimezone(pytz.timezone('UTC'))
        today = fields.Datetime.to_string(today)

        # Serie - Correlativo
        if re.match(PATTERN_SERIE_CORRELATIVO, self.number):
            serie, correlativo = self.number.split('-')
        else:
            return self.env['mensaje.emergente'].get_mensaje(
                    'Validación de campos', 'La serie y el correlativo '
                                            'no tienen un patron adecuado '
                                            'para la facturación electrónica. '
                                            'Ejm: XXXX-X')

        if tipo_doc in '01':
            if (receptor.tipo_doc_id.code is False
                    or receptor.vat is False or receptor.name is False):
                return self.env['mensaje.emergente'].get_mensaje(
                    'Validación de campos', 'Es requerida la los datos del'
                                            ' cliente como Nombre, Tipo Doc.,'
                                            ' Num. Doc')
            if receptor.tipo_doc_id.code == u'1':
                return self.env['mensaje.emergente'].get_mensaje(
                        'Validación de campos', 'No se puede emitir Facturas '
                                                'a clientes con DNI.')
        elif self.amount_total_company_signed >= 700 and tipo_doc in '03':
            if (receptor.tipo_doc_id.code is False
                    or receptor.vat is False or receptor.name is False):
                return self.env['mensaje.emergente'].get_mensaje(
                        'Validación de campos', 'Es requerida la los datos del'
                                                ' cliente como Nombre, '
                                                'Tipo Doc., Num. Doc')
        tipo_doc_recep = (receptor.tipo_doc_id.code
                          if receptor.tipo_doc_id.code is not False else '-')
        num_doc_recep = receptor.vat if receptor.vat is not False else '-'
        nom_recep = receptor.name if receptor.name is not False else '-'
        doc = {
            'serie': serie,
            'correlativo': correlativo,
            'nombreEmisor': emisor.name,
            'tipoDocEmisor': emisor.tipo_doc_id.code,
            'numDocEmisor': emisor.vat,
            'direccionOrigen': self.get_direc(emisor),
            'direccionUbigeo': emisor.zip,
            'tipoDocReceptor': tipo_doc_recep,
            'numDocReceptor': num_doc_recep,
            'nombreReceptor': nom_recep,
            "tipoMoneda": self.currency_id.name,
            'fechaVencimiento': self.date_due,
            "tipoFormatoRepresentacionImpresa": "GENERAL",
            "mntNeto": self.total_amount_gravado,
            "mntTotalIgv": self.amount_tax,
            "mntTotal": self.amount_total,
        }

        descuento = {
            'mntTotalDescuentos': self.total_descuentos,
        }
        # Descuento Gobal solo para Facturas 01 y Boletas 03
        # if tipo_doc in (u'01', u'03'):
        #     descuento['mntDescuentoGlobal'] = self.total_descuento_global,
        impuesto = []
        detalle = []
        for tax in self.tax_line_ids:
            impuesto.append({
                "codImpuesto": str(tax.tax_id.tipo_imp_sunat.code),
                "montoImpuesto": tax.amount_total,
                "tasaImpuesto": tax.tax_id.amount / 100
            })

        for item in self.invoice_line_ids:

            if item.invoice_line_tax_ids.price_include:

                if item.invoice_line_tax_ids.amount == 0:
                    montoImpuestoUni = 0
                    base_imponible = item.price_unit
                else:
                    base_imponible = item.price_unit / (
                                1 + (item.invoice_line_tax_ids.amount / 100))
                    montoImpuestoUni = item.price_unit - base_imponible

                precioItem = item.price_unit

            else:
                base_imponible = item.price_unit
                descuento_uni = item.discount / 100.0
                descuento_item_unit = base_imponible * descuento_uni
                monto_item_unit = base_imponible - descuento_item_unit
                impuesto_ap = item.invoice_line_tax_ids.amount / 100
                monto_igv = monto_item_unit * impuesto_ap
                precioItem = monto_item_unit + monto_igv

            detalle.append({
                "cantidadItem": round(item.quantity, 3),
                "unidadMedidaItem": item.uom_id.code,
                "codItem": str(item.product_id.id),
                "nombreItem": item.product_id.name,
                "precioItem": round(precioItem, 2),
                "precioItemSinIgv": round(base_imponible, 2),
                "montoItem": round(monto_item_unit * item.quantity, 2),
                "descuentoMonto": item.quantity * descuento_item_unit,
                "codAfectacionIgv": (
                    item.invoice_line_tax_ids[0].afect_igv.code
                ),
                "tasaIgv": impuesto_ap,
                "montoIgv": round(monto_igv * item.quantity, 2),
                # "codSistemaCalculoIsc": "01",  # VERIFICAR
                # "montoIsc": 0.0,  # VERIFICAR
                # "tasaIsc" : 0.0, #VERIFICAR
                # "precioItemReferencia": 0.0,  # VERIFICAR
                "idOperacion": serie + '-' + correlativo + '-' + str(item.id),
            })

        anexo = [{}]
        anticipo = [{}]
        today_code = self.date_invoice.replace('-', '')
        data = {
            'documento': doc,
            'tipoDocumento': tipo_doc,
            'fechaEmision': today[:10],
            'idTransaccion': (tipo_doc + '-' + ruc_emisor + '-'
                              + today_code + correlativo),
            'correoReceptor': self.partner_id.email or '',
            'impuesto': impuesto,
            'detalle': detalle,
            'descuento': descuento,
            # 'anexo': anexo,
            # 'referencia': ref,
            # 'anticipo': anticipo,
            # 'servicioHospedaje':
        }
        # Boleta
        if tipo_doc in '03':
            data['documento'].update(
                {'direccionDestino': self.get_direc(receptor)}
            )
        # Nota de Crédito
        if tipo_doc == u'07':
            data['documento']['sustento'] = self.name
            data['documento']['tipoMotivoNotaModificatoria'] = (
                self.tipo_nota_doc_id.code
            )
            doc_ref = self.search([('number', '=', self.origin)])
            serie_ref, correlativo_ref = doc_ref.number.split('-')
            ref = [{
                'serieRef': serie_ref,
                'correlativoRef': correlativo_ref,
                'fechaEmisionRef': doc_ref.date_invoice,
                'tipoDocumentoRef': doc_ref.journal_id.tipo_doc_id.code
            }]
            data['referencia'] = ref
        if tipo_doc == u'08':
            data['documento']['sustento'] = self.sustento_ndeb
            data['documento']['tipoMotivoNotaModificatoria'] = (
                self.tipo_ndeb_id.code
            )
            if self.inv_ndeb_rel_id:
                doc_ref = self.inv_ndeb_rel_id
                serie_ref, correlativo_ref = doc_ref.number.split('-')
                ref = [{
                    'serieRef': serie_ref,
                    'correlativoRef': correlativo_ref,
                    'fechaEmisionRef': doc_ref.date_invoice,
                    'tipoDocumentoRef': doc_ref.journal_id.tipo_doc_id.code
                }]
                data['referencia'] = ref
        _logger.info(json.dumps(data, indent=4))
        # _logger.info(self.validate(tipo_doc, data))
        try:
            self.validate(tipo_doc, data)
        except voluptuous.error.MultipleInvalid as exc:
            _logger.info(exc)
            return self.env['mensaje.emergente'].get_mensaje(
                        'Validación de campos',
                        str(exc))
        self.env['logs.comprobante'].create(
            {
                'invoice_id': self.id,
                'fecha': fields.Datetime.now(),
                'descripcion': 'Envio a Factur@activa',
                'estado_ini': False,
                'estado_fin': 'xenviar',
                'json_envio': json.dumps(data, indent=4),
            }
        )
        rpta = send(
            self.company_id.url_endpoint,
            json.dumps(data),
            access_token,
            self.company_id.url_documentos
        )
        # _logger.info(rpta)
        if 'error' in rpta:
            data_rpta = rpta['data'].json()
            if 'errors' in data_rpta:
                errors = data_rpta.get('errors')[0]
                if 'meta' in errors:
                    meta = data_rpta.get('errors')[0].get('meta')
                    if ('reenvioHabilitado' in meta
                            and meta.get('reenvioHabilitado')):
                        self.env['logs.comprobante'].create(
                            {
                                'invoice_id': self.id,
                                'fecha': fields.Datetime.now(),
                                'descripcion': ('Code: ' + errors.get('code')
                                                + '-' + errors.get('detail')),
                                'estado_ini': 'xenviar',
                                'estado_fin': 'xenviar',
                                'json_rpta': data_rpta,
                            }
                        )
                    return self.env['mensaje.emergente'].get_mensaje(
                        'Factur@ctiva',
                        ('Status: ' + str(errors.get('status')) + ' '
                         + 'Code: ' + errors.get('code')),
                        errors.get('detail'))
                else:
                    return self.env['mensaje.emergente'].get_mensaje(
                        'Factur@ctiva',
                        ('Status: ' + str(errors.get('status')) + ' '
                         + 'Code: ' + errors.get('code')),
                        errors.get('detail'))
        else:
            _logger.info(json.dumps(rpta.json(), indent=4))
            data_rpta = rpta.json().get('data')
            self.env['logs.comprobante'].create(
                {
                    'invoice_id': self.id,
                    'fecha': fields.Datetime.now(),
                    'descripcion': 'Enviado a Factur@ctiva',
                    'estado_ini': 'xenviar',
                    'estado_fin': 'enviado',
                    'json_rpta': data_rpta,
                }
            )
            self.estado_envio = 'acep_factiva'
            self.env['logs.comprobante'].create(
                {
                    'invoice_id': self.id,
                    'fecha': fields.Datetime.now(),
                    'descripcion': 'Aceptado Factur@ctiva',
                    'estado_ini': 'enviado',
                    'estado_fin': 'acep_factiva',
                    'json_rpta': data_rpta,
                }
            )
            if 'estadoEmision' in data_rpta:
                estado_emision = data_rpta['estadoEmision']
                if estado_emision == u'A':
                    self.env['logs.comprobante'].create(
                        {
                            'invoice_id': self.id,
                            'fecha': fields.Datetime.now(),
                            'descripcion': 'Aceptado Sunat',
                            'estado_ini': 'acep_factiva',
                            'estado_fin': 'acep_sunat',
                            'json_rpta': data_rpta,
                        }
                    )
                    self.estado_envio = 'acep_sunat'
                    return self.env['mensaje.emergente'].get_mensaje(
                        'Factur@ctiva', 'Aceptado SUNAT', False)
                elif estado_emision == u'P':
                    self.env['logs.comprobante'].create(
                        {
                            'invoice_id': self.id,
                            'fecha': fields.Datetime.now(),
                            'descripcion': 'Pendiente de envio a SUNAT',
                            'estado_ini': 'acep_factiva',
                            'estado_fin': 'acep_factiva',
                            'json_rpta': data_rpta,
                        }
                    )
                    self.estado_envio = 'acep_factiva'
                    return self.env['mensaje.emergente'].get_mensaje(
                        'Factur@ctiva', 'Pendiente de envio a SUNAT', False)
                elif estado_emision == u'O':
                    self.env['logs.comprobante'].create(
                        {
                            'invoice_id': self.id,
                            'fecha': fields.Datetime.now(),
                            'descripcion': 'Aceptado Sunat Obs.',
                            'estado_ini': 'acep_factiva',
                            'estado_fin': 'acep_sunat_obs',
                            'json_rpta': data_rpta,
                        }
                    )
                    self.estado_envio = 'acep_sunat_obs'
                    # TODO: Mostar popup con informacion
                elif estado_emision == u'R':
                    self.env['logs.comprobante'].create(
                        {
                            'invoice_id': self.id,
                            'fecha': fields.Datetime.now(),
                            'descripcion': 'Aceptado Sunat Obs.',
                            'estado_ini': 'acep_factiva',
                            'estado_fin': 'rechaz_sunat',
                            'json_rpta': data_rpta,
                        }
                    )
                    self.estado_envio = 'rechaz_sunat'
                    # TODO: Mostar popup con informacion

    @api.multi
    def action_baja_comprobante(self):
        domain = [('invoice_id', '=', self.id),
                  ('resp_estado_emision', '=', 'acep_factiva')]
        baja = self.env['baja.documento'].search(domain,
                                                 order='id desc',
                                                 limit=1)
        if baja and baja.id:
            form_id = self.env.ref(
                'factiva_integracion.baja_documento_form_view').id
            return {
                'type': 'ir.actions.act_window',
                'name': "Baja Documento",
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'baja.documento',
                'view_id': form_id,
                'views': [(form_id, 'form')],
                'target': 'new',
                'context': {
                    'name': baja.name,
                    'invoice_id': baja.invoice_id.id,
                    'fecha': baja.fecha,
                    'motivo': baja.motivo,
                    'resp_id_resumen': baja.resp_id_resumen,
                    'resp_id_ticket': baja.resp_id_ticket,
                    'resp_estado_emision': baja.resp_estado_emision,
                }
            }
        else:
            today = fields.Date.from_string(fields.Date.context_today(self))
            date_invoice = fields.Date.from_string(self.date_invoice)
            if today > date_invoice + relativedelta(days=7):
                year, month, day = self.date_invoice.split('-')
                raise UserError('Solo tiene 7 días para solicitar la baja'
                                ' de un comprobante, la fecha de emisión de %s'
                                ' es %s/%s/%s'
                                % (self.number, day, month, year))
            form_id = self.env.ref(
                'factiva_integracion.send_baja_documento_form_view').id
            return {
                'type': 'ir.actions.act_window',
                'name': "Baja Documento",
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'baja.documento',
                'view_id': form_id,
                'views': [(form_id, 'form')],
                'target': 'new',
                'context': {
                    'invoice_id': self.id,
                }
            }

    @api.multi
    def action_estado_envio(self):
        access_token = token(self.company_id.url_endpoint,
                             self.company_id.api_key,
                             self.company_id.api_secret)
        id_consulta = self.fa_consulta_id
        rpta = get(self.company_id.url_endpoint,
                   {},
                   access_token,
                   self.company_id.url_documentos,
                   id_consulta)
        data_rpta = rpta.json()
        _logger.info(id_consulta)
        _logger.info(rpta)
        _logger.info(data_rpta)
        # TODO: Mensaje de error cuando no se tenga respuesta.

    @api.multi
    def action_print_documento_fa(self):
        self.ensure_one()
        access_token = token(self.company_id.url_endpoint,
                             self.company_id.api_key,
                             self.company_id.api_secret)
        id_consulta = self.fa_consulta_id
        rpta = get(self.company_id.url_endpoint,
                   {},
                   access_token,
                   self.company_id.url_download,
                   id_consulta)
        data_rpta = rpta.json().get('data')

        if 'pdf' in data_rpta:
            pdf = data_rpta.get('pdf')
            file_id = self.env['file.imp'].create({'filecontent': pdf})
            filename_field = self.fa_consulta_id[2:]

            if file_id and file_id.id is not False:
                action = {
                    'res_model': 'ir.actions.act_url',
                    'type': 'ir.actions.act_url',
                    'url': ("web/content/?model=file.imp&id=" + str(file_id.id)
                            + "&filename_field=" + filename_field
                            + "&field=filecontent&download=true&filename="
                            + filename_field+'.pdf'),
                    'target': 'new',
                }
                return action
        else:
            # TODO: Mensaje de error
            pass

    # ================ REFUND ===========================================
    @api.multi
    @api.returns('self')
    def refund(self, date_invoice=None, date=None, description=None,
               journal_id=None, tipo_nota=None):
        new_invoices = self.browse()
        for invoice in self:
            # create the new invoice
            values = self._prepare_refund(invoice, date_invoice=date_invoice,
                                          date=date, description=description,
                                          journal_id=journal_id)
            if tipo_nota:
                values['tipo_nota_doc_id'] = tipo_nota
            refund_invoice = self.create(values)
            invoice_type = {'out_invoice': ('customer invoices credit note'),
                            'in_invoice': ('vendor bill credit note')}
            message = (_("This %s has been created from: <a href=# "
                         "data-oe-model=account.invoice data-oe-id=%d>%s</a>")
                       % (invoice_type[invoice.type],
                          invoice.id, invoice.number)
                       )
            refund_invoice.message_post(body=message)
            new_invoices += refund_invoice
        return new_invoices
    # ================ FIN REFUND =======================================
