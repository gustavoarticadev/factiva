# -*- coding: utf-8 -*-
{
    'name': 'Factur@ctiva Consulta Doc.',
    'version': '1.0',
    'summary': 'Consulta de Documentos de identidad',
    'sequence': 10,
    'author': 'Salcedo Salazar Juan Diego - salcedo.salazar@gmail.com',
    'description': """
Factur@ctiva Consulta Doc.
============================
Módulo que Consulta de Documentos de identidad(RUC,...).
    """,
    'website': 'https://facturactiva.com/',
    'depends': [
        'factiva_catalogos',
    ],
    'data': [
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
