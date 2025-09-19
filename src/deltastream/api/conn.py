from typing import List, Optional, Callable, Awaitable, Dict, Union
from urllib.parse import urlparse, parse_qs
import os
import mimetypes
from .blob import Blob
from .error import AuthenticationError
from deltastream.api.controlplane.openapi_client.api import DeltastreamApi
from deltastream.api.controlplane.openapi_client.api_client import ApiClient
from deltastream.api.controlplane.openapi_client.exceptions import ApiException
from .streaming_rows import StreamingRows
from .resultset_rows import ResultsetRows
from .dpconn import DPAPIConnection
from .models import (
    ResultSetContext,
    ResultSet,
    Rows,
    ResultSetMetadata,
    DataplaneRequest,
)
from deltastream.api.controlplane.openapi_client.models.result_set import (
    ResultSet as CPResultSet,
)
from .handlers import StatementHandler, map_error_response
from deltastream.api.controlplane.openapi_client.configuration import Configuration
from uuid import UUID


class APIConnection:
    def __init__(
        self,
        server_url: str,
        token_provider: Callable[[], Awaitable[str]],
        session_id: Optional[str],
        timezone: str,
        organization_id: Optional[Union[str, UUID]],
        role_name: Optional[str],
        database_name: Optional[str],
        schema_name: Optional[str],
        store_name: Optional[str],
        compute_pool_name: Optional[str] = None,
    ):
        self.catalog: Optional[str] = None
        self.server_url = server_url
        self.session_id = session_id
        self.timezone = timezone
        # Convert to UUID if provided and valid
        org_uuid = None
        if organization_id is not None:
            if isinstance(organization_id, UUID):
                org_uuid = organization_id
            elif isinstance(organization_id, str):
                try:
                    org_uuid = UUID(organization_id)
                except ValueError as e:
                    raise ValueError(
                        f"Invalid organization_id: '{organization_id}' is not a valid UUID string"
                    ) from e
            else:
                raise TypeError(
                    f"organization_id must be a string or UUID, got {type(organization_id)}"
                )
        self.rsctx = ResultSetContext(
            organization_id=org_uuid,
            role_name=role_name,
            database_name=database_name,
            schema_name=schema_name,
            store_name=store_name,
            compute_pool_name=compute_pool_name,
        )
        self.token_provider = token_provider
        self.statement_handler = StatementHandler(
            self._create_api(), self.rsctx, self.session_id, self.timezone
        )

    @staticmethod
    def from_dsn(
        dsn: str, token_provider: Optional[Callable[[], Awaitable[str]]] = None
    ):
        url = urlparse(dsn)
        query_params = parse_qs(url.query)

        if not token_provider:
            if not url.password:
                raise AuthenticationError("Invalid DSN: missing token")

            async def token_provider() -> str:
                return url.password or ""

        server_url = f"{url.scheme}://{url.hostname}{url.path}"
        session_id = query_params.get("sessionID", [None])[0] or ""  # Ensure string
        timezone = query_params.get("timezone", ["UTC"])[0]
        organization_id = query_params.get("organizationID", [None])[0]
        role_name = query_params.get("roleName", [None])[0]
        database_name = query_params.get("databaseName", [None])[0]
        schema_name = query_params.get("schemaName", [None])[0]
        store_name = query_params.get("storeName", [None])[0]
        compute_pool_name = query_params.get("computePoolName", [None])[0]

        return APIConnection(
            server_url,
            token_provider,
            session_id,
            timezone,
            organization_id,
            role_name,
            database_name,
            schema_name,
            store_name,
            compute_pool_name,
        )

    def _create_config(self):
        config = Configuration()
        config.host = self.server_url
        return config

    def _create_api(self):
        config = self._create_config()
        api_client = ApiClient(config)
        return DeltastreamApi(api_client)

    async def _set_auth_header(self):
        token = await self.token_provider()
        self.statement_handler.api.api_client.configuration.access_token = token
        self.statement_handler.api.api_client.default_headers["Authorization"] = (
            f"Bearer {token}"
        )

    async def exec(self, query: str, attachments: Optional[List[Blob]] = None) -> None:
        try:
            await self._set_auth_header()
            rs = await self.submit_statement(query, attachments)
            if rs.metadata.context:
                new_ctx = rs.metadata.context
                if new_ctx.organization_id:
                    self.rsctx.organization_id = new_ctx.organization_id
                if new_ctx.role_name:
                    self.rsctx.role_name = new_ctx.role_name
                if new_ctx.database_name:
                    self.rsctx.database_name = new_ctx.database_name
                if new_ctx.schema_name:
                    self.rsctx.schema_name = new_ctx.schema_name
                if new_ctx.store_name:
                    self.rsctx.store_name = new_ctx.store_name
                if hasattr(new_ctx, "compute_pool_name") and new_ctx.compute_pool_name:
                    self.rsctx.compute_pool_name = new_ctx.compute_pool_name
            return None
        except ApiException as err:
            map_error_response(err)
            raise

    async def query(self, query: str, attachments: Optional[List[Blob]] = None) -> Rows:
        try:
            await self._set_auth_header()
            rs = await self.submit_statement(query, attachments)
            if rs.metadata.dataplane_request:
                dp_req = rs.metadata.dataplane_request
                base_uri = dp_req.uri.replace(f"/statements/{dp_req.statement_id}", "")

                dpconn = DPAPIConnection(
                    base_uri, dp_req.token, self.timezone, self.session_id
                )

                if dp_req.request_type == "result-set":
                    dp_rs = await dpconn.get_statement_status(
                        UUID(dp_req.statement_id), 0
                    )
                    cp_rs = self._dataplane_to_controlplane_resultset(dp_rs)

                    async def cp_get_statement_status(
                        statement_id: UUID, partition_id: int
                    ) -> CPResultSet:
                        dp_result = await dpconn.get_statement_status(
                            statement_id, partition_id
                        )
                        return self._dataplane_to_controlplane_resultset(dp_result)

                    return ResultsetRows(cp_get_statement_status, cp_rs)

                rows = StreamingRows(dpconn, self.cp_dataplanerequest_to_local(dp_req))
                await rows.open()
                return rows

            if rs.metadata.context:
                self._update_context(
                    self.cp_resultsetcontext_to_local(rs.metadata.context)
                )
            cp_rs = self._dataplane_to_controlplane_resultset(rs)

            async def cp_get_statement_status(
                statement_id: UUID, partition_id: int
            ) -> CPResultSet:
                result = await self.statement_handler.get_statement_status(
                    statement_id, partition_id
                )
                return self._dataplane_to_controlplane_resultset(result)

            return ResultsetRows(cp_get_statement_status, cp_rs)

        except ApiException as err:
            map_error_response(err)
            raise

    async def exec_with_files(
        self, query: str, file_paths: Optional[List[Union[str, Dict[str, str]]]] = None
    ) -> None:
        """Execute a query with file attachments using file paths.

        Args:
            query: The SQL query to execute
            file_paths: List of file paths or dictionaries with file configuration.
                       Can be:
                       - List of strings: file paths (filename will be auto-detected)
                       - List of dicts with keys: 'path', 'name' (optional), 'content_type' (optional)

        Example:
            # Simple file paths
            await conn.exec_with_files(
                "CREATE FUNCTION_SOURCE \"my_func\" WITH ('file' = 'my_jar.jar');",
                ["/path/to/my_jar.jar"]
            )

            # With custom names and content types
            await conn.exec_with_files(
                "CREATE FUNCTION_SOURCE \"my_func\" WITH ('file' = 'custom_name.jar');",
                [{"path": "/path/to/file.jar", "name": "custom_name.jar", "content_type": "application/java-archive"}]
            )
        """
        attachments = None
        if file_paths is not None:
            attachments = []
            for file_config in file_paths:
                if isinstance(file_config, str):
                    # Simple file path
                    file_path = file_config
                    file_name = os.path.basename(file_path)
                    content_type = mimetypes.guess_type(file_path)[0]
                elif isinstance(file_config, dict):
                    # Dictionary with configuration
                    file_path = file_config["path"]
                    file_name = file_config.get("name", os.path.basename(file_path))
                    content_type = file_config.get(
                        "content_type", mimetypes.guess_type(file_path)[0]
                    )
                else:
                    raise ValueError("file_paths must contain strings or dictionaries")

                # Read file and create blob
                with open(file_path, "rb") as f:
                    data = f.read()

                blob = Blob.from_bytes(data, name=file_name, content_type=content_type)
                attachments.append(blob)

        await self.exec(query, attachments)

    async def query_with_files(
        self, query: str, file_paths: Optional[List[Union[str, Dict[str, str]]]] = None
    ) -> Rows:
        """Execute a query with file attachments using file paths and return results.

        Args:
            query: The SQL query to execute
            file_paths: List of file paths or dictionaries with file configuration.
                       Can be:
                       - List of strings: file paths (filename will be auto-detected)
                       - List of dicts with keys: 'path', 'name' (optional), 'content_type' (optional)

        Returns:
            Rows object for iterating through results

        Example:
            # Simple file paths
            rows = await conn.query_with_files(
                "CREATE FUNCTION_SOURCE \"my_func\" WITH ('file' = 'my_jar.jar');",
                ["/path/to/my_jar.jar"]
            )

            # With custom names and content types
            rows = await conn.query_with_files(
                "CREATE FUNCTION_SOURCE \"my_func\" WITH ('file' = 'custom_name.jar');",
                [{"path": "/path/to/file.jar", "name": "custom_name.jar", "content_type": "application/java-archive"}]
            )
        """
        attachments = None
        if file_paths is not None:
            attachments = []
            for file_config in file_paths:
                if isinstance(file_config, str):
                    # Simple file path
                    file_path = file_config
                    file_name = os.path.basename(file_path)
                    content_type = mimetypes.guess_type(file_path)[0]
                elif isinstance(file_config, dict):
                    # Dictionary with configuration
                    file_path = file_config["path"]
                    file_name = file_config.get("name", os.path.basename(file_path))
                    content_type = file_config.get(
                        "content_type", mimetypes.guess_type(file_path)[0]
                    )
                else:
                    raise ValueError("file_paths must contain strings or dictionaries")

                # Read file and create blob
                with open(file_path, "rb") as f:
                    data = f.read()

                blob = Blob.from_bytes(data, name=file_name, content_type=content_type)
                attachments.append(blob)

        return await self.query(query, attachments)

    @staticmethod
    def _dataplane_to_controlplane_resultset(dp_rs) -> CPResultSet:
        # Import controlplane models here to avoid circular imports
        from deltastream.api.controlplane.openapi_client.models.result_set import (
            ResultSet as CPResultSet,
        )
        from deltastream.api.controlplane.openapi_client.models.result_set_metadata import (
            ResultSetMetadata as CPResultSetMetadata,
        )

        # This assumes dp_rs has dict() method; adjust as needed for your dataclass
        meta = dp_rs.metadata
        cp_meta = CPResultSetMetadata(
            encoding=getattr(meta, "encoding", ""),
            partitionInfo=getattr(meta, "partition_info", None),
            columns=getattr(meta, "columns", []),
            dataplaneRequest=getattr(meta, "dataplane_request", None),
            context=getattr(meta, "context", None),
        )
        return CPResultSet(
            sqlState=dp_rs.sql_state,
            message=dp_rs.message,
            statementID=dp_rs.statement_id,
            createdOn=getattr(dp_rs, "created_on", 0),
            metadata=cp_meta,
            data=getattr(dp_rs, "data", None),
        )

    async def submit_statement(
        self, query: str, attachments: Optional[List[Blob]] = None
    ) -> CPResultSet:
        try:
            await self._set_auth_header()
            return await self.statement_handler.submit_statement(query, attachments)
        except ApiException as err:
            map_error_response(err)
            raise

    async def get_statement_status(
        self, statement_id: UUID, partition_id: int
    ) -> CPResultSet:
        try:
            await self._set_auth_header()
            return await self.statement_handler.get_statement_status(
                statement_id, partition_id
            )
        except ApiException as err:
            map_error_response(err)
            raise

    async def version(self) -> Dict[str, int]:
        try:
            await self._set_auth_header()
            version_response = self.statement_handler.api.get_version()
            return {
                "major": version_response.major,
                "minor": version_response.minor,
                "patch": version_response.patch,
            }
        except ApiException as err:
            map_error_response(err)
            raise

    def _update_context(self, new_ctx: ResultSetContext) -> None:
        if new_ctx.organization_id:
            self.rsctx.organization_id = new_ctx.organization_id
        if new_ctx.role_name:
            self.rsctx.role_name = new_ctx.role_name
        if new_ctx.database_name:
            self.rsctx.database_name = new_ctx.database_name
        if new_ctx.schema_name:
            self.rsctx.schema_name = new_ctx.schema_name
        if new_ctx.store_name:
            self.rsctx.store_name = new_ctx.store_name
        if hasattr(new_ctx, "compute_pool_name") and new_ctx.compute_pool_name:
            self.rsctx.compute_pool_name = new_ctx.compute_pool_name

    def get_catalog_name(self) -> str:
        return self.catalog if self.catalog else ""

    # --- Conversion helpers ---
    def cp_resultset_to_local(self, cp_rs) -> ResultSet:
        meta = cp_rs.metadata
        local_meta = ResultSetMetadata(
            context=self.cp_resultsetcontext_to_local(meta.context)
            if meta.context
            else None,
            dataplane_request=self.cp_dataplanerequest_to_local(meta.dataplaneRequest)
            if getattr(meta, "dataplaneRequest", None)
            else None,
        )
        return ResultSet(
            statement_id=cp_rs.statementID,
            sql_state=cp_rs.sqlState,
            message=cp_rs.message,
            metadata=local_meta,
        )

    def cp_dataplanerequest_to_local(self, cp_dp) -> DataplaneRequest:
        return DataplaneRequest(
            uri=cp_dp.uri,
            statement_id=cp_dp.statement_id,
            token=cp_dp.token,
            request_type=cp_dp.request_type,
        )

    def cp_resultsetcontext_to_local(self, cp_ctx) -> ResultSetContext:
        return ResultSetContext(
            organization_id=cp_ctx.organization_id,
            role_name=cp_ctx.role_name,
            database_name=cp_ctx.database_name,
            schema_name=cp_ctx.schema_name,
            store_name=cp_ctx.store_name,
            compute_pool_name=cp_ctx.compute_pool_name,
        )


def create_connection(
    dsn: str, token_provider: Optional[Callable[[], Awaitable[str]]] = None
) -> APIConnection:
    raise NotImplementedError(
        "Concrete implementation should be provided by specific provider"
    )
