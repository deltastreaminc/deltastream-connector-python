from typing import AsyncIterator, List, Optional, Any, Tuple, Callable, Awaitable

from deltastream.api.dataplane.openapi_client import ResultSet
from .models import Rows
from .error import InterfaceError
from .rows import castRowData, Column

class ResultsetRows(Rows):
    def __init__(
        self,
        get_statement_status: Callable[[str, int], Awaitable[ResultSet]],
        result_set: ResultSet
    ):
        self.current_row_idx: int = -1
        self.current_partition_idx: int = 0
        self.current_result_set: ResultSet = result_set
        self.get_statement_status = get_statement_status
        self.is_open: bool = True
        self.cached_columns: Optional[List[Column]] = None

    async def close(self) -> None:
        self.is_open = False

    def __aiter__(self) -> AsyncIterator[Optional[List[Any]]]:
        return self

    async def __anext__(self) -> Optional[List[Any]]:
        if not self.is_open:
            raise StopAsyncIteration

        row_idx, part_idx = self._calc_partition_idx(self.current_row_idx + 1)
        if part_idx == -1:
            raise StopAsyncIteration

        if part_idx != self.current_partition_idx:
            self.current_result_set = await self.get_statement_status(
                self.current_result_set.statement_id,
                part_idx
            )
            self.current_partition_idx = part_idx

        self.current_row_idx += 1
        if self.current_result_set.data is None:
            return None
        row = castRowData(
            self.current_result_set.data[row_idx],
            self.columns()
        )
        return row

    def columns(self) -> List[Column]:
        """
        Returns the names and types of the columns returned by the query.
        """
        if not self.is_open:
            return []

        if self.cached_columns is not None:
            return self.cached_columns

        if self.current_result_set.metadata.columns is None:
            raise InterfaceError('invalid result set metadata')

        columns: List[Column] = []
        for column in self.current_result_set.metadata.columns:
            columns.append(Column(
                name=column.name,
                type=column.type,
                nullable=column.nullable
            ))

        self.cached_columns = columns
        return columns

    def _calc_partition_idx(self, row_idx: int) -> Tuple[int, int]:
        """
        Calculate the partition index for a given row index.
        Returns a tuple of (row_index, partition_index).
        """
        if self.current_result_set.metadata.partition_info is None:
            raise InterfaceError('invalid result set metadata')

        for i, partition in enumerate(self.current_result_set.metadata.partition_info):
            if row_idx < partition.row_count:
                return row_idx, i
            row_idx = row_idx - partition.row_count

        return -1, -1