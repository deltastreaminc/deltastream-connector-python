"""
Tests for streaming_rows.py module
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from deltastream.api.streaming_rows import StreamingRows, PrintTopicMetadata
from deltastream.api.models import DataplaneRequest
from deltastream.api.dpconn import DPAPIConnection
from deltastream.api.rows import Column
from uuid import uuid4

pytestmark = pytest.mark.asyncio


class TestStreamingRowsURLConversion:
    """Test WebSocket URL scheme conversion"""

    async def test_websocket_connection_with_url_conversion(self):
        """Test that WebSocket connects with converted URL"""
        conn = MagicMock(spec=DPAPIConnection)
        conn.token = "test_token"
        conn.session_id = "test_session"

        req = DataplaneRequest(
            uri="https://api.deltastream.io/v2/print/123",
            statement_id=uuid4(),
            token="test_token",
            request_type="print",
        )

        rows = StreamingRows(conn, req)

        # Mock WebSocket connection with async iterator
        async def async_message_generator():
            yield json.dumps(
                {
                    "type": "metadata",
                    "headers": {},
                    "columns": [{"name": "col1", "type": "VARCHAR", "nullable": True}],
                }
            )

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.__aiter__ = lambda self: async_message_generator()

        with patch(
            "deltastream.api.streaming_rows.ws_connect",
            new=AsyncMock(return_value=mock_ws),
        ) as mock_connect:
            await rows.open()

            # Verify WebSocket was called with WSS URL
            mock_connect.assert_called_once()
            called_url = mock_connect.call_args[0][0]
            assert called_url == "wss://api.deltastream.io/v2/print/123"
            assert called_url.startswith("wss://")


class TestStreamingRowsMetadataParsing:
    """Test metadata parsing and column conversion"""

    async def test_metadata_columns_conversion_from_dict(self):
        """Test that metadata columns are converted from dictionaries to Column objects"""
        conn = MagicMock(spec=DPAPIConnection)
        conn.token = "test_token"
        conn.session_id = "test_session"

        req = DataplaneRequest(
            uri="https://api.deltastream.io/v2/print/123",
            statement_id=uuid4(),
            token="test_token",
            request_type="print",
        )

        rows = StreamingRows(conn, req)

        # Mock WebSocket with metadata message
        metadata_msg = json.dumps(
            {
                "type": "metadata",
                "headers": {"content-type": "application/json"},
                "columns": [
                    {"name": "user_id", "type": "VARCHAR", "nullable": False},
                    {"name": "view_time", "type": "BIGINT", "nullable": True},
                    {"name": "page_id", "type": "VARCHAR", "nullable": True},
                ],
            }
        )

        async def async_message_generator():
            yield metadata_msg

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.__aiter__ = lambda self: async_message_generator()

        with patch(
            "deltastream.api.streaming_rows.ws_connect",
            new=AsyncMock(return_value=mock_ws),
        ):
            await rows.open()

            # Verify metadata is set correctly
            assert rows.metadata is not None
            assert isinstance(rows.metadata, PrintTopicMetadata)
            assert len(rows.metadata.columns) == 3

            # Verify columns are Column objects, not dicts
            for col in rows.metadata.columns:
                assert isinstance(col, Column)

            # Verify column data
            assert rows.metadata.columns[0].name == "user_id"
            assert rows.metadata.columns[0].type == "VARCHAR"
            assert rows.metadata.columns[0].nullable is False

            assert rows.metadata.columns[1].name == "view_time"
            assert rows.metadata.columns[1].type == "BIGINT"
            assert rows.metadata.columns[1].nullable is True

    async def test_columns_method_returns_column_objects(self):
        """Test that columns() method returns the parsed Column objects"""
        conn = MagicMock(spec=DPAPIConnection)
        conn.token = "test_token"
        conn.session_id = "test_session"

        req = DataplaneRequest(
            uri="https://api.deltastream.io/v2/print/123",
            statement_id=uuid4(),
            token="test_token",
            request_type="print",
        )

        rows = StreamingRows(conn, req)

        # Mock WebSocket with metadata message
        metadata_msg = json.dumps(
            {
                "type": "metadata",
                "headers": {},
                "columns": [
                    {"name": "col1", "type": "INTEGER", "nullable": False},
                    {"name": "col2", "type": "VARCHAR", "nullable": True},
                ],
            }
        )

        async def async_message_generator():
            yield metadata_msg

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.__aiter__ = lambda self: async_message_generator()

        with patch(
            "deltastream.api.streaming_rows.ws_connect",
            new=AsyncMock(return_value=mock_ws),
        ):
            await rows.open()

            columns = rows.columns()

            # Verify columns are returned directly from metadata
            assert len(columns) == 2
            assert columns is rows.metadata.columns
            assert all(isinstance(col, Column) for col in columns)

    async def test_columns_method_empty_when_no_metadata(self):
        """Test that columns() returns empty list when metadata is None"""
        conn = MagicMock(spec=DPAPIConnection)
        req = DataplaneRequest(
            uri="https://api.deltastream.io/v2/print/123",
            statement_id=uuid4(),
            token="test_token",
            request_type="print",
        )

        rows = StreamingRows(conn, req)

        # Before open() is called, metadata should be None
        assert rows.metadata is None
        columns = rows.columns()
        assert columns == []

    async def test_metadata_with_optional_column_fields(self):
        """Test metadata parsing with optional column fields (length, precision, scale)"""
        conn = MagicMock(spec=DPAPIConnection)
        conn.token = "test_token"
        conn.session_id = "test_session"

        req = DataplaneRequest(
            uri="https://api.deltastream.io/v2/print/123",
            statement_id=uuid4(),
            token="test_token",
            request_type="print",
        )

        rows = StreamingRows(conn, req)

        # Mock WebSocket with metadata including optional fields
        metadata_msg = json.dumps(
            {
                "type": "metadata",
                "headers": {},
                "columns": [
                    {
                        "name": "price",
                        "type": "DECIMAL",
                        "nullable": False,
                        "precision": 10,
                        "scale": 2,
                    },
                    {
                        "name": "description",
                        "type": "VARCHAR",
                        "nullable": True,
                        "length": 255,
                    },
                ],
            }
        )

        async def async_message_generator():
            yield metadata_msg

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.__aiter__ = lambda self: async_message_generator()

        with patch(
            "deltastream.api.streaming_rows.ws_connect",
            new=AsyncMock(return_value=mock_ws),
        ):
            await rows.open()

            columns = rows.columns()

            # Verify optional fields are parsed correctly
            assert columns[0].precision == 10
            assert columns[0].scale == 2

            assert columns[1].length == 255

    async def test_metadata_with_missing_nullable_field(self):
        """Test metadata parsing when nullable field is missing (defaults to True)"""
        conn = MagicMock(spec=DPAPIConnection)
        conn.token = "test_token"
        conn.session_id = "test_session"

        req = DataplaneRequest(
            uri="https://api.deltastream.io/v2/print/123",
            statement_id=uuid4(),
            token="test_token",
            request_type="print",
        )

        rows = StreamingRows(conn, req)

        # Mock WebSocket with metadata missing nullable field
        metadata_msg = json.dumps(
            {
                "type": "metadata",
                "headers": {},
                "columns": [
                    {
                        "name": "user_id",
                        "type": "VARCHAR",
                        # nullable field is missing - should default to True
                    },
                    {
                        "name": "view_time",
                        "type": "BIGINT",
                        # nullable field is missing - should default to True
                    },
                ],
            }
        )

        async def async_message_generator():
            yield metadata_msg

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.__aiter__ = lambda self: async_message_generator()

        with patch(
            "deltastream.api.streaming_rows.ws_connect",
            new=AsyncMock(return_value=mock_ws),
        ):
            await rows.open()

            columns = rows.columns()

            # Verify columns are created successfully despite missing nullable field
            assert len(columns) == 2
            assert all(isinstance(col, Column) for col in columns)

            # Verify nullable defaults to True when missing
            assert columns[0].name == "user_id"
            assert columns[0].type == "VARCHAR"
            assert columns[0].nullable is True  # Should default to True

            assert columns[1].name == "view_time"
            assert columns[1].type == "BIGINT"
            assert columns[1].nullable is True  # Should default to True


class TestStreamingRowsDataHandling:
    """Test data message handling with the new column parsing"""

    async def test_data_message_with_parsed_columns(self):
        """Test that data messages are processed correctly with parsed columns"""
        conn = MagicMock(spec=DPAPIConnection)
        conn.token = "test_token"
        conn.session_id = "test_session"

        req = DataplaneRequest(
            uri="https://api.deltastream.io/v2/print/123",
            statement_id=uuid4(),
            token="test_token",
            request_type="print",
        )

        rows = StreamingRows(conn, req)

        # Mock WebSocket with metadata and data messages
        messages = [
            json.dumps(
                {
                    "type": "metadata",
                    "headers": {},
                    "columns": [
                        {"name": "id", "type": "INTEGER", "nullable": False},
                        {"name": "name", "type": "VARCHAR", "nullable": True},
                    ],
                }
            ),
            json.dumps({"type": "data", "headers": {}, "data": ["123", "test_name"]}),
        ]

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.open = True

        # Use an async generator for messages
        async def message_generator():
            for msg in messages:
                yield msg

        mock_ws.__aiter__ = lambda self: message_generator()

        with patch(
            "deltastream.api.streaming_rows.ws_connect",
            new=AsyncMock(return_value=mock_ws),
        ):
            with patch("deltastream.api.streaming_rows.castRowData") as mock_cast:
                mock_cast.return_value = [123, "test_name"]

                await rows.open()

                # Verify castRowData was called with the correct columns
                mock_cast.assert_called_once()
                call_args = mock_cast.call_args

                # First arg should be the data
                assert call_args[0][0] == ["123", "test_name"]

                # Second arg should be the columns
                columns = call_args[0][1]
                assert len(columns) == 2
                assert all(isinstance(col, Column) for col in columns)
                assert columns[0].name == "id"
                assert columns[1].name == "name"
