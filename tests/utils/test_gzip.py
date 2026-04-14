import gzip
import unittest

from qorme.utils.gzip import GzipCompressor


class TestGzipCompressor(unittest.TestCase):
    def test_roundtrip(self):
        data = bytearray()
        for level in range(4):
            compressor = GzipCompressor(level=level)
            data += b"hello world" * level

            compressed = compressor.compress(data)
            decompressed = gzip.decompress(compressed)

            self.assertEqual(decompressed, data)
