from enum import Enum

class InterfaceError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.name = 'InterfaceError'

class AuthenticationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.name = 'AuthenticationError'

class TimeoutError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.name = 'TimeoutError'

class ServerError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.name = 'ServerError'

class ServiceUnavailableError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.name = 'ServiceUnavailableError'

class SQLError(Exception):
    def __init__(self, message: str, code: str, statement_id: str):
        super().__init__(message)
        self.name = 'SQLError'
        self.code = SqlState(code)
        self.statement_id = statement_id

class SqlState(str, Enum):
    # Base SQL States
    SQL_STATE_00000 = '00000'
    SQL_STATE_01000 = '01000'
    SQL_STATE_01004 = '01004'
    SQL_STATE_01006 = '01006'
    SQL_STATE_01007 = '01007'
    SQL_STATE_01P01 = '01P01'
    SQL_STATE_02000 = '02000'
    SQL_STATE_03000 = '03000'
    SQL_STATE_0A000 = '0A000'
    SQL_STATE_0L000 = '0L000'
    SQL_STATE_0LP01 = '0LP01'
    SQL_STATE_2BP01 = '2BP01'
    SQL_STATE_3D000 = '3D000'
    SQL_STATE_3D001 = '3D001'
    SQL_STATE_3D002 = '3D002'
    SQL_STATE_3D003 = '3D003'
    SQL_STATE_3D004 = '3D004'
    SQL_STATE_3D005 = '3D005'
    SQL_STATE_3D006 = '3D006'
    SQL_STATE_3D007 = '3D007'
    SQL_STATE_3D008 = '3D008'
    SQL_STATE_3D009 = '3D009'
    SQL_STATE_3D010 = '3D010'
    SQL_STATE_3D011 = '3D011'
    SQL_STATE_3E001 = '3E001'
    SQL_STATE_3E002 = '3E002'
    SQL_STATE_3E003 = '3E003'
    SQL_STATE_42501 = '42501'
    SQL_STATE_42601 = '42601'
    SQL_STATE_42622 = '42622'
    SQL_STATE_42710 = '42710'
    SQL_STATE_42P04 = '42P04'
    SQL_STATE_42P05 = '42P05'
    SQL_STATE_42P06 = '42P06'
    SQL_STATE_42P07 = '42P07'
    SQL_STATE_42P08 = '42P08'
    SQL_STATE_42P001 = '42P001'
    SQL_STATE_42P002 = '42P002'
    SQL_STATE_57014 = '57014'
    SQL_STATE_57015 = '57015'
    SQL_STATE_57000 = '57000'
    SQL_STATE_53000 = '53000'
    SQL_STATE_XX000 = 'XX000'
    SQL_STATE_XX001 = 'XX001'

    # Class 00 — Successful Completion
    SQL_STATE_SUCCESSFUL_COMPLETION = SQL_STATE_00000

    # Class 01 — Warning
    SQL_STATE_WARNING = SQL_STATE_01000
    SQL_STATE_PRIVILEGE_NOT_GRANTED = SQL_STATE_01007
    SQL_STATE_PRIVILEGE_NOT_REVOKED = SQL_STATE_01006
    SQL_STATE_STRING_DATA_RIGHT_TRUNCATION = SQL_STATE_01004
    SQL_STATE_DEPRECATED_FEATURE = SQL_STATE_01P01

    # Class 02 — No Data
    SQL_STATE_NO_DATA = SQL_STATE_02000

    # Class 03 — SQL Statement Not Yet Complete
    SQL_STATE_SQL_STATEMENT_NOT_YET_COMPLETE = SQL_STATE_03000

    # Class 0A — Feature Not Supported
    SQL_STATE_FEATURE_NOT_SUPPORTED = SQL_STATE_0A000

    # Class 0L — Invalid Grantor
    SQL_STATE_INVALID_GRANTOR = SQL_STATE_0L000
    SQL_STATE_INVALID_GRANT_OPERATION = SQL_STATE_0LP01

    # Class 2B — Dependent Objects Still Exist
    SQL_STATE_DEPENDENT_OBJECTS_STILL_EXIST = SQL_STATE_2BP01

    # Class 3D — Invalid Objects (not found errors)
    SQL_STATE_INVALID_USER = SQL_STATE_3D000
    SQL_STATE_INVALID_ROLE = SQL_STATE_3D001
    SQL_STATE_INVALID_DATABASE = SQL_STATE_3D002
    SQL_STATE_INVALID_SCHEMA = SQL_STATE_3D003
    SQL_STATE_INVALID_ORGANIZATION = SQL_STATE_3D004
    SQL_STATE_INVALID_REGION = SQL_STATE_3D005
    SQL_STATE_INVALID_STORE = SQL_STATE_3D006
    SQL_STATE_INVALID_TOPIC = SQL_STATE_3D007
    SQL_STATE_INVALID_PARAMETER = SQL_STATE_3D008
    SQL_STATE_INVALID_SCHEMA_REGISTRY = SQL_STATE_3D009
    SQL_STATE_INVALID_DESCRIPTOR = SQL_STATE_3D010
    SQL_STATE_INVALID_DESCRIPTOR_SOURCE = SQL_STATE_3D011

    # Class 3E — Resource not ready
    SQL_STATE_STORE_NOT_READY = SQL_STATE_3E001
    SQL_STATE_SCHEMA_REGISTRY_NOT_READY = SQL_STATE_3E002
    SQL_STATE_RELATION_NOT_READY = SQL_STATE_3E003

    # Class 42 — Syntax Error or Access Rule Violation
    SQL_STATE_INSUFFICIENT_PRIVILEGE = SQL_STATE_42501
    SQL_STATE_SYNTAX_ERROR = SQL_STATE_42601
    SQL_STATE_NAME_TOO_LONG = SQL_STATE_42622
    SQL_STATE_DUPLICATE_OBJECT = SQL_STATE_42710
    SQL_STATE_DUPLICATE_DATABASE = SQL_STATE_42P04
    SQL_STATE_DUPLICATE_STORE = SQL_STATE_42P05
    SQL_STATE_DUPLICATE_SCHEMA = SQL_STATE_42P06
    SQL_STATE_DUPLICATE_USER = SQL_STATE_42P07
    SQL_STATE_DUPLICATE_TOPIC_DESCRIPTOR = SQL_STATE_42P08
    SQL_STATE_AMBIGUOUS_ORGANIZATION = SQL_STATE_42P001
    SQL_STATE_AMBIGUOUS_STORE = SQL_STATE_42P002

    # Class 53 — Insufficient Resources
    SQL_STATE_CONFIGURATION_LIMIT_EXCEEDED = SQL_STATE_53000

    # Class XX — Internal Error
    SQL_STATE_INTERNAL_ERROR = SQL_STATE_XX000
    SQL_STATE_UNDEFINED = SQL_STATE_XX001

    # Class 57 — Operator Intervention
    SQL_STATE_CANCELLED = SQL_STATE_57000
    SQL_STATE_TIMEOUT = SQL_STATE_57014
    SQL_STATE_REMOTE_UNAVAILABLE = SQL_STATE_57015