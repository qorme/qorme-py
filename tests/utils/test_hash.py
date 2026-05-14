import datetime
import unittest
import uuid

from qorme.utils.hash import NONE_HASH, Hasher, deterministic_hash


class TestDeterministicHash(unittest.TestCase):
    def test_none_and_empty_values(self):
        for value, expected in [
            (None, NONE_HASH),
            ("", 17241709254077376921),
            (b"", 17241709254077376921),
            ([], 6864306351248909839),
            ({}, 9516710917713200287),
            ((), 6864306351248909839),
        ]:
            self.assertEqual(deterministic_hash(value), expected)

    def test_simple_types(self):
        for value, expected in [
            (42, 42),
            (3.14, 322818021289917443),
            (True, 1),
            (False, 0),
        ]:
            self.assertEqual(deterministic_hash(value), expected)

    def test_string(self):
        for s, expected in [
            ("", 17241709254077376921),
            ("hello", 2794345569481354659),
            ("world", 16679358290033791471),
            ("unicode: 世界 🚀", 10106186320699614812),
        ]:
            self.assertEqual(deterministic_hash(s), expected)

    def test_bytes(self):
        for b, expected in [
            (b"binary data", 11977462163197767574),
            (b"", 17241709254077376921),
            (b"\x00\x01\x02", 16557408460946040285),
        ]:
            self.assertEqual(deterministic_hash(b), expected)

    def test_uuid(self):
        uuid_obj = uuid.UUID("12345678-1234-5678-1234-123456789abc")
        self.assertEqual(deterministic_hash(uuid_obj), 276626082786659969)

    def test_datetime(self):
        for value, expected in [
            (datetime.datetime(2024, 1, 15, 10, 30), 12506584324303623050),
            (datetime.date(2024, 1, 15), 12094587152155689920),
            (datetime.time(10, 30, 45), 7669327382447786887),
            (
                datetime.datetime(2024, 1, 15, 10, 30, tzinfo=datetime.timezone.utc),
                6356847411642271134,
            ),
        ]:
            self.assertEqual(deterministic_hash(value), expected)

    def test_complex_objects(self):
        for obj, expected in [
            ([1, 2, 3], 18411644864286483529),
            ({"name": "John", "age": 30}, 14434407841181989270),
            ((1, "tuple", 3.14), 1758590964072651304),
            ({"nested": {"deep": [1, 2, {"more": "data"}]}}, 11041018134964410091),
        ]:
            self.assertEqual(deterministic_hash(obj), expected)

    def test_different_values_different_hashes(self):
        for value, expected in [
            (2, 2),
            (3, 3),
            ("hello", 2794345569481354659),
            ("world", 16679358290033791471),
            ([1, 2], 15366073274920769204),
            ([2, 1], 6350583200841052616),
            ({"a": 1}, 15961709706453961884),
            ({"a": 2}, 3162048860685962812),
            ("True", 17732755876315995952),
            ("False", 1044637672521554167),
        ]:
            self.assertEqual(deterministic_hash(value), expected)


class TestHasher(unittest.TestCase):
    def test_empty_hasher(self):
        self.assertEqual(Hasher().digest(), 17241709254077376921)

    def test_single_value(self):
        h = Hasher()
        h.update("test")
        self.assertEqual(h.digest(), 9680477713229540635)

    def test_multiple_values_order_matters(self):
        """Test that order of updates affects the final hash."""
        h1 = Hasher()
        h1.update("first")
        h1.update("second")
        self.assertEqual(h1.digest(), 1747033864432273957)

        h2 = Hasher()
        h2.update("second")
        h2.update("first")
        self.assertEqual(h2.digest(), 14661069772275380988)

    def test_db_row_like_data(self):
        """Test with database row-like tuples."""
        rows = [(1, "Alice", 25), (2, "Bob", 30), (3, "Charlie", 35)]

        h = Hasher()
        for row in rows:
            h.update(row)

        self.assertEqual(h.digest(), 13382544848678539704)

    def test_different_data_types(self):
        """Test with various Python data types."""
        values = [
            42,
            3.14,
            "string",
            b"bytes",
            [1, 2, 3],
            {"key": "value"},
            None,
            True,
            uuid.UUID("12345678-1234-5678-1234-123456789abc"),
        ]

        h = Hasher()
        for value in values:
            h.update(value)

        self.assertEqual(h.digest(), 15408561512376601701)
