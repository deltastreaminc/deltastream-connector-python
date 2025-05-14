from deltastream.api.conn import APIConnection
from deltastream.api.controlplane.openapi_client.exceptions import ApiException
from deltastream.api.error import SQLError
import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from deltastream.api.controlplane.openapi_client.models.result_set import ResultSet
from deltastream.api.controlplane.openapi_client.models.result_set_metadata import ResultSetMetadata
from deltastream.api.controlplane.openapi_client.models.result_set_context import ResultSetContext
from deltastream.api.handlers import StatementHandler, StatementRequest

pytestmark = pytest.mark.asyncio


async def test_statement_handler_submit_statement_passes_compute_pool_name():
    rsctx = ResultSetContext(compute_pool_name="pool42")
    handler = StatementHandler(
        api=MagicMock(), rsctx=rsctx, session_id="sid", timezone="UTC"
    )
    with patch(
        "deltastream.api.handlers.StatementRequest", wraps=StatementRequest
    ) as MockRequest:
        handler.api.submit_statement = Mock(
            return_value=ResultSet(
                statement_id="sid",
                sql_state="00000",
                message=None,
                metadata=ResultSetMetadata(context=rsctx.__dict__, encoding="json"),
                createdOn=1704067200,
            )
        )
        await handler.submit_statement("SELECT 1")
        args, kwargs = MockRequest.call_args
        assert kwargs.get("computePool") == "pool42"

async def test_query_handles_sql_error():
    rsctx = ResultSetContext(compute_pool_name="pool42")
    handler = StatementHandler(
        api=MagicMock(), rsctx=rsctx, session_id="sid", timezone="UTC"
    )

    # Simulate a ResultSet with an error SQL state
    error_result = ResultSet(
        statement_id="sid",
        sql_state="42601",  # SQL state indicating a syntax error
        message="Syntax error near 'FROM'",
        metadata=ResultSetMetadata(context=rsctx.__dict__, encoding="json"),
        createdOn=1704067200,
    )
    handler.api.submit_statement = Mock(return_value=error_result)

    with pytest.raises(SQLError) as exc_info:
        await handler.submit_statement("SELECT * FROM nonexistent_table")
    
    assert "Syntax error near 'FROM'" in str(exc_info.value)
    assert exc_info.value.code == "42601"
    assert exc_info.value.statement_id == "sid"

@pytest.mark.parametrize("status_code,expected_error,error_message", [
    (400, "InterfaceError", "Bad request"),
    (401, "AuthenticationError", "Unauthorized"),
    (403, "AuthenticationError", "Forbidden"),
    (404, "InterfaceError", "Not found"),
    (408, "TimeoutError", "Request timeout"),
    (500, "ServerError", "Internal server error"),
    (503, "ServiceUnavailableError", "Service unavailable"),
    (418, "InterfaceError", "Unexpected interface error"),  # Testing default case
])
async def test_map_error_response(status_code, expected_error, error_message):
    from deltastream.api.handlers import map_error_response
    from deltastream.api.error import (
        InterfaceError, AuthenticationError, ServerError,
        TimeoutError, ServiceUnavailableError
    )

    # Create an API exception with the test parameters
    error = ApiException(status=status_code, reason=error_message)
    error.body = f'{{"message": "{error_message}"}}'

    # Map the error class name to the actual error class
    error_classes = {
        "InterfaceError": InterfaceError,
        "AuthenticationError": AuthenticationError,
        "ServerError": ServerError,
        "TimeoutError": TimeoutError,
        "ServiceUnavailableError": ServiceUnavailableError,
    }
    expected_exception = error_classes[expected_error]

    # Test that the correct exception is raised
    with pytest.raises(expected_exception) as exc_info:
        map_error_response(error)
    assert error_message in str(exc_info.value)

async def test_map_error_response_handles_invalid_json():
    from deltastream.api.handlers import map_error_response
    from deltastream.api.error import InterfaceError

    # Create an API exception with invalid JSON in body
    error = ApiException(status=400, reason="Bad request")
    error.body = "Invalid JSON {]"

    with pytest.raises(InterfaceError) as exc_info:
        map_error_response(error)
    assert str(error) in str(exc_info.value)

async def test_map_error_response_handles_none_body():
    from deltastream.api.handlers import map_error_response
    from deltastream.api.error import InterfaceError

    # Create an API exception with None body
    error = ApiException(status=400, reason="Bad request")
    error.body = None

    with pytest.raises(InterfaceError) as exc_info:
        map_error_response(error)
    assert str(error) in str(exc_info.value)

