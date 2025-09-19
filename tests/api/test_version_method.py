"""
Comprehensive tests for the APIConnection.version() method.

This test module covers various scenarios for the version method including:
- Successful version retrieval
- Authentication errors
- API exceptions
- Network errors
- Valid token scenarios
"""

import pytest
from unittest.mock import MagicMock, patch
from deltastream.api.conn import APIConnection
from deltastream.api.error import (
    AuthenticationError,
    ServerError,
    ServiceUnavailableError,
)
from deltastream.api.controlplane.openapi_client.models.version import (
    Version as ApiVersion,
)
from deltastream.api.controlplane.openapi_client.exceptions import ApiException

pytestmark = pytest.mark.asyncio


class TestVersionMethod:
    """Test class for the APIConnection.version() method."""

    @pytest.fixture
    def mock_token_provider(self):
        """Create a mock token provider."""

        async def token_provider() -> str:
            return "valid_test_token"

        return token_provider

    @pytest.fixture
    def api_connection(self, mock_token_provider):
        """Create an APIConnection instance for testing."""
        return APIConnection.from_dsn(
            "https://api.deltastream.io/v2?sessionID=test123", mock_token_provider
        )

    async def test_version_success_with_valid_token(self, api_connection):
        """Test successful version retrieval with valid token."""
        # Arrange
        mock_api = MagicMock()
        version_response = ApiVersion(major=2, minor=1, patch=3)
        mock_api.get_version.return_value = version_response
        api_connection.statement_handler.api = mock_api

        # Act
        result = await api_connection.version()

        # Assert
        assert result == {"major": 2, "minor": 1, "patch": 3}
        assert isinstance(result, dict)
        assert "major" in result
        assert "minor" in result
        assert "patch" in result
        mock_api.get_version.assert_called_once()

    async def test_version_success_different_version_numbers(self, api_connection):
        """Test version method with different version number combinations."""
        test_cases = [
            (1, 0, 0),
            (2, 0, 5),
            (3, 12, 45),
            (10, 255, 1024),
        ]

        for major, minor, patch_version in test_cases:
            # Arrange
            mock_api = MagicMock()
            version_response = ApiVersion(major=major, minor=minor, patch=patch_version)
            mock_api.get_version.return_value = version_response
            api_connection.statement_handler.api = mock_api

            # Act
            result = await api_connection.version()

            # Assert
            assert result == {"major": major, "minor": minor, "patch": patch_version}

    async def test_version_authentication_error_401(self, api_connection):
        """Test version method with 401 authentication error."""
        # Arrange
        mock_api = MagicMock()
        error = ApiException(status=401, reason="Unauthorized")
        error.body = '{"code": "401", "message": "Invalid token"}'
        mock_api.get_version.side_effect = error
        api_connection.statement_handler.api = mock_api

        # Act & Assert
        with pytest.raises(AuthenticationError):
            await api_connection.version()

    async def test_version_authentication_error_403(self, api_connection):
        """Test version method with 403 forbidden error."""
        # Arrange
        mock_api = MagicMock()
        error = ApiException(status=403, reason="Forbidden")
        error.body = '{"code": "403", "message": "Access denied"}'
        mock_api.get_version.side_effect = error
        api_connection.statement_handler.api = mock_api

        # Act & Assert
        with pytest.raises(AuthenticationError):
            await api_connection.version()

    async def test_version_server_error_500(self, api_connection):
        """Test version method with 500 server error."""
        # Arrange
        mock_api = MagicMock()
        error = ApiException(status=500, reason="Internal Server Error")
        error.body = '{"code": "500", "message": "Server error"}'
        mock_api.get_version.side_effect = error
        api_connection.statement_handler.api = mock_api

        # Act & Assert
        with pytest.raises(ServerError):
            await api_connection.version()

    async def test_version_service_unavailable_503(self, api_connection):
        """Test version method with 503 service unavailable error."""
        # Arrange
        mock_api = MagicMock()
        error = ApiException(status=503, reason="Service Unavailable")
        error.body = '{"code": "503", "message": "Service temporarily unavailable"}'
        mock_api.get_version.side_effect = error
        api_connection.statement_handler.api = mock_api

        # Act & Assert
        with pytest.raises(ServiceUnavailableError):
            await api_connection.version()

    async def test_version_sets_auth_header_correctly(self, api_connection):
        """Test that version method correctly sets authentication header."""
        # Arrange
        mock_api = MagicMock()
        mock_api_client = MagicMock()
        mock_configuration = MagicMock()
        mock_headers = {}

        mock_api.api_client = mock_api_client
        mock_api_client.configuration = mock_configuration
        mock_api_client.default_headers = mock_headers

        version_response = ApiVersion(major=2, minor=0, patch=0)
        mock_api.get_version.return_value = version_response
        api_connection.statement_handler.api = mock_api

        # Act
        await api_connection.version()

        # Assert
        # Verify auth header was set
        assert mock_configuration.access_token == "valid_test_token"
        assert mock_headers["Authorization"] == "Bearer valid_test_token"

    async def test_version_with_token_from_dsn_url(self):
        """Test version method when token is provided in DSN URL."""
        # Arrange
        conn = APIConnection.from_dsn(
            "https://_:test_token_from_url@api.deltastream.io/v2?sessionID=test456"
        )
        mock_api = MagicMock()
        version_response = ApiVersion(major=1, minor=5, patch=10)
        mock_api.get_version.return_value = version_response
        conn.statement_handler.api = mock_api

        # Act
        result = await conn.version()

        # Assert
        assert result == {"major": 1, "minor": 5, "patch": 10}
        assert (
            conn.statement_handler.api.api_client.configuration.access_token
            == "test_token_from_url"
        )

    async def test_version_api_exception_without_body(self, api_connection):
        """Test version method with API exception that has no body."""
        # Arrange
        mock_api = MagicMock()
        error = ApiException(status=400, reason="Bad Request")
        error.body = None
        mock_api.get_version.side_effect = error
        api_connection.statement_handler.api = mock_api

        # Act & Assert
        with pytest.raises(Exception):  # Should raise mapped error
            await api_connection.version()

    async def test_version_api_exception_invalid_json_body(self, api_connection):
        """Test version method with API exception that has invalid JSON body."""
        # Arrange
        mock_api = MagicMock()
        error = ApiException(status=400, reason="Bad Request")
        error.body = "invalid json"
        mock_api.get_version.side_effect = error
        api_connection.statement_handler.api = mock_api

        # Act & Assert
        with pytest.raises(Exception):  # Should raise mapped error
            await api_connection.version()

    async def test_version_method_is_async(self, api_connection):
        """Test that version method is properly async."""
        import inspect

        # Assert
        assert inspect.iscoroutinefunction(api_connection.version)

    async def test_version_return_type_structure(self, api_connection):
        """Test that version method returns correctly structured dictionary."""
        # Arrange
        mock_api = MagicMock()
        version_response = ApiVersion(major=2, minor=3, patch=4)
        mock_api.get_version.return_value = version_response
        api_connection.statement_handler.api = mock_api

        # Act
        result = await api_connection.version()

        # Assert
        assert isinstance(result, dict)
        assert len(result) == 3
        assert set(result.keys()) == {"major", "minor", "patch"}
        assert all(isinstance(v, int) for v in result.values())

    @patch("deltastream.api.conn.map_error_response")
    async def test_version_calls_map_error_response_on_exception(
        self, mock_map_error, api_connection
    ):
        """Test that version method calls map_error_response when ApiException occurs."""
        # Arrange
        mock_api = MagicMock()
        error = ApiException(status=500, reason="Server Error")
        mock_api.get_version.side_effect = error
        api_connection.statement_handler.api = mock_api

        # Mock map_error_response to raise a specific error so we can catch it
        mock_map_error.side_effect = ServerError("Mapped server error")

        # Act & Assert
        with pytest.raises(ServerError):
            await api_connection.version()

        # Verify map_error_response was called with the exception
        mock_map_error.assert_called_once_with(error)

    async def test_version_with_zero_version_numbers(self, api_connection):
        """Test version method with zero version numbers."""
        # Arrange
        mock_api = MagicMock()
        version_response = ApiVersion(major=0, minor=0, patch=0)
        mock_api.get_version.return_value = version_response
        api_connection.statement_handler.api = mock_api

        # Act
        result = await api_connection.version()

        # Assert
        assert result == {"major": 0, "minor": 0, "patch": 0}

    async def test_version_method_maintains_context(self, api_connection):
        """Test that version method doesn't modify connection context."""
        # Arrange
        original_rsctx = api_connection.rsctx
        original_session_id = api_connection.session_id

        mock_api = MagicMock()
        version_response = ApiVersion(major=2, minor=0, patch=0)
        mock_api.get_version.return_value = version_response
        api_connection.statement_handler.api = mock_api

        # Act
        await api_connection.version()

        # Assert - context should remain unchanged
        assert api_connection.rsctx is original_rsctx
        assert api_connection.session_id == original_session_id
