import unittest

from qorme.utils.bitset import BitSet


class TestBitSet(unittest.TestCase):
    def test_initially_empty(self):
        bs = BitSet()
        self.assertEqual(bs.length(), 0)
        self.assertEqual(bs.list(), [])

    def test_set_and_has_and_length(self):
        bs = BitSet()
        bs.set(10)
        self.assertTrue(bs.has(10))
        self.assertEqual(bs.length(), 1)
        bs.set(10)
        self.assertEqual(bs.length(), 1)

    def test_clear(self):
        bs = BitSet()
        bs.set(5)
        self.assertTrue(bs.has(5))
        bs.clear(5)
        self.assertFalse(bs.has(5))
        self.assertEqual(bs.length(), 0)

    def test_list_and_length(self):
        bs = BitSet()
        items = [0, 2, 5, 63]
        for el in items:
            bs.set(el)
        self.assertEqual(bs.length(), 4)
        self.assertEqual(bs.list(), items)

    def test_out_of_bounds_behavior(self):
        bs = BitSet()
        bs.set(64)
        self.assertTrue(bs.has(64))
        # Value wraps around
        self.assertEqual(bs.list(), [0])
        bs.clear(64)
        self.assertFalse(bs.has(64))

    def test_multiple_bits(self):
        bs = BitSet()
        for i in range(64):
            if i % 2 == 0:
                bs.set(i)
        self.assertEqual(bs.length(), 32)
        evens = list(range(0, 64, 2))
        self.assertEqual(bs.list(), evens)

    def test_int(self):
        bs = BitSet()
        expected = 0
        for i in range(0, 64, 8):
            bs.set(i)
            expected |= 1 << i

        self.assertEqual(bs.int(), expected)
