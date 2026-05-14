import functools
import threading
from typing import Any
from uuid import UUID

import msgspec
import xxhash

NoneType = type(None)

str_hash = xxhash.xxh64_intdigest

# Reusable MessagePack encoder with deterministic ordering
_encoder = msgspec.msgpack.Encoder(order="deterministic")

# Thread-local storage for reusable buffers to reduce allocations
_local = threading.local()

NONE_HASH = 142709532119778


def none_hash(v: None) -> int:
    return NONE_HASH


def deterministic_hash(obj: Any) -> int:
    return get_hasher(type(obj))(obj)


@functools.cache
def get_hasher(type):
    if issubclass(type, NoneType):
        return none_hash
    if issubclass(type, int | float | bool | UUID):
        return hash
    if issubclass(type, str | bytes):
        return str_hash
    return custom_hash


def custom_hash(obj):
    buffer = _get_thread_buffer()
    _encoder.encode_into(obj, buffer)
    return str_hash(buffer)


def _get_thread_buffer():
    """Get a thread-local buffer for encoding, creating one if needed."""
    if (buffer := getattr(_local, "buffer", None)) is None:
        buffer = _local.buffer = bytearray(256)
    return buffer


class Hasher:
    """
    Incrementally compute a 64-bit hash for an arbitrary sequence
    of Python values (e.g. DB rows). Each value is first reduced
    to a stable 64-bit int via `deterministic_hash()` and that
    integer is then folded into an internal xxh64() stream.
    """

    __slots__ = "_stream"

    def __init__(self) -> None:
        self._stream = xxhash.xxh64()

    def update(self, obj: Any) -> None:
        """
        Feed *obj* into the running hash.

        `deterministic_hash()` returns a platform-independent 64-bit
        integer, so we convert that to 8 bytes (little-endian) and
        push it into the xxhash stream.
        """
        h = deterministic_hash(obj) & 0xFFFFFFFFFFFFFFFF
        self._stream.update(h.to_bytes(8, "little", signed=False))

    def digest(self) -> int:
        """Return the final 64-bit integer digest."""
        return self._stream.intdigest()
