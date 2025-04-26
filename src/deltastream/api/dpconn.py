from typing import Optional
from urllib.parse import urlparse, parse_qs
import asyncio

from .handlers import map_error_response
from deltastream.api.dataplane.openapi_client import (
    Configuration,
    DataplaneApi,
    ResultSet,
    StatementStatus,
    ErrorResponse as ResponseError,
)
from .error import AuthenticationError, SQLError, SqlState


class DPAPIConnection:
    def __init__(
        self, dsn: str, token: str, timezone: str, session_id: Optional[str] = None
    ):
        if token is None:
            raise AuthenticationError("Invalid DSN: missing token")

        self.token = token
        self.timezone = timezone
        self.session_id = session_id

        url = urlparse(dsn)
        self.server_url = f"{url.scheme}://{url.hostname}{url.path}"

        query_params = parse_qs(url.query)
        self.session_id = query_params.get("sessionID", [None])[0]

        config = Configuration()
        config.host = self.server_url
        config.access_token = self.token

        self.api = DataplaneApi(config)

    async def get_statement_status(
        self, statement_id: str, partition_id: int
    ) -> ResultSet:
        try:
            resp = await self.api.get_statement_status_raw(
                statement_id=statement_id, partition_id=partition_id
            )

            if resp.raw.status == 200:
                result_set = await resp.value()
                if result_set.sql_state == SqlState.SQL_STATE_SUCCESSFUL_COMPLETION:
                    return result_set
                raise SQLError(
                    result_set.message or "",
                    result_set.sql_state,
                    result_set.statement_id,
                )
            elif resp.raw.status == 202:
                statement_status = StatementStatus.from_json(resp.raw.body)
                await asyncio.sleep(1)  # Don't use return value
                return await self.get_statement_status(
                    statement_status.statement_id, partition_id
                )
            else:
                # Handle default case
                result_set = await resp.value()
                if result_set.sql_state == SqlState.SQL_STATE_SUCCESSFUL_COMPLETION:
                    return result_set
                raise SQLError(
                    result_set.message or "",
                    result_set.sql_state,
                    result_set.statement_id,
                )

        except ResponseError as err:
            map_error_response(err)
            raise
        except Exception:
            raise

    async def wait_for_completion(self, statement_id: str) -> ResultSet:
        result_set = await self.get_statement_status(statement_id, 0)
        if result_set.sql_state == SqlState.SQL_STATE_SUCCESSFUL_COMPLETION:
            return result_set
        await asyncio.sleep(1)  # Don't use return value
        return await self.wait_for_completion(statement_id)
