from dataclasses import dataclass
from typing import Optional, Protocol, List, Any, AsyncIterator
from .rows import Column


class Rows(Protocol):
    def columns(self) -> List[Column]: ...
    async def close(self) -> None: ...
    def __aiter__(self) -> AsyncIterator[Optional[List[Any]]]: ...


@dataclass
class DataplaneRequest:
    uri: str
    statement_id: str
    token: str
    request_type: str


@dataclass
class ResultSetContext:
    organization_id: Optional[str] = None
    role_name: Optional[str] = None
    database_name: Optional[str] = None
    schema_name: Optional[str] = None
    store_name: Optional[str] = None


@dataclass
class ResultSetMetadata:
    context: Optional[ResultSetContext] = None
    dataplane_request: Optional[DataplaneRequest] = None


@dataclass
class ResultSet:
    statement_id: str
    sql_state: str
    message: Optional[str]
    metadata: ResultSetMetadata
