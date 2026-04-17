from datetime import datetime
from uuid import UUID

import msgspec

from .types import ContextType


class ContextData(msgspec.Struct, omit_defaults=True):
    """
    Holds data about a context, which represents a logical operation in the application.
    Each context has a unique identifier (uid), a name, a type, a timestamp,
    and optional parent context information (parent_ts and parent_uid).
    The data field can hold additional key-value pairs relevant to the context.
    """

    uid: UUID
    name: str
    type: ContextType
    timestamp: datetime
    data: dict[str, str]
    parent_ts: datetime | None = None
    parent_uid: UUID | None = None
