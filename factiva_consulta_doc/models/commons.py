# -*- coding: utf-8 -*-

import requests
import logging

_logger = logging.getLogger(__name__)


def consulta_tipo_doc_ws(url, num):
    url = '%s/%s' % (url, num)
    res = {'error': True, 'mensaje': None, 'data': {}}
    try:
        response = requests.get(url)
        response.raise_for_status()

        if response.status_code == requests.codes.ok:
            res['error'] = False
            res['data'] = response.json()
            _logger.info('Consulta documento WS: %s', res['data'])
    except requests.exceptions.HTTPError as exc:
        _logger.warning("Http Error: %s" % exc)
        res['mensaje'] = 'Http Error'
    except requests.exceptions.ConnectionError as exc:
        _logger.warning("Connection error: %s" % exc)
        res['mensaje'] = 'Error de conexión'
    except requests.exceptions.Timeout as exc:
        _logger.warning("Timeout Error: %s" % exc)
        res['mensaje'] = 'Timeout Error'
    except requests.exceptions.RequestException as exc:
        _logger.warning("OOps: Something Else: %s" % exc)
        res['mensaje'] = 'OOps: Something Else'
    return res


def build_street_ws(data):
    street_format = ("%(tipoVia)s%(nombreVia)s%"
                     "(numero)s%(km)s%(dpto)s%(interior)s%(manzana)s%(lote)s")
    args = {
        'tipoVia': data['tipoVia'] if data['tipoVia'] != u'-' else '',
        'nombreVia': (
            ' ' + data['nombreVia'] if data['nombreVia'] != u'-' else ''
        ),
        'numero': (
            (' NRO. ' + data['numero']) if data['numero'] != u'-' else ''
        ),
        'km': (' KM. ' + data['km']) if data['km'] != u'-' else '',
        'dpto': (' DPTO. ' + data['dpto']) if data['dpto'] != u'-' else '',
        'interior': (
            (' INT. ' + data['interior']) if data['interior'] != u'-' else ''
        ),
        'manzana': (
            (' MZ. ' + data['manzana']) if data['manzana'] != u'-' else ''
        ),
        'lote': (' LOTE. ' + data['lote']) if data['lote'] != u'-' else '',
    }
    return street_format % args


def build_street2_ws(data):
    street2_format = "%(codZona)s%(tipoZona)s"
    args = {
        'codZona': data['codZona'] if data['tipoVia'] != u'-' else '',
        'tipoZona': (
            ' ' + data['tipoZona'] if data['tipoZona'] != u'-' else ''
        ),
    }
    return street2_format % args
