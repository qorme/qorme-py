import unittest

from qorme.client.dsn import DSN, DSNError


class TestDSN(unittest.TestCase):
    def test_parse(self):
        cases = [
            ("https://apikey@host", "https://host:443", "apikey", None),
            ("https://api-key@host:92", "https://host:92", "api-key", None),
            ("http://apikey@host", None, None, DSNError),
            ("https://@host", None, None, DSNError),
            ("https://apikey@", None, None, DSNError),
        ]
        for idx, (dsn, expected_url, expected_api_key, expected_exception) in enumerate(cases):
            with self.subTest(case=idx, dsn=dsn):
                if expected_exception:
                    with self.assertRaises(expected_exception):
                        DSN.parse(dsn)
                else:
                    obj = DSN.parse(dsn)
                    self.assertEqual(obj.url, expected_url)
                    self.assertEqual(obj.api_key, expected_api_key)
