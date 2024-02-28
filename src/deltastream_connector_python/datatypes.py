# SPDX-FileCopyrightText: 2023-present DeltaStream Inc. <support@deltastream.io>
#
# SPDX-License-Identifier: Apache-2.0

import time
import datetime
import decimal
from typing import Any, Dict, Sequence, Union  # pylint: disable=unused-import
from dateutil import parser as date_parser

from .exceptions import DataError


class DBAPITypeObject:
    def __init__(self, *values):
        self.values = values

    def __cmp__(self, other):
        if other in self.values:
            return 0
        if other < self.values:
            return 1
        else:
            return -1


Date = datetime.date
Time = datetime.time
Timestamp = datetime.datetime


def DateFromTicks(ticks):
    return Date(*time.localtime(ticks)[:3])


def TimeFromTicks(ticks):
    return Time(*time.localtime(ticks)[3:6])


def TimestampFromTicks(ticks):
    return Timestamp(*time.localtime(ticks)[:6])


Binary = bytes

STRING = DBAPITypeObject(str)
BINARY = DBAPITypeObject(str)
NUMBER = DBAPITypeObject(int, decimal.Decimal)
DATETIME = DBAPITypeObject(Timestamp, Date, Time)
ROWID = DBAPITypeObject()

TYPEMAP = {
    '<null>': None,
    'VARCHAR': STRING,
    'TINYINT': NUMBER,
    'SMALLINT': NUMBER,
    'INTEGER': NUMBER,
    'BIGINT': NUMBER,
    'FLOAT': NUMBER,
    'DOUBLE': NUMBER,
    'DECIMAL': NUMBER,
    'TIMESTAMP': DATETIME,
    'TIMESTAMP_TZ': DATETIME,
    'DATE': DATETIME,
    'TIME': DATETIME,
    'TIMESTAMP_LTZ': DATETIME,
    'VARBINARY': BINARY,
    'BYTES': BINARY,
    'ARRAY': STRING,
    'MAP': STRING,
    'STRUCT': STRING,
}


def map_dsql_type_to_object(dsql_type):
    dsql_type = dsql_type.strip()
    for t in TYPEMAP:
        if t.find(dsql_type) == 0:
            return TYPEMAP[t]
    raise DataError('unknown column type "%s"' % (dsql_type))


QueryParameters = Union[Sequence[Any], Dict[Union[str, int], Any]]


def cast_null(inp):
    return None


def cast_str(inp):
    if inp is None:
        return None
    return inp


def cast_int(inp):
    if inp is None:
        return None
    return int(inp)


def cast_float(inp):
    if inp is None:
        return None
    return float(inp)


def cast_datetime(inp):
    if inp is None:
        return None
    return date_parser.parse(inp)


CAST_MAP = {
    '<null>': cast_null,
    'VARCHAR': cast_str,
    'TINYINT': cast_int,
    'SMALLINT': cast_int,
    'INTEGER': cast_int,
    'BIGINT': cast_int,
    'FLOAT': cast_float,
    'DOUBLE': cast_float,
    'DECIMAL': cast_float,
    'TIMESTAMP': cast_datetime,
    'TIMESTAMP_TZ': cast_datetime,
    'DATE': cast_datetime,
    'TIME': cast_datetime,
    'TIMESTAMP_LTZ': cast_datetime,
    'VARBINARY': cast_str,
    'BYTES': cast_str,
    'ARRAY': cast_str,
    'MAP': cast_str,
    'STRUCT': cast_str,
}


def cast_string_to_python_type(dsql_type, inp):
    return CAST_MAP[dsql_type](inp)
