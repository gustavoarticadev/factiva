# -*- coding: utf-8 -*-
{
    'name': 'Factur@ctiva Integración',
    'version': '3.0',
    'summary': 'Integración con el core de facturación de Factur@activa',
    'sequence': 10,
    'author': 'Salcedo Salazar Juan Diego - salcedo.salazar@gmail.com',
    'description': """
Factur@ctiva Integración
==========================
Módulo que integra la emisión de comprobantes electrónicos del ERP con el core
de facturación de Factur@ctiva.
    """,
    'website': 'https://facturactiva.com/',
    'depends': [
        'account',
        'factiva_popup',
    ],
    'external_dependencies': {'python': ['voluptuous']},
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/baja_documento_view.xml',
        'views/logs_comprobante_view.xml',
        'data/product_uom_data.xml',
        'views/res_company_view.xml',
        'views/account_view.xml',
        'views/account_invoice_refund_view.xml',
        'views/account_invoice_view.xml',
        'views/product_uom_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
