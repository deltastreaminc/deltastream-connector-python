# SPDX-FileCopyrightText: 2023-present DeltaStream Inc. <support@deltastream.io>
#
# SPDX-License-Identifier: Apache-2.0

import pytest
import httpretty

from deltastream_connector_python import connect, Connection, Options, STRING, DATETIME
from requests_toolbelt.multipart import decoder
from dateutil.parser import parse as parse_tz

from openapi_client.models.statement_request import StatementRequest


def test_cursor_raises_exception_if_not_executed():
    httpretty.enable(verbose=True, allow_net_connect=False)
    conn = connect(endpoint='http://localhost:8080/v2', token='token', options=Options(debug=True))
    cur = conn.cursor()

    with pytest.raises(Connection.InterfaceError):
        _ = cur.rowcount

    with pytest.raises(Connection.InterfaceError):
        _ = cur.description

    with pytest.raises(Connection.InterfaceError):
        cur.fetchone()


def test_empty_result_set():
    httpretty.enable(verbose=True, allow_net_connect=False)
    conn = connect(endpoint='http://localhost:8080/v2', token='token', options=Options(debug=True))
    cur = conn.cursor()

    def list_organizations(request, uri, response_headers):
        mp = decoder.MultipartDecoder(request.body, request.headers.get('Content-Type'))
        part0 = mp.parts[0]
        assert part0.headers.get(b'content-type') == b'application/json'
        s = StatementRequest.from_json(part0.text)
        assert s.statement == 'LIST ORGANIZATIONS;'
        return [200, response_headers, open('tests/fixtures/list-organizations-200-00000-0.json', 'r').read()]

    httpretty.register_uri(httpretty.POST, 'http://localhost:8080/v2/statements', body=list_organizations)
    cur.execute('LIST ORGANIZATIONS;', [])
    assert cur.rowcount == 0
    assert cur.description == [
        ('id', STRING, None, None, None, False),
        ('name', STRING, None, None, None, False),
        ('description', STRING, None, None, None, True),
        ('profileImageURI', STRING, None, None, None, True),
        ('createdAt', DATETIME, None, None, None, False),
    ]
    assert cur.fetchone() is None


def test_result_set_1_result():
    httpretty.enable(verbose=True, allow_net_connect=False)
    conn = connect(endpoint='http://localhost:8080/v2', token='token', options=Options(debug=True))
    cur = conn.cursor()

    def list_organizations(request, uri, response_headers):
        mp = decoder.MultipartDecoder(request.body, request.headers.get('Content-Type'))
        part0 = mp.parts[0]
        assert part0.headers.get(b'content-type') == b'application/json'
        s = StatementRequest.from_json(part0.text)
        assert s.statement == 'LIST ORGANIZATIONS;'
        return [200, response_headers, open('tests/fixtures/list-organizations-200-00000-1.json', 'r').read()]

    httpretty.register_uri(httpretty.POST, 'http://localhost:8080/v2/statements', body=list_organizations)
    cur.execute('LIST ORGANIZATIONS;', [])
    assert cur.rowcount == 1
    assert cur.description == [
        ('id', STRING, None, None, None, False),
        ('name', STRING, None, None, None, False),
        ('description', STRING, None, None, None, True),
        ('profileImageURI', STRING, None, None, None, True),
        ('createdAt', DATETIME, None, None, None, False),
    ]
    assert cur.fetchone() == ['0e0e3617-3cd6-4407-a189-97daf226c4d4', 'o1', None, None, parse_tz('2023-12-30 03:37:45Z')]
    assert cur.fetchone() is None


def test_delayed_result_set():
    httpretty.enable(verbose=True, allow_net_connect=False)
    conn = connect(endpoint='http://localhost:8080/v2', token='token', options=Options(debug=True))
    cur = conn.cursor()

    def list_organizations_202(request, uri, response_headers):
        mp = decoder.MultipartDecoder(request.body, request.headers.get('Content-Type'))
        part0 = mp.parts[0]
        assert part0.headers.get(b'content-type') == b'application/json'
        s = StatementRequest.from_json(part0.text)
        assert s.statement == 'LIST ORGANIZATIONS;'
        return [202, response_headers, open('tests/fixtures/list-organizations-202-03000.json', 'r').read()]

    count = 0

    def list_organizations_200(request, uri, response_headers):
        nonlocal count
        if count < 2:
            count += 1
            return [202, response_headers, open('tests/fixtures/list-organizations-202-03000.json', 'r').read()]
        return [200, response_headers, open('tests/fixtures/list-organizations-200-00000-0.json', 'r').read()]

    httpretty.register_uri(httpretty.POST, 'http://localhost:8080/v2/statements', body=list_organizations_202)
    httpretty.register_uri(httpretty.GET, 'http://localhost:8080/v2/statements/d789687d-4e1b-4649-846e-4f10b722f3ad?partitionID=0', body=list_organizations_200)

    cur.execute('LIST ORGANIZATIONS;', [])
    assert cur.rowcount == 0
    assert cur.description == [
        ('id', STRING, None, None, None, False),
        ('name', STRING, None, None, None, False),
        ('description', STRING, None, None, None, True),
        ('profileImageURI', STRING, None, None, None, True),
        ('createdAt', DATETIME, None, None, None, False),
    ]
    assert cur.fetchone() is None

def test_multi_partition_resultset():
    pass

def test_context_across_executions():
    pass


def test_unsuccesful_sql_code():
    pass


def test_bad_request():
    pass


def test_unauthorized():
    pass


def test_forbidden():
    pass


def test_api_not_found():
    pass


def test_service_exception():
    pass


def test_api_exception():
    pass
