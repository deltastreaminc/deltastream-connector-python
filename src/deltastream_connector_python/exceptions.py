# SPDX-FileCopyrightText: 2023-present DeltaStream Inc. <support@deltastream.io>
#
# SPDX-License-Identifier: Apache-2.0


class Error(Exception):
    pass


class Warning(Exception):
    pass


class InterfaceError(Error):
    pass


class DatabaseError(Error):
    pass


class InternalError(DatabaseError):
    pass


class OperationalError(DatabaseError):
    pass


class ProgrammingError(DatabaseError):
    pass


class IntegrityError(DatabaseError):
    pass


class DataError(DatabaseError):
    pass


class NotSupportedError(DatabaseError):
    pass
