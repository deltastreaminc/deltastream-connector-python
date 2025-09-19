from typing import Optional, List, Union, Tuple
import json
from uuid import UUID
from deltastream.api.controlplane.openapi_client.exceptions import ApiException
from deltastream.api.controlplane.openapi_client.models import (
    ResultSet,
    StatementStatus,
)
from deltastream.api.controlplane.openapi_client.models.statement_request import (
    StatementRequest,
    StatementRequestParameters,
)
from .error import (
    InterfaceError,
    AuthenticationError,
    ServerError,
    TimeoutError,
    ServiceUnavailableError,
    SQLError,
)
from deltastream.api.controlplane.openapi_client.api import DeltastreamApi
from .models import ResultSetContext
from .blob import Blob
from pydantic import ValidationError
import asyncio
from deltastream.api.error import SqlState


class StatementHandler:
    def __init__(
        self,
        api: DeltastreamApi,
        rsctx: ResultSetContext,
        session_id: Optional[str],
        timezone: str,
    ):
        self.api = api
        self.rsctx = rsctx
        self.session_id = session_id
        self.timezone = timezone

    async def submit_statement(
        self, query: str, attachments: Optional[List[Blob]] = None
    ) -> ResultSet:
        try:
            statement_request = StatementRequest(
                statement=query,
                organization=str(self.rsctx.organization_id)
                if self.rsctx.organization_id is not None
                else None,
                role=self.rsctx.role_name,
                database=self.rsctx.database_name,
                schema=self.rsctx.schema_name,
                store=self.rsctx.store_name,
                computePool=self.rsctx.compute_pool_name,
                parameters=StatementRequestParameters(
                    sessionID=self.session_id,
                    timezone=self.timezone,
                ),
            )
            if not statement_request.statement:
                raise ValueError("The statement field cannot be empty.")

            attachments_list: Optional[List[Union[bytes, str, Tuple[str, bytes]]]] = (
                [
                    (b.name if b.name else "attachment", b.to_bytes())
                    for b in attachments
                ]
                if attachments
                else None
            )

            initial_response = self.api.submit_statement(
                request=statement_request,
                attachments=attachments_list,
                _content_type="multipart/form-data",
            )
            if isinstance(initial_response, ResultSet):
                result_set = initial_response
            elif isinstance(initial_response, StatementStatus):
                status_response = initial_response
                result_set = await self.get_statement_status(
                    statement_id=status_response.statement_id, partition_id=0
                )
            else:
                raise ValueError(
                    f"Unexpected response type from submit_statement: {type(initial_response)}"
                )

            match result_set.sql_state:
                case SqlState.SQL_STATE_SUCCESSFUL_COMPLETION:
                    return result_set
                case SqlState.SQL_STATE_SQL_STATEMENT_NOT_YET_COMPLETE:
                    return await self.get_resultset(result_set.statement_id, 0)
                case _:
                    from deltastream.api.error import SQLError

                    raise SQLError(
                        result_set.message or "No message provided",
                        result_set.sql_state,
                        result_set.statement_id,
                    )

        except ValidationError:
            raise
        except ApiException as err:
            map_error_response(err)
            raise

    async def get_statement_status(
        self, statement_id: UUID, partition_id: int
    ) -> ResultSet:
        try:
            result_set = self.api.get_statement_status(
                statement_id=statement_id,
                session_id=self.session_id,
                partition_id=partition_id,
            )

            match result_set.sql_state:
                case SqlState.SQL_STATE_SUCCESSFUL_COMPLETION:
                    return result_set
                case SqlState.SQL_STATE_SQL_STATEMENT_NOT_YET_COMPLETE:
                    await asyncio.sleep(1)
                    return await self.get_statement_status(result_set.statement_id, 0)
                case _:
                    raise SQLError(
                        result_set.message or "No message provided",
                        result_set.sql_state,
                        result_set.statement_id,
                    )

        except ApiException as err:
            map_error_response(err)
            raise
        except Exception as e:
            raise e

    async def get_resultset(self, statement_id: UUID, partition_id: int) -> ResultSet:
        initial_response = await self.get_statement_status(statement_id, partition_id)
        result = initial_response

        if initial_response.metadata.dataplane_request:
            status_response = await self.get_statement_status(
                statement_id, partition_id
            )
            final_result = status_response
            return final_result

        return result


def map_error_response(err: ApiException) -> None:
    """Map API exceptions to appropriate error types."""
    try:
        if err.body is not None:
            data = json.loads(err.body)
            message = data.get("message", str(err))
        else:
            message = str(err)
    except (json.JSONDecodeError, AttributeError):
        message = str(err)

    error_mapping = {
        400: lambda e: InterfaceError(message),
        401: lambda e: AuthenticationError(message),
        403: lambda e: AuthenticationError(message),
        404: lambda e: InterfaceError(f"path not found: {message}"),
        408: lambda e: TimeoutError(message),
        500: lambda e: ServerError(message),
        503: lambda e: ServiceUnavailableError(message),
    }

    handler = error_mapping.get(err.status, lambda e: InterfaceError(message))
    raise handler(err)
