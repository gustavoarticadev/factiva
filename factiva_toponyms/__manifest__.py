# -*- coding: utf-8 -*-
{
    'name': 'Factur@ctiva Topónimos',
    'version': '1.0',
    'summary': 'Topónimos para la localización Peruana',
    'sequence': 10,
    'author': 'Salcedo Salazar Juan Diego - salcedo.salazar@gmail.com',
    'description': """
Factur@ctiva Topónimos
========================
Módulo que registra los topónimos para la localización Peruana
    """,
    'website': 'https://facturactiva.com/',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/factiva_departamento_data.xml',
        'data/factiva_provincia_data.xml',
        'data/factiva_distrito_data.xml',
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
