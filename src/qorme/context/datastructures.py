from datetime import datetime
from uuid import UUID

import msgspec

from .types import ContextType


class ContextData(msgspec.Struct, omit_defaults=True):
    uid: UUID
    name: str
    type: ContextType
    timestamp: datetime
    data: dict[str, str]
    parent_ts: datetime | None = None
    parent_uid: UUID | None = None
