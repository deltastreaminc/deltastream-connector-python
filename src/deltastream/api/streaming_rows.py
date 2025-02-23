from typing import List, Optional, Any, Dict, AsyncIterator
from dataclasses import dataclass
import asyncio
import json
from websockets.legacy.client import WebSocketClientProtocol, connect as ws_connect

from .models import DataplaneRequest, Rows
from .dpconn import DPAPIConnection
from .error import InterfaceError, SQLError
from .rows import castRowData, Column

@dataclass
class PrintTopicMetadata:
    type: str
    headers: Dict[str, str]
    columns: List[Column]

@dataclass
class DataMessage:
    type: str
    headers: Dict[str, str]
    data: List[str]

@dataclass
class ErrorMessage:
    type: str
    headers: Dict[str, str]
    message: str
    sql_code: str

class Deferred:
    """A simple implementation of a deferred/promise pattern."""
    def __init__(self) -> None:
        self.future: asyncio.Future[Any] = asyncio.Future()

    def resolve(self, value=None):
        if not self.future.done():
            self.future.set_result(value)

    def reject(self, error=None):
        if not self.future.done():
            self.future.set_exception(error if error else Exception())

    @property
    def promise(self):
        return self.future

class StreamingRows(Rows):
    def __init__(self, conn: DPAPIConnection, req: DataplaneRequest):
        self.conn = conn
        self.req = req
        self.ws: Optional[WebSocketClientProtocol] = None
        self.metadata: Optional[PrintTopicMetadata] = None
        self.rows: List[List[Any]] = []
        self.deferred_row: Optional[Deferred] = None
        self.error: Optional[Any] = None

    async def open(self) -> None:
        """Internal function used by the connection to authenticate and open the websocket."""
        self.rows = []
        deferred_ready = Deferred()

        async def handle_messages():
            try:
                ws = await ws_connect(self.req.uri)
                self.ws = ws
                
                # Send authentication
                await ws.send(json.dumps({
                    "type": "auth",
                    "accessToken": self.conn.token,
                    "sessionId": self.conn.session_id,
                }))

                async for message in ws:
                    data = json.loads(message)
                    
                    if data["type"] == "metadata":
                        self.metadata = PrintTopicMetadata(**data)
                        deferred_ready.resolve()
                        
                    elif data["type"] == "data":
                        row = castRowData(
                            data["data"],
                            self.columns()
                        )
                        if self.deferred_row is not None:
                            self.deferred_row.resolve(row)
                            self.deferred_row = None
                        else:
                            self.rows.append(row)
                            
                    elif data["type"] == "error":
                        err = ErrorMessage(**data)
                        self.error = err
                        if self.deferred_row is not None:
                            self.deferred_row.reject()
                            self.deferred_row = None
                        if not deferred_ready.future.done():
                            deferred_ready.reject(err)
                        await ws.close()
                        break

            except Exception as e:
                if not deferred_ready.future.done():
                    deferred_ready.reject(e)
                raise

        # Start handling messages in the background
        asyncio.create_task(handle_messages())
        
        # Wait for the connection to be ready
        await deferred_ready.promise

    def columns(self) -> List[Column]:
        """Returns the column definitions."""
        if self.metadata is None:
            return []
            
        return [
            Column(
                name=column.name,
                type=column.type,
                nullable=column.nullable,
                length=column.length,
                precision=column.precision,
                scale=column.scale
            )
            for column in self.metadata.columns
        ]

    async def close(self) -> None:
        """Closes the WebSocket connection."""
        if self.ws is not None:
            await self.ws.close()
            self.ws = None

    def __aiter__(self) -> AsyncIterator[Optional[List[Any]]]:
        return self

    async def __anext__(self) -> Optional[List[Any]]:
        if self.error is not None:
            raise SQLError(
                self.error.message,
                self.error.sql_code,
                self.req.statement_id
            )

        if self.ws is None or not self.ws.open:
            raise StopAsyncIteration

        if self.rows:
            row = self.rows.pop(0)
            if row is not None:
                return row
            raise InterfaceError('client error: undefined row')

        self.deferred_row = Deferred()
        row = await self.deferred_row.promise
        
        if row is None:
            raise StopAsyncIteration
            
        return row