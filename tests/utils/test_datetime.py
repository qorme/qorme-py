import unittest
from datetime import datetime, timezone

from qorme.utils.datetime import utcnow


class TestUTCNow(unittest.TestCase):
    def test_utcnow(self):
        current_time = utcnow()
        self.assertIsInstance(current_time, datetime)
        self.assertEqual(current_time.tzinfo, timezone.utc)
