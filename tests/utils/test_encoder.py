import unittest

import msgspec

from qorme.utils.bitset import BitSet
from qorme.utils.encoder import new_encoder


class TestEncoder(unittest.TestCase):
    def test_bitset_encoding(self):
        bitset = BitSet()
        bitset.set(2)
        data = {"key": [1, 2, 3], "bs": bitset}
        msg = new_encoder().encode(data)
        self.assertEqual(msgspec.msgpack.decode(msg), {"bs": 4, "key": [1, 2, 3]})
