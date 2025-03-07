from typing import List, Optional, Callable, Awaitable, Dict
from urllib.parse import urlparse, parse_qs
from .blob import Blob
from .error import AuthenticationError
from deltastream.api.controlplane.openapi_client.api import DeltastreamApi
from deltastream.api.controlplane.openapi_client.api_client import ApiClient
from deltastream.api.controlplane.openapi_client.exceptions import ApiException
from .streaming_rows import StreamingRows
from .resultset_rows import ResultsetRows
from .dpconn import DPAPIConnection
from .models import ResultSetContext, ResultSet, Rows
from .handlers import StatementHandler, map_error_response
from deltastream.api.controlplane.openapi_client.configuration import Configuration

class APIConnection:
    def __init__(self, 
                 server_url: str, 
                 token_provider: Callable[[], Awaitable[str]], 
                 session_id: Optional[str], 
                 timezone: str, 
                 organization_id: Optional[str], 
                 role_name: Optional[str], 
                 database_name: Optional[str], 
                 schema_name: Optional[str], 
                 store_name: Optional[str]):
        self.catalog: Optional[str] = None
        self.server_url = server_url
        self.session_id = session_id
        self.timezone = timezone
        self.rsctx = ResultSetContext(
            organization_id=organization_id,
            role_name=role_name,
            database_name=database_name,
            schema_name=schema_name,
            store_name=store_name
        )
        self.token_provider = token_provider
        self.statement_handler = StatementHandler(self._create_api(), self.rsctx, self.session_id, self.timezone)

    @staticmethod
    def from_dsn(dsn: str, token_provider: Optional[Callable[[], Awaitable[str]]] = None):
        url = urlparse(dsn)
        query_params = parse_qs(url.query)
        
        if not token_provider:
            if not url.password:
                raise AuthenticationError("Invalid DSN: missing token")
            async def token_provider() -> str:
                return url.password  or ""
        
        server_url = f"{url.scheme}://{url.hostname}{url.path}"
        session_id = query_params.get('sessionID', [None])[0] or ""  # Ensure string
        timezone = query_params.get('timezone', ['UTC'])[0]
        organization_id = query_params.get('organizationID', [None])[0]
        role_name = query_params.get('roleName', [None])[0]
        database_name = query_params.get('databaseName', [None])[0]
        schema_name = query_params.get('schemaName', [None])[0]
        store_name = query_params.get('storeName', [None])[0]
        
        return APIConnection(server_url, token_provider, session_id, timezone, organization_id, role_name, database_name, schema_name, store_name)

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
        self.statement_handler.api.api_client.default_headers['Authorization'] = f'Bearer {token}'

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
                    base_uri,
                    dp_req.token,
                    self.timezone,
                    self.session_id
                )
                
                if dp_req.request_type == 'result-set':
                    dp_rs = await dpconn.get_statement_status(dp_req.statement_id, 0)
                    return ResultsetRows(dpconn.get_statement_status, dp_rs)
                
                rows = StreamingRows(dpconn, dp_req)
                await rows.open()
                return rows
                
            if rs.metadata.context:
                self._update_context(rs.metadata.context)
            
            return ResultsetRows(self.statement_handler.get_statement_status, rs)
        except ApiException as err:
            map_error_response(err)
            raise

    async def submit_statement(
        self, 
        query: str, 
        attachments: Optional[List[Blob]] = None
    ) -> ResultSet:
        try:
            await self._set_auth_header()
            return await self.statement_handler.submit_statement(query, attachments)
        except ApiException as err:
            map_error_response(err)
            raise

    async def get_statement_status(
        self, 
        statement_id: str, 
        partition_id: int
    ) -> ResultSet:
        try:
            await self._set_auth_header()
            return await self.statement_handler.get_statement_status(statement_id, partition_id)
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
                "patch": version_response.patch
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

    def get_catalog_name(self) -> str:
        return self.catalog if self.catalog else ""

def create_connection(
    dsn: str,
    token_provider: Optional[Callable[[], Awaitable[str]]] = None
) -> APIConnection:
    raise NotImplementedError("Concrete implementation should be provided by specific provider")