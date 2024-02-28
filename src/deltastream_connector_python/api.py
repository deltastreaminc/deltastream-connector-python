import requests
import logging
import time
from typing import Sequence, Any, Mapping
from pydantic import StrictStr
import http.client as http_client

from openapi_client.models import StatementRequest, StatementRequestParameters, ResultSetContext, StatementStatus, ResultSet
from openapi_client.exceptions import ApiException, BadRequestException, UnauthorizedException, ForbiddenException, NotFoundException, ServiceException
from openapi_client.api import DefaultApi
from openapi_client import ApiClient, Configuration

from .options import Options
from .exceptions import DatabaseError, InterfaceError, InternalError

Parameters = Sequence[Any] | Mapping[str, Any]


def get_resultset_with_op(operation: str, parameters: Parameters, context: ResultSetContext, endpoint: StrictStr, token: StrictStr, options: Options) -> ResultSet:
    statement = operation.format(parameters)
    request = StatementRequest(
        statement=statement,
        organization=context.organization_id,
        role=context.role_name,
        database=context.database_name,
        schema=context.schema_name,
        store=context.store_name,
        parameters=StatementRequestParameters(sessionID=options.session_id, timezone=options.timezone),
    )
    attachments = []
    try:
        rs = submit_statement(endpoint, token, options, request, attachments)
        match rs.sql_state:
            case '00000':  # SqlStateSuccessfulCompletion
                return rs
            case '03000':  # SqlStateSqlStatementNotYetComplete
                return get_resultset_with_statement_id(rs.statement_id, 0, endpoint, token, options)
            case _:
                raise DatabaseError('sql state: ' + rs.sql_state)
    except Exception as e:
        map_api_error_to_db_error(e)


def get_resultset_with_statement_id(statement_id: str, partition_id: int, endpoint: StrictStr, token: StrictStr, options: Options) -> ResultSet:
    conf = Configuration(access_token=token, host=endpoint)
    conf.debug = options.debug
    api_client = ApiClient(configuration=conf)
    api = DefaultApi(api_client)
    timeout = time.time() + 60
    while True:
        if time.time() > timeout:
            raise TimeoutError('unable to complete request')

        try:
            rs = api.get_statement_status(statement_id, options.session_id, partition_id)
            match rs.sql_state:
                case '00000':  # SqlStateSuccessfulCompletion
                    return rs
                case '03000':  # SqlStateSqlStatementNotYetComplete
                    # sleep and retry
                    time.sleep(1)
                case _:
                    raise DatabaseError('sql state: ' + rs.sql_state)
        except Exception as e:
            map_api_error_to_db_error(e)


def map_api_error_to_db_error(err):
    try:
        raise err
    except BadRequestException as e:
        raise InternalError(str(e))
    except UnauthorizedException as e:
        raise DatabaseError('invalid token: ' + str(e))
    except ForbiddenException as e:
        raise DatabaseError('invalid token: ' + str(e))
    except NotFoundException as e:
        raise InterfaceError('api endpoint is invalid: ' + str(e))
    except ServiceException as e:
        raise InternalError(str(e))
    except ApiException as e:
        raise InterfaceError('unexpected error: ' + str(e))
    except Exception:
        raise err


def submit_statement(endpoint: StrictStr, token: StrictStr, options: Options, request: StatementRequest, attachments: Any) -> StatementStatus | ResultSet:
    if options.debug:
        http_client.HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger('requests.packages.urllib3')
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    files = [('request', ('', request.to_json(), 'application/json'))]
    resp = requests.post(url=endpoint + '/statements', headers={'Authorization': 'Bearer ' + token}, files=files)
    match resp.status_code:
        case 200:
            return ResultSet.from_json(resp.text)
        case 202:
            return StatementStatus.from_json(resp.text)
        case _:
            resp.status = resp.status_code
            ApiException.from_response(http_resp=resp, body=resp.text, data=None)
