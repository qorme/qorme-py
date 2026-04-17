from typing import Any

import msgspec

from qorme.utils.bitset import BitSet


def enc_hook(obj: Any) -> Any:
    if isinstance(obj, BitSet):
        return obj.int()
    raise NotImplementedError(f"Objects of type {type(obj)} are not supported")


def new_encoder() -> msgspec.msgpack.Encoder:
    return msgspec.msgpack.Encoder(enc_hook=enc_hook)
