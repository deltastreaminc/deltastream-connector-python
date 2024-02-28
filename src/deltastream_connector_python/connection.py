# SPDX-FileCopyrightText: 2023-present DeltaStream Inc. <support@deltastream.io>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Optional, ClassVar  # pylint: disable=unused-import
from pydantic import BaseModel, StrictStr


from .options import Options
from .cursor import Cursor
from .exceptions import Warning, Error, InterfaceError, DatabaseError
from .exceptions import OperationalError, IntegrityError, InternalError
from .exceptions import ProgrammingError, NotSupportedError


def connect(endpoint: Optional[str] = None, token: str = None, options: Options = Options(), **kwargs):
    pass
    return Connection(endpoint=endpoint, token=token, options=options, **kwargs)


class Connection(BaseModel):
    Warning: ClassVar[Warning] = Warning
    Error: ClassVar[Error] = Error
    InterfaceError: ClassVar[InterfaceError] = InterfaceError
    DatabaseError: ClassVar[DatabaseError] = DatabaseError
    OperationalError: ClassVar[OperationalError] = OperationalError
    IntegrityError: ClassVar[IntegrityError] = IntegrityError
    InternalError: ClassVar[InternalError] = InternalError
    ProgrammingError: ClassVar[ProgrammingError] = ProgrammingError
    NotSupportedError: ClassVar[NotSupportedError] = NotSupportedError

    _open: bool = True

    _endpoint: StrictStr
    _token: StrictStr
    _options: Options

    def __init__(self, endpoint: Optional[StrictStr] = None, token: StrictStr = None, options: Options = Options(), **kwargs):
        super().__init__(**kwargs)
        self._options = options

        if token is None:
            raise InterfaceError('no API token provided')
        self._token = token

        if endpoint is None:
            self._endpoint = 'https://api.deltastream.io/v2'
        else:
            self._endpoint = endpoint

        # config = Configuration(
        #     host=self._endpoint,
        #     access_token=self._token
        # )
        # config.debug = options.debug
        # self._client = DefaultApi(api_client=ApiClient(configuration=config))

    def close(self) -> None:
        self._check_closed()
        self._open = False
        return

    def commit(self) -> None:
        self._check_closed()
        raise NotSupportedError('transactions are not supported')

    def rollback(self) -> None:
        self._check_closed()
        raise NotSupportedError('transactions are not supported')

    def _check_closed(self):
        if not self._open:
            raise InterfaceError('connection is closed')
        return

    def cursor(self):
        self._check_closed()
        return Cursor(self._endpoint, self._token, self._options)
