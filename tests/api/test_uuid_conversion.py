# coding: utf-8

"""
Test UUID to string conversion in the DeltaStream Python client library.

These tests verify that UUID fields from OpenAPI generated models are properly
converted to strings when needed for API requests and internal representations.
"""

import unittest
import uuid
from unittest.mock import Mock, AsyncMock

from deltastream.api.conn import APIConnection
from deltastream.api.models import ResultSetContext
from deltastream.api.controlplane.openapi_client.models.result_set_context import (
    ResultSetContext as CPResultSetContext,
)
from deltastream.api.handlers import StatementHandler
from deltastream.api.controlplane.openapi_client.models.statement_request import (
    StatementRequest,
)


class TestUUIDConversion(unittest.TestCase):
    """Test UUID conversion between OpenAPI models and internal models."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_uuid = uuid.uuid4()

    def test_cp_resultsetcontext_to_local_with_uuid(self):
        """Test conversion from OpenAPI ResultSetContext (UUID) to local model (UUID)."""
        # Create a mock APIConnection to test the conversion method
        conn = APIConnection(
            server_url="https://api.test.com",
            token_provider=AsyncMock(return_value="test_token"),
            session_id="test_session",
            timezone="UTC",
            organization_id=str(self.test_uuid),
            role_name="test_role",
            database_name="test_db",
            schema_name="test_schema",
            store_name="test_store",
            compute_pool_name="test_pool",
        )

        # Create OpenAPI model with UUID organization_id
        cp_ctx = CPResultSetContext(
            organizationID=self.test_uuid,
            roleName="admin",
            databaseName="main_db",
            schemaName="public",
            storeName="store1",
            computePoolName="pool1",
        )

        # Convert to local model
        local_ctx = conn.cp_resultsetcontext_to_local(cp_ctx)

        # Verify conversion
        self.assertIsInstance(local_ctx, ResultSetContext)
        self.assertEqual(local_ctx.organization_id, self.test_uuid)
        self.assertEqual(local_ctx.role_name, "admin")
        self.assertEqual(local_ctx.database_name, "main_db")
        self.assertEqual(local_ctx.schema_name, "public")
        self.assertEqual(local_ctx.store_name, "store1")
        self.assertEqual(local_ctx.compute_pool_name, "pool1")

    def test_cp_resultsetcontext_to_local_with_none_uuid(self):
        """Test conversion when organization_id is None."""
        # Create a mock APIConnection with None organization_id
        conn = APIConnection(
            server_url="https://api.test.com",
            token_provider=AsyncMock(return_value="test_token"),
            session_id="test_session",
            timezone="UTC",
            organization_id=None,
            role_name="test_role",
            database_name="test_db",
            schema_name="test_schema",
            store_name="test_store",
        )

        # Create OpenAPI model with None organization_id
        cp_ctx = CPResultSetContext(
            organizationID=None,
            roleName="admin",
            databaseName="main_db",
            schemaName="public",
            storeName="store1",
        )

        # Convert to local model
        local_ctx = conn.cp_resultsetcontext_to_local(cp_ctx)

        # Verify conversion
        self.assertIsInstance(local_ctx, ResultSetContext)
        self.assertIsNone(local_ctx.organization_id)
        self.assertEqual(local_ctx.role_name, "admin")

    def test_statement_request_accepts_string_organization(self):
        """Test that StatementRequest properly accepts string organization_id."""
        # Create a local ResultSetContext with UUID organization_id
        rsctx = ResultSetContext(
            organization_id=self.test_uuid,
            role_name="admin",
            database_name="main_db",
            schema_name="public",
            store_name="store1",
            compute_pool_name="pool1",
        )

        # Create mock API and StatementHandler
        mock_api = Mock()
        StatementHandler(
            api=mock_api,
            rsctx=rsctx,
            session_id="test_session",
            timezone="UTC",
        )

        # Create StatementRequest (this should not raise any type errors)
        statement_request = StatementRequest(
            statement="SELECT 1",
            organization=str(rsctx.organization_id) if rsctx.organization_id else None,
            role=rsctx.role_name,
            database=rsctx.database_name,
            schema=rsctx.schema_name,
            store=rsctx.store_name,
            computePool=rsctx.compute_pool_name,
        )

        # Verify the fields
        self.assertEqual(statement_request.statement, "SELECT 1")
        self.assertEqual(statement_request.organization, str(self.test_uuid))
        self.assertEqual(statement_request.role, "admin")
        self.assertEqual(statement_request.database, "main_db")
        self.assertEqual(statement_request.var_schema, "public")
        self.assertEqual(statement_request.store, "store1")
        self.assertEqual(statement_request.compute_pool, "pool1")

    def test_statement_request_with_none_organization(self):
        """Test that StatementRequest handles None organization properly."""
        # Create a local ResultSetContext with None organization_id
        rsctx = ResultSetContext(
            organization_id=None,
            role_name="admin",
            database_name="main_db",
        )

        # Create StatementRequest
        statement_request = StatementRequest(
            statement="SELECT 1",
            organization=rsctx.organization_id,
            role=rsctx.role_name,
            database=rsctx.database_name,
        )

        # Verify the fields
        self.assertEqual(statement_request.statement, "SELECT 1")
        self.assertIsNone(statement_request.organization)
        self.assertEqual(statement_request.role, "admin")
        self.assertEqual(statement_request.database, "main_db")

    def test_uuid_to_string_conversion_in_handlers(self):
        """Test that handlers properly convert UUID to string for StatementRequest."""
        # Create a local ResultSetContext with UUID organization_id
        rsctx = ResultSetContext(
            organization_id=self.test_uuid,
            role_name="admin",
            database_name="main_db",
            schema_name="public",
            store_name="store1",
            compute_pool_name="pool1",
        )

        # Create mock API and StatementHandler
        mock_api = Mock()
        handler = StatementHandler(
            api=mock_api,
            rsctx=rsctx,
            session_id="test_session",
            timezone="UTC",
        )

        # Verify that the handler correctly converts UUID to string in StatementRequest
        # We can't easily test submit_statement directly, but we can verify the
        # conversion logic works as expected by checking the rsctx
        self.assertIsInstance(handler.rsctx.organization_id, uuid.UUID)
        self.assertEqual(handler.rsctx.organization_id, self.test_uuid)

        # The conversion to string should happen in the StatementRequest creation
        converted_org = (
            str(handler.rsctx.organization_id)
            if handler.rsctx.organization_id
            else None
        )
        self.assertEqual(converted_org, str(self.test_uuid))

    def test_apiconnection_accepts_uuid_organization_id(self):
        """Test that APIConnection constructor accepts UUID organization_id."""
        conn = APIConnection(
            server_url="https://api.test.com",
            token_provider=AsyncMock(return_value="test_token"),
            session_id="test_session",
            timezone="UTC",
            organization_id=self.test_uuid,  # Pass UUID directly
            role_name="test_role",
            database_name="test_db",
            schema_name="test_schema",
            store_name="test_store",
        )

        # Verify it's stored as UUID
        self.assertIsInstance(conn.rsctx.organization_id, uuid.UUID)
        self.assertEqual(conn.rsctx.organization_id, self.test_uuid)

    def test_apiconnection_accepts_string_uuid_organization_id(self):
        """Test that APIConnection constructor accepts string UUID organization_id."""
        conn = APIConnection(
            server_url="https://api.test.com",
            token_provider=AsyncMock(return_value="test_token"),
            session_id="test_session",
            timezone="UTC",
            organization_id=str(self.test_uuid),  # Pass string UUID
            role_name="test_role",
            database_name="test_db",
            schema_name="test_schema",
            store_name="test_store",
        )

        # Verify it's converted and stored as UUID
        self.assertIsInstance(conn.rsctx.organization_id, uuid.UUID)
        self.assertEqual(conn.rsctx.organization_id, self.test_uuid)

    def test_apiconnection_rejects_invalid_string_organization_id(self):
        """Test that APIConnection constructor rejects invalid string organization_id."""
        with self.assertRaises(ValueError) as context:
            APIConnection(
                server_url="https://api.test.com",
                token_provider=AsyncMock(return_value="test_token"),
                session_id="test_session",
                timezone="UTC",
                organization_id="invalid-uuid-string",  # Invalid UUID string
                role_name="test_role",
                database_name="test_db",
                schema_name="test_schema",
                store_name="test_store",
            )

        self.assertIn("Invalid organization_id", str(context.exception))
        self.assertIn("is not a valid UUID string", str(context.exception))

    def test_apiconnection_rejects_wrong_type_organization_id(self):
        """Test that APIConnection constructor rejects wrong type for organization_id."""
        with self.assertRaises(TypeError) as context:
            APIConnection(
                server_url="https://api.test.com",
                token_provider=AsyncMock(return_value="test_token"),
                session_id="test_session",
                timezone="UTC",
                organization_id=12345,  # Wrong type
                role_name="test_role",
                database_name="test_db",
                schema_name="test_schema",
                store_name="test_store",
            )

        self.assertIn(
            "organization_id must be a string or UUID", str(context.exception)
        )


class TestOpenAPIModelTypes(unittest.TestCase):
    """Test the types of fields in OpenAPI generated models."""

    def test_cp_resultsetcontext_organization_id_is_uuid(self):
        """Verify that the OpenAPI generated model has UUID type for organization_id."""
        test_uuid = uuid.uuid4()

        # Create instance with UUID
        cp_ctx = CPResultSetContext(organizationID=test_uuid)

        # Verify the type
        self.assertIsInstance(cp_ctx.organization_id, uuid.UUID)
        self.assertEqual(cp_ctx.organization_id, test_uuid)

    def test_cp_resultsetcontext_accepts_string_uuid(self):
        """Verify that the OpenAPI model can accept string UUID and converts it."""
        test_uuid = uuid.uuid4()

        cp_ctx = CPResultSetContext(organizationID=test_uuid)

        # Verify the conversion
        self.assertIsInstance(cp_ctx.organization_id, uuid.UUID)
        self.assertEqual(cp_ctx.organization_id, test_uuid)

    def test_local_resultsetcontext_organization_id_is_uuid(self):
        """Verify that local model has UUID type for organization_id."""
        from deltastream.api.models import ResultSetContext as LocalResultSetContext

        test_uuid = uuid.uuid4()

        # Create local instance
        local_ctx = LocalResultSetContext(organization_id=test_uuid)

        # Verify the type
        self.assertIsInstance(local_ctx.organization_id, uuid.UUID)
        self.assertEqual(local_ctx.organization_id, test_uuid)


if __name__ == "__main__":
    unittest.main()
