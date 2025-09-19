import pytest
import uuid
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from deltastream.api.conn import APIConnection
from deltastream.api.error import AuthenticationError
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
from deltastream.api.controlplane.openapi_client.models.result_set_partition_info import (
    ResultSetPartitionInfo,
)
from deltastream.api.controlplane.openapi_client.models.result_set_columns_inner import (
    ResultSetColumnsInner,
)
from deltastream.api.controlplane.openapi_client.exceptions import ApiException
from deltastream.api.blob import Blob
import tempfile
import os

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
        organization_id=str(uuid.uuid4()),
        role_name="new_role",
        database_name="new_db",
        schema_name="new_schema",
        store_name="new_store",
        compute_pool_name="new_pool",
    )
    mock_metadata = ResultSetMetadata(
        context=mock_context, 
        encoding="json",
        partition_info=[ResultSetPartitionInfo(row_count=1)],
        columns=[ResultSetColumnsInner(name="col1", type="VARCHAR", nullable=True)]
    )
    mock_result = ResultSet(
        metadata=mock_metadata,
        sql_state="00000",
        statement_id=str(uuid.uuid4()),
        message=None,
        createdOn=1704067200,
    )
    conn.submit_statement = AsyncMock(return_value=mock_result)
    await conn.exec("USE DATABASE new_db")
    assert conn.rsctx.organization_id == mock_context.organization_id
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
        organization_id=str(uuid.uuid4()),
        role_name="new_role",
        database_name="new_db",
        schema_name="new_schema",
        store_name="new_store",
    )
    mock_metadata = ResultSetMetadata(
        encoding="json", 
        context=mock_context,
        partition_info=[ResultSetPartitionInfo(row_count=1)],
        columns=[ResultSetColumnsInner(name="col1", type="VARCHAR", nullable=True)]
    )
    mock_result = ResultSet(
        metadata=mock_metadata,
        sql_state="00000",
        statement_id=str(uuid.uuid4()),
        created_on=1710848400,
    )

    conn.submit_statement = AsyncMock(return_value=mock_result)

    await conn.exec("USE DATABASE new_db")

    assert conn.rsctx.organization_id == mock_context.organization_id
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
    mock_metadata = ResultSetMetadata(
        encoding="json",
        partition_info=[ResultSetPartitionInfo(row_count=1)],
        columns=[ResultSetColumnsInner(name="col1", type="VARCHAR", nullable=True)]
    )
    mock_result = ResultSet(
        metadata=mock_metadata,
        sql_state="00000",
        statement_id=str(uuid.uuid4()),
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
        statement_id=str(uuid.uuid4()),
        token="dp_token",
        request_type="result-set",
    )
    mock_metadata = ResultSetMetadata(
        encoding="json", 
        dataplane_request=mock_dp_request,
        partition_info=[ResultSetPartitionInfo(row_count=1)],
        columns=[ResultSetColumnsInner(name="col1", type="VARCHAR", nullable=True)]
    )
    mock_result = ResultSet(
        metadata=mock_metadata,
        sql_state="00000",
        statement_id=str(uuid.uuid4()),
        created_on=1710848400,
    )

    conn.submit_statement = AsyncMock(return_value=mock_result)

    with patch("deltastream.api.conn.DPAPIConnection") as mock_dp_conn:
        # Provide a valid ResultSet as the return value for get_statement_status
        dp_result = ResultSet(
            metadata=mock_metadata,
            sql_state="00000",
            statement_id=str(uuid.uuid4()),
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

    mock_metadata = ResultSetMetadata(
        encoding="json",
        partition_info=[ResultSetPartitionInfo(row_count=1)],
        columns=[ResultSetColumnsInner(name="col1", type="VARCHAR", nullable=True)]
    )
    mock_result = ResultSet(
        metadata=mock_metadata,
        sql_state="00000",
        statement_id=str(uuid.uuid4()),
        created_on=1710848400,
    )
    conn.statement_handler.get_statement_status = AsyncMock(return_value=mock_result)

    result = await conn.get_statement_status("statement_123", 0)
    assert result is not None
    assert isinstance(result, ResultSet)


async def test_exec_with_files_simple_file_paths():
    """Test exec_with_files with simple file paths."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    # Create temporary test files
    with tempfile.NamedTemporaryFile(suffix=".jar", delete=False) as f1:
        f1.write(b"test jar content")
        jar_path = f1.name

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f2:
        f2.write(b"test text content")
        txt_path = f2.name

    try:
        # Mock the exec method to capture the attachments
        mock_exec = AsyncMock()
        conn.exec = mock_exec

        query = "CREATE FUNCTION_SOURCE \"my_func\" WITH ('file' = 'test.jar');"
        await conn.exec_with_files(query, [jar_path, txt_path])

        # Verify exec was called with correct parameters
        mock_exec.assert_called_once()
        call_args = mock_exec.call_args
        assert call_args[0][0] == query  # First positional arg is query
        attachments = call_args[0][1]  # Second positional arg is attachments

        assert len(attachments) == 2
        assert all(isinstance(blob, Blob) for blob in attachments)
        assert attachments[0].name == os.path.basename(jar_path)
        assert attachments[1].name == os.path.basename(txt_path)
        assert attachments[0].content_type == "application/java-archive"
        assert attachments[1].content_type == "text/plain"
        assert attachments[0].to_bytes() == b"test jar content"
        assert attachments[1].to_bytes() == b"test text content"

    finally:
        # Clean up temporary files
        os.unlink(jar_path)
        os.unlink(txt_path)


async def test_exec_with_files_dict_config():
    """Test exec_with_files with dictionary configuration."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    # Create temporary test file
    with tempfile.NamedTemporaryFile(suffix=".jar", delete=False) as f:
        f.write(b"custom jar content")
        jar_path = f.name

    try:
        # Mock the exec method
        mock_exec = AsyncMock()
        conn.exec = mock_exec

        query = "CREATE FUNCTION_SOURCE \"my_func\" WITH ('file' = 'custom_name.jar');"
        file_config = [
            {
                "path": jar_path,
                "name": "custom_name.jar",
                "content_type": "application/java-archive",
            }
        ]
        await conn.exec_with_files(query, file_config)

        # Verify exec was called with correct parameters
        mock_exec.assert_called_once()
        call_args = mock_exec.call_args
        attachments = call_args[0][1]

        assert len(attachments) == 1
        assert attachments[0].name == "custom_name.jar"
        assert attachments[0].content_type == "application/java-archive"
        assert attachments[0].to_bytes() == b"custom jar content"

    finally:
        os.unlink(jar_path)


async def test_exec_with_files_no_files():
    """Test exec_with_files with no files provided."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    # Mock the exec method
    mock_exec = AsyncMock()
    conn.exec = mock_exec

    query = "SELECT * FROM my_table;"
    await conn.exec_with_files(query, None)

    # Verify exec was called with None attachments
    mock_exec.assert_called_once_with(query, None)


async def test_exec_with_files_empty_list():
    """Test exec_with_files with empty file list."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    # Mock the exec method
    mock_exec = AsyncMock()
    conn.exec = mock_exec

    query = "SELECT * FROM my_table;"
    await conn.exec_with_files(query, [])

    # Verify exec was called with empty attachments list
    mock_exec.assert_called_once_with(query, [])


async def test_exec_with_files_invalid_file_config():
    """Test exec_with_files with invalid file configuration."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    query = "SELECT * FROM my_table;"

    # Test with invalid type in file_paths
    with pytest.raises(
        ValueError, match="file_paths must contain strings or dictionaries"
    ):
        await conn.exec_with_files(query, [123])  # Invalid type


async def test_exec_with_files_missing_file():
    """Test exec_with_files with non-existent file."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    query = "SELECT * FROM my_table;"

    # Test with non-existent file
    with pytest.raises(FileNotFoundError):
        await conn.exec_with_files(query, ["/non/existent/file.jar"])


async def test_query_with_files_simple_file_paths():
    """Test query_with_files with simple file paths."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    # Create temporary test file
    with tempfile.NamedTemporaryFile(suffix=".jar", delete=False) as f:
        f.write(b"test jar content")
        jar_path = f.name

    try:
        # Mock the query method
        mock_rows = Mock()
        mock_query = AsyncMock(return_value=mock_rows)
        conn.query = mock_query

        query = "SELECT * FROM my_function('test.jar');"
        result = await conn.query_with_files(query, [jar_path])

        # Verify query was called with correct parameters
        mock_query.assert_called_once()
        call_args = mock_query.call_args
        assert call_args[0][0] == query
        attachments = call_args[0][1]

        assert len(attachments) == 1
        assert attachments[0].name == os.path.basename(jar_path)
        assert attachments[0].content_type == "application/java-archive"
        assert attachments[0].to_bytes() == b"test jar content"

        # Verify return value
        assert result is mock_rows

    finally:
        os.unlink(jar_path)


async def test_query_with_files_dict_config():
    """Test query_with_files with dictionary configuration."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    # Create temporary test file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"test content")
        file_path = f.name

    try:
        # Mock the query method
        mock_rows = Mock()
        mock_query = AsyncMock(return_value=mock_rows)
        conn.query = mock_query

        query = "SELECT * FROM my_function('custom.txt');"
        file_config = [
            {"path": file_path, "name": "custom.txt", "content_type": "text/plain"}
        ]
        result = await conn.query_with_files(query, file_config)

        # Verify query was called with correct parameters
        mock_query.assert_called_once()
        call_args = mock_query.call_args
        attachments = call_args[0][1]

        assert len(attachments) == 1
        assert attachments[0].name == "custom.txt"
        assert attachments[0].content_type == "text/plain"
        assert attachments[0].to_bytes() == b"test content"

        # Verify return value
        assert result is mock_rows

    finally:
        os.unlink(file_path)


async def test_query_with_files_no_files():
    """Test query_with_files with no files provided."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    # Mock the query method
    mock_rows = Mock()
    mock_query = AsyncMock(return_value=mock_rows)
    conn.query = mock_query

    query = "SELECT * FROM my_table;"
    result = await conn.query_with_files(query, None)

    # Verify query was called with None attachments
    mock_query.assert_called_once_with(query, None)
    assert result is mock_rows


async def test_query_with_files_mixed_config():
    """Test query_with_files with mixed string and dict configuration."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    # Create temporary test files
    with tempfile.NamedTemporaryFile(suffix=".jar", delete=False) as f1:
        f1.write(b"jar content")
        jar_path = f1.name

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f2:
        f2.write(b"text content")
        txt_path = f2.name

    try:
        # Mock the query method
        mock_rows = Mock()
        mock_query = AsyncMock(return_value=mock_rows)
        conn.query = mock_query

        query = "SELECT * FROM my_function('test.jar', 'custom.txt');"
        file_config = [
            jar_path,  # Simple string path
            {"path": txt_path, "name": "custom.txt", "content_type": "text/plain"},
        ]
        result = await conn.query_with_files(query, file_config)

        # Verify query was called with correct parameters
        mock_query.assert_called_once()
        call_args = mock_query.call_args
        attachments = call_args[0][1]

        assert len(attachments) == 2

        # First attachment (from string path)
        assert attachments[0].name == os.path.basename(jar_path)
        assert attachments[0].content_type == "application/java-archive"
        assert attachments[0].to_bytes() == b"jar content"

        # Second attachment (from dict config)
        assert attachments[1].name == "custom.txt"
        assert attachments[1].content_type == "text/plain"
        assert attachments[1].to_bytes() == b"text content"

        # Verify return value
        assert result is mock_rows

    finally:
        os.unlink(jar_path)
        os.unlink(txt_path)


async def test_query_with_files_invalid_file_config():
    """Test query_with_files with invalid file configuration."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    query = "SELECT * FROM my_table;"

    # Test with invalid type in file_paths
    with pytest.raises(
        ValueError, match="file_paths must contain strings or dictionaries"
    ):
        await conn.query_with_files(query, [123])  # Invalid type


async def test_exec_with_files_dict_missing_path():
    """Test exec_with_files with dictionary missing required path key."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    query = "SELECT * FROM my_table;"
    file_config = [{"name": "test.jar"}]  # Missing 'path' key

    with pytest.raises(KeyError):
        await conn.exec_with_files(query, file_config)


async def test_query_with_files_dict_missing_path():
    """Test query_with_files with dictionary missing required path key."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    query = "SELECT * FROM my_table;"
    file_config = [{"name": "test.jar"}]  # Missing 'path' key

    with pytest.raises(KeyError):
        await conn.query_with_files(query, file_config)


async def test_exec_with_files_unknown_content_type():
    """Test exec_with_files with unknown file extension."""

    async def token_provider() -> str:
        return "valid_token"

    conn = APIConnection.from_dsn(
        "https://_:sometoken@api.deltastream.io/v2?sessionID=123", token_provider
    )

    # Create temporary test file with unknown extension
    with tempfile.NamedTemporaryFile(suffix=".unknown", delete=False) as f:
        f.write(b"unknown content")
        unknown_path = f.name

    try:
        # Mock the exec method
        mock_exec = AsyncMock()
        conn.exec = mock_exec

        query = "SELECT * FROM my_function('test.unknown');"
        await conn.exec_with_files(query, [unknown_path])

        # Verify exec was called with correct parameters
        mock_exec.assert_called_once()
        call_args = mock_exec.call_args
        attachments = call_args[0][1]

        assert len(attachments) == 1
        assert attachments[0].name == os.path.basename(unknown_path)
        assert attachments[0].content_type is None  # Unknown content type
        assert attachments[0].to_bytes() == b"unknown content"

    finally:
        os.unlink(unknown_path)
