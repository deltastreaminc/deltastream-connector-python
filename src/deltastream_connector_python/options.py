# SPDX-FileCopyrightText: 2023-present DeltaStream Inc. <support@deltastream.io>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Optional
from pydantic import BaseModel, StrictStr


class Options(BaseModel):
    session_id: Optional[StrictStr] = None
    timezone: Optional[StrictStr] = None
    debug: bool = False
    insecure_skip_verify: bool = False

    def __init__(self, session_id: Optional[StrictStr] = None, timezone: Optional[StrictStr] = None, debug: bool = False, insecure_skip_verify: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.session_id = session_id
        self.timezone = timezone
        self.debug = debug
        self.insecure_skip_verify = insecure_skip_verify
