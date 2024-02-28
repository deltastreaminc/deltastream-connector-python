# SPDX-FileCopyrightText: 2023-present DeltaStream Inc. <support@deltastream.io>
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from deltastream_connector_python import connect, Connection

def test_token_is_required():
    with pytest.raises(Connection.InterfaceError, match='no API token provided'):
        connect()

    conn = connect(token='blah')
    assert conn._token == 'blah'
    conn.close()


def test_endpoint_is_defaulted():
    conn = connect(token='blah')
    assert conn._endpoint == 'https://api.deltastream.io/v2'
    conn.close()


def test_endpoint_is_settable():
    conn = connect(token='blah', endpoint='http://some.where')
    assert conn._endpoint == 'http://some.where'
    conn.close()


def test_commit_rollback_raise_exception():
    conn = connect(token='blah', endpoint='http://some.where')
    with pytest.raises(Connection.NotSupportedError):
        conn.commit()
    with pytest.raises(Connection.NotSupportedError):
        conn.rollback()
    conn.close()


def test_close_connection():
    conn = connect(token='blah', endpoint='http://some.where')
    conn.close()
    with pytest.raises(Connection.InterfaceError):
        conn.close()
