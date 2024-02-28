# SPDX-FileCopyrightText: 2023-present DeltaStream Inc. <support@deltastream.io>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Tuple, Sequence, Any, Optional, List
from pydantic import StrictStr

from openapi_client.models.result_set_context import ResultSetContext
from openapi_client.models.result_set import ResultSet
from openapi_client.models.result_set_partition_info import ResultSetPartitionInfo
from openapi_client.models.result_set_data_inner_inner import ResultSetDataInnerInner

from .options import Options
from .exceptions import InterfaceError
from .datatypes import map_dsql_type_to_object, cast_string_to_python_type
from .api import get_resultset_with_op, get_resultset_with_statement_id, Parameters

DBAPITypeCode = Any | None
DBAPIColumnDescription = Tuple[str, DBAPITypeCode, int | None, int | None, int | None, int | None, bool | None]


class Cursor(object):
    """
    This object represent a database cursor, which is used to manage the context of a fetch operation

    Attributes:
        *arraysize*       Specifies the number of rows to fetch at a time with .fetchmany()
    """

    arraysize: int = 1
    _endpoint: StrictStr
    _token: StrictStr
    _options: Options
    _context: ResultSetContext
    _open: bool = True

    _result_set: Optional[ResultSet] = None
    _columns: Sequence[DBAPIColumnDescription]
    _partitions: List[ResultSetPartitionInfo]
    _current_partition: int
    _row_index: int

    def __init__(self, endpoint: StrictStr, token: StrictStr, options: Options, **kwargs):
        super().__init__(**kwargs)
        self._endpoint = endpoint
        self._token = token
        self._options = options
        self._context = ResultSetContext()

    @property
    def description(self) -> Sequence[DBAPIColumnDescription] | None:
        self._check_closed()
        if self._result_set is None:
            raise InterfaceError('no result set')
        return self._columns

    @property
    def rowcount(self) -> int:
        self._check_closed()
        if self._result_set is None:
            raise InterfaceError('no result set')
        cnt = 0
        for pinfo in self._partitions:
            cnt += pinfo.row_count
        return cnt

    def close(self):
        self._check_closed()
        self._open = False
        self._result_set = None
        self._columns = None
        self._partitions = None
        self._current_partition = -1
        self._row_index = -1

    def execute(self, operation: str, parameters: Parameters):
        """Prepare and execute a database operation (query or command)."""
        self._result_set = get_resultset_with_op(operation, parameters, self._context, self._endpoint, self._token, self._options)
        self._context = self._result_set.metadata.context
        self._row_index = 0
        self._current_partition = 0
        self._partitions = self._result_set.metadata.partition_info

        cols = []
        for c in self._result_set.metadata.columns:
            cols.append((c.name, map_dsql_type_to_object(c.type), None, None, None, c.nullable))
        self._columns = cols

    def executemany(self, operation: str, multi_parameters: Sequence[Parameters]):
        """Prepare a database operation (query or command) and then execute it against
        all parameter sequences or mappings found in the sequence seq_of_parameters.

        This operation will not return any result sets.
        """
        pass

    def fetchone(self) -> Sequence[Any] | None:
        """Fetch the next row of a query result set, returning a single sequence, or None when no more data is available.
        An Error exception is raised if the previous call to .execute() did not produce any result set or no call was issued yet."""
        if self._result_set is None:
            raise InterfaceError('no result set')
        part_idx, row_idx = self._calc_partition_idx(self._row_index)
        if part_idx == -1:
            return None
        if part_idx != self._current_partition:
            if part_idx >= len(self._result_set.metadata.partition_info):
                return None
            self._result_set = get_resultset_with_statement_id(self._result_set.statement_id, part_idx, self._endpoint, self._token, self._options)
        self._row_index += 1
        return self._cast_row_data(self._result_set.data[row_idx])

    def fetchmany(self, size: int = 1) -> Sequence[Sequence[Any]]:
        """Fetch the next set of rows of a query result, returning a sequence of sequences (e.g. a list of tuples).
        An empty sequence is returned when no more rows are available."""
        result = []
        for i in range(size):
            row = self.fetchone()
            if row is None:
                break
            result.append(row)
        return result

    def fetchall(self) -> Sequence[Sequence[Any]]:
        """Fetch all (remaining) rows of a query result, returning them as a sequence of sequences.
        An Error exception is raised if the previous call to .execute() did not produce any result set or no call was issued yet."""
        result = []
        while True:
            row = self.fetchone()
            if row is None:
                break
            result.append(row)
        return result

    def _check_closed(self):
        if not self._open:
            raise InterfaceError('cursor is closed')
        return

    def _calc_partition_idx(self, row_idx: int):
        for pidx in range(len(self._partitions)):
            if row_idx < self._partitions[pidx].row_count:
                return (pidx, row_idx)
            row_idx -= self._partitions[pidx].row_count
        return (-1, -1)

    def _cast_row_data(self, data: ResultSetDataInnerInner) -> List[Any]:
        row = []
        for idx in range(len(data)):
            row.append(cast_string_to_python_type(self._result_set.metadata.columns[idx].type, data[idx].actual_instance))
        return row
