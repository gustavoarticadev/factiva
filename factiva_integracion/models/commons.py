# -*- coding: utf-8 -*-

import requests
import json
import logging


_logger = logging.getLogger(__name__)

# Tiempo de espera máximo al servidor de Factur@ctiva en segundos
TIMEOUT = 30


ESTADOS_INTEGRACION = [
    ('xenviar', 'Por Enviar'),
    ('enviado', 'Enviado'),
    ('acep_factiva', 'Aceptado Factur@ctiva'),
    ('rechaz_factiva', 'Rechazado Factur@ctiva'),
    ('acep_sunat', 'Aceptado SUNAT'),
    ('acep_sunat_obs', 'Aceptado SUNAT OBS.'),
    ('rechaz_sunat', 'Rechazado SUNAT'),
    ('proc_baja', 'Proceso de Baja'),
    ('baja_acep_sunat', 'Baja Aceptada SUNAT'),
    ('baja_rechaz_sunat', 'Baja Rechazada SUNAT'),
]


def token(url, key, secret):
    url = '%s/oauth2/token' % url
    res = {'error': True, 'mensaje': None, 'data': {}}

    headers = {"Content-Type": "application/json"}
    data = {
        "grant_type": "client_credentials",
        "client_id": key,
        "client_secret": secret
    }
    try:
        resp = requests.post(
            url,
            headers=headers,
            data=json.dumps(data),
            timeout=TIMEOUT
        )
        resp.raise_for_status()
        if resp.status_code == requests.codes.ok:
            return resp
            # _logger.info('Token WS: %s', resp.json().get('access_token'))
    except requests.exceptions.HTTPError as exc:
        _logger.warning('Http Error: %s' % exc)
        res['mensaje'] = 'Http Error:' % exc
    except requests.exceptions.ConnectionError as exc:
        _logger.warning('Connection error: %s' % exc)
        res['mensaje'] = 'Error de connexion: %s' % exc
    except requests.exceptions.Timeout as exc:
        _logger.warning('Timeout Error: %s' % exc)
        res['mensaje'] = 'Timeout Error: %s' % exc
    except requests.exceptions.RequestException as exc:
        _logger.warning('OOps: Something Else: %s' % exc)
        res['mensaje'] = 'OOps: Something Else: %s' % exc
    return res


def peticion(method='POST', url='', data=None, response=None,
             url_final=None, id_consulta=None):
    url = '%s/%s' % (url, url_final)
    if method == 'GET':
        url = '%s/%s' % (url, id_consulta)
    res = {'error': True, 'mensaje': None, 'data': {}}
    content = response.json()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': content['token_type'] + ' ' + content['access_token']
    }
    try:
        resp = requests.request(
            method,
            url,
            headers=headers,
            data=data,
            timeout=TIMEOUT
        )
        resp.raise_for_status()
        if resp.status_code == requests.codes.ok:
            return resp
    except requests.exceptions.HTTPError as exc:
        _logger.warning('Http Error: %s' % exc)
        res['mensaje'] = 'Http Error: %s' % exc
        res['data'] = resp
    except requests.exceptions.ConnectionError as exc:
        _logger.warning('Connection error: %s' % exc)
        res['mensaje'] = 'Error de connexion: %s' % exc
        res['data'] = resp
    except requests.exceptions.Timeout as exc:
        _logger.warning('Timeout Error: %s' % exc)
        res['mensaje'] = 'Timeout Error: %s' % exc
        res['data'] = resp
    except requests.exceptions.RequestException as exc:
        _logger.warning('OOps: Something Else: %s' % exc)
        res['mensaje'] = 'OOps: Something Else: %s' % exc
        res['data'] = resp
    return res


def send(url, data, response, url_final):
    return peticion('POST', url, data, response, url_final)


def get(url, data, response, url_final, id_consulta):
    return peticion('GET', url, data, response, url_final, id_consulta)
