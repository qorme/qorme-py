import os
import pickle
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from qorme.utils.config import _SENTINEL, Config, ConfigurationError


class TestConfig(unittest.TestCase):
    @contextmanager
    def mock_env_var(self, name: str, value: str):
        with patch("qorme.utils.config.os.getenv", return_value=value) as mock_getenv:
            yield mock_getenv

    def test_config_uses_defaults_types_if_not_provided(self):
        defaults = {
            "debug": True,
            "name": "test",
            "value": 1,
            "timeout": 0.5,
            "items": [1, 2, 3],
            "db": {
                "url": "sqlite://",
                "handlers": frozenset(["a", "b", "c"]),
            },
            "cache": {"memory": {"sample": ("qwerty", 225, [])}},
        }
        config = Config(name="test", data={}, defaults=defaults, types=None)
        self.assertDictEqual(
            config.types,
            {
                "debug": bool,
                "name": str,
                "value": int,
                "timeout": float,
                "items": list,
                "db": {
                    "url": str,
                    "handlers": frozenset,
                },
                "cache": {"memory": {"sample": tuple}},
            },
        )

    def test_load_from_env_uses_uppercase_env_var_name(self):
        config = Config(name="test", data={}, defaults={}, types={})
        with (
            self.mock_env_var("test_env_var", _SENTINEL) as mock_getenv,
            self.assertRaises(AttributeError),
        ):
            _ = config.test_env_var
            mock_getenv.assert_called_once_with("TEST_ENV_VAR", _SENTINEL)

    def test_load_from_env_raises_error_when_var_type_is_not_specified(self):
        config = Config(name="test", data={}, defaults={}, types={})
        expected_error_message = "Type of `env_var` was not specified in test config"
        with (
            self.mock_env_var("TEST_ENV_VAR", "test"),
            self.assertRaisesRegex(ConfigurationError, expected_error_message),
        ):
            _ = config.env_var

    def test_load_from_env_raises_error_when_no_parser_found_for_var_type(self):
        config = Config(name="test", data={}, defaults={}, types={"env_var": dict})
        expected_error_message = (
            r"No parser found for \(attr: env_var, type: <class 'dict'>\) in test config"
        )
        with (
            self.mock_env_var("TEST_ENV_VAR", "test"),
            self.assertRaisesRegex(ConfigurationError, expected_error_message),
        ):
            _ = config.env_var

    def test_load_from_env_raises_error_when_parsing_fails(self):
        for _type, bad_value in [(int, "not an int"), (float, "not a float")]:
            config = Config(name="test", data={}, defaults={}, types={"env_var": _type})
            expected_error_message = (
                rf"Expected {_type} for env_var, got {bad_value} instead in test config"
            )
            with (
                self.subTest(type=_type, bad_value=bad_value),
                self.mock_env_var("TEST_ENV_VAR", bad_value),
                self.assertRaisesRegex(ConfigurationError, expected_error_message),
            ):
                _ = config.env_var

    def test_load_from_env(self):
        for _type, value, parsed in [
            (str, "test", "test"),
            (int, "1", 1),
            (float, "1.0", 1.0),
            (bool, "y", True),
            (list, " a, b ,  c ", ["a", "b", "c"]),
        ]:
            config = Config(name="test", data={}, defaults={}, types={"env_var": _type})
            with self.subTest(type=_type, value=value), self.mock_env_var("TEST_ENV_VAR", value):
                self.assertEqual(config.env_var, parsed)

    def test_load_from_data_raises_error_when_var_type_is_not_specified(self):
        config = Config(name="test", data={"debug": None}, defaults={}, types={})
        expected_error_message = "Type of `debug` was not specified in test config"
        with self.assertRaisesRegex(ConfigurationError, expected_error_message):
            _ = config.debug

    def test_load_from_data_raises_error_when_invalid_type_is_specified(self):
        config = Config(name="test", data={"debug": None}, defaults={}, types={"debug": False})
        expected_error_message = "Invalid type specified for `debug` value in test config: False"
        with self.assertRaisesRegex(ConfigurationError, expected_error_message):
            _ = config.debug

    def test_load_from_data_raises_error_when_value_does_not_match_type(self):
        for _type, value in [
            (str, 1),
            (int, "not an int"),
            (float, 10),
            # (bool, [1, 2, 3]),
            (list, {4: 5}),
        ]:
            config = Config(name="test", data={"debug": value}, defaults={}, types={"debug": _type})
            expected_error_message = (
                rf"Expected {_type} for debug, got {value} instead in test config"
            )
            with (
                self.subTest(type=_type, value=value),
                self.assertRaisesRegex(ConfigurationError, expected_error_message),
            ):
                _ = config.debug

    def test_load_from_data(self):
        for _type, value in [
            (str, "test"),
            (int, 1),
            (float, 1.0),
            (bool, False),
            (list, ["a", "b", "c"]),
        ]:
            config = Config(name="test", data={"debug": value}, defaults={}, types={"debug": _type})
            with self.subTest(type=_type, value=value):
                self.assertEqual(config.debug, value)

    def test_load_from_defaults(self):
        defaults = {"debug": True, "name": "test", "value": 1, "pks": [1, 2, 3]}
        config = Config(name="test", data={}, defaults=defaults, types={})
        self.assertEqual(config.debug, True)
        self.assertEqual(config.name, "test")
        self.assertEqual(config.value, 1)
        self.assertEqual(config.pks, [1, 2, 3])

    def test_load_class_raises_error_when_import_fails(self):
        config = Config(
            name="test",
            data={"handler": "path.to.nonexistent.class"},
            defaults={},
            types={"handler": str},
        )
        expected_error_message = (
            "Couldn't import handler_class 'path.to.nonexistent.class' for test config"
        )
        with self.assertRaisesRegex(ConfigurationError, expected_error_message):
            _ = config.handler_class

    def test_load_class(self):
        config = Config(
            name="test",
            data={"handler": f"{TestConfig.__module__}.{TestConfig.__name__}"},
            defaults={},
            types={"handler": str},
        )
        self.assertEqual(config.handler_class, TestConfig)

    def test_load_nested(self):
        config = Config(
            name="test",
            types={
                "tracking": {"handler": str},
                "db": {"debug": bool, "env": {"var": str, "timeout": int}},
            },
            data={
                "tracking": {"handler": f"{TestConfig.__module__}.{TestConfig.__name__}"},
                "db": {"env": {"timeout": 10}},
            },
            defaults={"db": {"debug": True}},
        )

        self.assertEqual(config.tracking.handler_class, TestConfig)
        self.assertEqual(config.db.env.timeout, 10)
        self.assertEqual(config.db.debug, True)

        os.environ["TEST_DB_ENV_VAR"] = "test"
        self.assertEqual(config.db.env.var, "test")
        del os.environ["TEST_DB_ENV_VAR"]

    def test_load_caches_result(self):
        config = Config(name="test", data={}, defaults={"debug": True}, types={})
        # Test that attribute is lazily loaded and cached.
        self.assertNotIn("debug", config.__dict__)
        self.assertIs(config.debug, True)
        self.assertIn("debug", config.__dict__)

    def test_load_missing_attribute(self):
        config = Config(name="test", data={}, defaults={}, types={})
        with self.assertRaises(AttributeError):
            _ = config.debug

    def test_pickle(self):
        # Test that Config can be pickled and unpickled
        config = Config(
            name="test",
            data={"debug": True},
            defaults={"items": [1, 2, 3]},
            types={"debug": bool, "items": list},
        )
        pickled = pickle.dumps(config)
        unpickled = pickle.loads(pickled)

        # Verify the unpickled object has the same data
        self.assertEqual(unpickled, config)

    def test_dict_behavior(self):
        config = Config(name="test", data={"debug": True}, defaults={"engine": "sqlite"}, types={})
        self.assertEqual(len(config), 1)
        self.assertEqual(config, {"debug": True})
        self.assertNotIn("engine", config)
