from typing import Optional
from urllib.parse import urlparse, parse_qs
import asyncio

from deltastream.api.dataplane.openapi_client import (
    Configuration,
    DataplaneApi,
    ResultSet,
    StatementStatus,
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

    def _get_statement_status_api(self, statement_id: str, partition_id: int):
        resp = self.api.get_statement_status(
            statement_id=statement_id, partition_id=partition_id
        )
        return resp

    async def get_statement_status(
        self, statement_id: str, partition_id: int
    ) -> ResultSet:
        try:
            resp = self._get_statement_status_api(statement_id, partition_id)
            if resp.status == 200:
                result_set = resp.body
                if result_set.sql_state == SqlState.SQL_STATE_SUCCESSFUL_COMPLETION:
                    return result_set
                raise SQLError(
                    result_set.message or "",
                    result_set.sql_state,
                    result_set.statement_id,
                )
            elif resp.status == 202:
                statement_status = StatementStatus.from_json(resp.raw.body)
                await asyncio.sleep(1)
                if statement_status is not None and hasattr(
                    statement_status, "statement_id"
                ):
                    # Recurse, but always call the API again
                    return await self.get_statement_status(
                        statement_status.statement_id, partition_id
                    )
                else:
                    raise SQLError("Invalid statement status", "", "")
            else:
                result_set = resp.body
                if result_set.sql_state == SqlState.SQL_STATE_SUCCESSFUL_COMPLETION:
                    return result_set
                raise SQLError(
                    result_set.message or "",
                    result_set.sql_state,
                    result_set.statement_id,
                )

        except Exception as exc:
            raise RuntimeError(str(exc))

    async def wait_for_completion(self, statement_id: str) -> ResultSet:
        result_set = await self.get_statement_status(statement_id, 0)
        if result_set.sql_state == SqlState.SQL_STATE_SUCCESSFUL_COMPLETION:
            return result_set
        await asyncio.sleep(1)  # Don't use return value
        return await self.wait_for_completion(statement_id)
