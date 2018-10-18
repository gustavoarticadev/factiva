# -*- coding: utf-8 -*-
{
    'name': 'Factur@ctiva Catálogos SUNAT',
    'version': '1.0',
    'summary': 'Catátolos SUNAT para la localización Peruana',
    'sequence': 10,
    'author': 'Salcedo Salazar Juan Diego - salcedo.salazar@gmail.com',
    'description': """
Factur@ctiva Topónimos
========================
Módulo que registra los catátalogos SUNAT para la Facturación Electrónica de
la localización Peruana
    """,
    'website': 'https://facturactiva.com/',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/factiva_catalogo_data.xml',
        'views/factiva_catalogo_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
