import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from deltastream.api.conn import APIConnection
from deltastream.api.error import AuthenticationError, SQLError
from deltastream.api.controlplane.openapi_client.models.version import (
    Version as ApiVersion,
)
from deltastream.api.controlplane.openapi_client.models.result_set import ResultSet
from deltastream.api.controlplane.openapi_client.models.result_set_metadata import (
    ResultSetMetadata,
)
from deltastream.api.controlplane.openapi_client.models.result_set_context import (
    ResultSetContext,
)
from deltastream.api.controlplane.openapi_client.models.dataplane_request import (
    DataplaneRequest,
)
from deltastream.api.controlplane.openapi_client.exceptions import ApiException
from deltastream.api.handlers import StatementRequest

pytestmark = pytest.mark.asyncio


async def test_should_throw_auth_error_if_no_token_provided():
    with pytest.raises(AuthenticationError):
        APIConnection.from_dsn("https://api.deltastream.io/v2?sessionID=123")


async def test_should_throw_auth_error_if_invalid_token_provided():
    async def token_provider():
        return "invalid_token"

    conn = APIConnection.from_dsn(
        "https://api.deltastream.io/v2?sessionID=123", token_provider
    )
    mock_api = MagicMock()
    error = ApiException(status=401, reason="Unauthorized")
    error.body = '{"code": "401", "message": "Invalid token"}'
    mock_api.get_version.side_effect = error
    conn.statement_handler.api = mock_api

    with pytest.raises(AuthenticationError):
        await conn.version()


async def test_should_succeed_if_valid_token_provided_in_url():
    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123"
    )
    mock_api = MagicMock()
    version_response = ApiVersion(major=2, minor=0, patch=0)
    mock_api.get_version.return_value = version_response
    conn.statement_handler.api = mock_api

    version = await conn.version()
    assert version == {"major": 2, "minor": 0, "patch": 0}


async def test_should_succeed_if_valid_token_provided_as_callback():
    async def token_provider() -> str:
        return "sometoken"

    conn = APIConnection.from_dsn(
        "https://api.deltastream.io/v2?sessionID=123", token_provider
    )
    mock_api = MagicMock()
    version_response = ApiVersion(major=2, minor=0, patch=0)
    mock_api.get_version.return_value = version_response
    conn.statement_handler.api = mock_api

    version = await conn.version()
    assert version == {"major": 2, "minor": 0, "patch": 0}


async def test_exec_updates_context():
    # Also test compute_pool_name update
    async def token_provider() -> str:
        return "sometoken"

    conn = APIConnection.from_dsn(
        "https://api.deltastream.io/v2?sessionID=123", token_provider
    )
    # Mock the submit_statement response
    mock_context = ResultSetContext(
        organization_id="new_org",
        role_name="new_role",
        database_name="new_db",
        schema_name="new_schema",
        store_name="new_store",
        compute_pool_name="new_pool",
    )
    mock_metadata = ResultSetMetadata(context=mock_context.__dict__, encoding="json")
    mock_result = ResultSet(
        metadata=mock_metadata,
        sql_state="00000",
        statement_id="test_statement_id",
        message=None,
        createdOn=1704067200,
    )
    conn.submit_statement = AsyncMock(return_value=mock_result)
    await conn.exec("USE DATABASE new_db")
    assert conn.rsctx.organization_id == "new_org"
    assert conn.rsctx.role_name == "new_role"
    assert conn.rsctx.database_name == "new_db"
    assert conn.rsctx.schema_name == "new_schema"
    assert conn.rsctx.store_name == "new_store"
    assert conn.rsctx.compute_pool_name == "new_pool"


async def test_from_dsn_parses_compute_pool_name():
    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123&computePoolName=my_pool"
    )
    assert conn.rsctx.compute_pool_name == "my_pool"

    async def token_provider() -> str:
        return "sometoken"

    conn = APIConnection.from_dsn(
        "https://api.deltastream.io/v2?sessionID=123", token_provider
    )

    # Mock the submit_statement response
    mock_context = ResultSetContext(
        organization_id="new_org",
        role_name="new_role",
        database_name="new_db",
        schema_name="new_schema",
        store_name="new_store",
    )
    mock_metadata = ResultSetMetadata(encoding="json", context=mock_context)
    mock_result = ResultSet(
        metadata=mock_metadata,
        sql_state="00000",
        statement_id="test_statement_id",
        created_on=1710848400,
    )

    conn.submit_statement = AsyncMock(return_value=mock_result)

    await conn.exec("USE DATABASE new_db")

    assert conn.rsctx.organization_id == "new_org"
    assert conn.rsctx.role_name == "new_role"
    assert conn.rsctx.database_name == "new_db"
    assert conn.rsctx.schema_name == "new_schema"
    assert conn.rsctx.store_name == "new_store"


async def test_query_with_resultset():
    async def token_provider() -> str:
        return "sometoken"

    conn = APIConnection.from_dsn(
        "https://api.deltastream.io/v2?sessionID=123", token_provider
    )

    # Mock the submit_statement response for a regular result set
    mock_metadata = ResultSetMetadata(encoding="json")
    mock_result = ResultSet(
        metadata=mock_metadata,
        sql_state="00000",
        statement_id="test_statement_id",
        created_on=1710848400,
    )

    conn.submit_statement = AsyncMock(return_value=mock_result)
    conn.statement_handler.get_statement_status = AsyncMock()

    rows = await conn.query("SELECT * FROM table")
    assert rows is not None


async def test_query_with_dataplane():
    async def token_provider() -> str:
        return "sometoken"

    conn = APIConnection.from_dsn(
        "https://api.deltastream.io/v2?sessionID=123", token_provider
    )

    # Mock the submit_statement response for a data plane request
    mock_dp_request = DataplaneRequest(
        uri="https://dp.deltastream.io/v2/statements/123",
        statement_id="123",
        token="dp_token",
        request_type="result-set",
    )
    mock_metadata = ResultSetMetadata(
        encoding="json", dataplane_request=mock_dp_request
    )
    mock_result = ResultSet(
        metadata=mock_metadata,
        sql_state="00000",
        statement_id="test_statement_id",
        created_on=1710848400,
    )

    conn.submit_statement = AsyncMock(return_value=mock_result)

    with patch("deltastream.api.conn.DPAPIConnection") as mock_dp_conn:
        # Provide a valid ResultSet as the return value for get_statement_status
        dp_result = ResultSet(
            metadata=mock_metadata,
            sql_state="00000",
            statement_id="test_statement_id",
            created_on=1710848400,
        )
        mock_dp_conn.return_value.get_statement_status = AsyncMock(
            return_value=dp_result
        )
        rows = await conn.query("SELECT * FROM large_table")
    assert rows is not None

async def test_get_statement_status():
    async def token_provider() -> str:
        return "sometoken"

    conn = APIConnection.from_dsn(
        "https://api.deltastream.io/v2?sessionID=123", token_provider
    )

    mock_metadata = ResultSetMetadata(encoding="json")
    mock_result = ResultSet(
        metadata=mock_metadata,
        sql_state="00000",
        statement_id="test_statement_id",
        created_on=1710848400,
    )
    conn.statement_handler.get_statement_status = AsyncMock(return_value=mock_result)

    result = await conn.get_statement_status("statement_123", 0)
    assert result is not None
    assert isinstance(result, ResultSet)
