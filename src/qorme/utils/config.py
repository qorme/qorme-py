import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing import TypeAlias

    ConfigType: TypeAlias = type | dict[str, Any]


# Sentinel object used to detect missing values in mappings.
_SENTINEL = object()

# Values that are considered True for boolean environment variables
_TRUTHY_VALUES = {"true", "t", "yes", "y", "1"}

# Mapping of types to their parsing functions for environment variables
_ENV_VAR_PARSERS: dict[type, Callable[[str], Any]] = {
    str: str,
    int: int,
    float: float,
    bool: lambda value: value.lower() in _TRUTHY_VALUES,
    list: lambda value: [s.strip() for s in value.split(",")],
}


def _get_types_from_dict(d: dict[str, Any]) -> dict[str, "ConfigType"]:
    # Returns the expected type structure based on data in the provided dict.
    return {
        k: type(v) if not isinstance(v, dict) else _get_types_from_dict(v) for k, v in d.items()
    }


class ConfigurationError(ValueError):
    """Configuration loading or validation failure."""

    ...


class Config(dict):
    """
    A flexible configuration container.

    It can load settings from environment variables,
    user data, or/and default values with type validation and auto-importing classes.

    This class handles loading configuration values from multiple sources with precedence:
    1. Environment variables (uppercase)
    2. Provided configuration data
    3. Default values

    It supports nested configurations and automatically imports classes from dotted paths
    when the attribute requested ends with "_class".

    Attributes:
        name: Base name for the configuration section, used in error messages and env vars
        data: Dictionary containing configuration values
        defaults: Dictionary containing default values
        types: Dictionary specifying expected types for configuration values
    """

    def __init__(
        self,
        name: str,
        data: dict[str, Any],
        defaults: dict[str, Any],
        types: dict[str, "ConfigType"] | None = None,
    ):
        super().__init__(data)
        self.name = name
        self.defaults = defaults
        self.types = (
            types if types is not None else _get_types_from_dict(defaults if defaults else data)
        )

    def _get_attr_type(self, attr: str) -> type:
        if (_type := self.types.get(attr)) is None:
            raise ConfigurationError(f"Type of `{attr}` was not specified in {self.name} config")
        if isinstance(_type, type):
            return _type
        elif isinstance(_type, dict):
            return dict
        else:
            raise ConfigurationError(
                f"Invalid type specified for `{attr}` value in {self.name} config: {_type}"
            )

    def _check_value_type(self, value: Any, attr: str) -> None:
        # Validates that a value matches its expected type.
        _type = self._get_attr_type(attr)
        if not isinstance(value, _type):
            raise ConfigurationError(
                f"Expected {_type} for {attr}, got {value} instead in {self.name} config"
            )

    def _parse_value_from_env(self, value: str, attr: str) -> Any:
        # Parses a string value from an environment variable into the expected type.
        _type = self._get_attr_type(attr)
        if not (parser := _ENV_VAR_PARSERS.get(_type)):
            raise ConfigurationError(
                f"No parser found for (attr: {attr}, type: {_type}) in {self.name} config"
            )

        try:
            return parser(value)
        except ValueError as e:
            raise ConfigurationError(
                f"Expected {_type} for {attr}, got {value} instead in {self.name} config"
            ) from e

    def _import_string(self, path: str, attr: str) -> Any:
        # Imports a class or object from a dotted path string.
        from qorme.utils.module_loading import import_string

        try:
            return import_string(path)
        except ImportError as e:
            raise ConfigurationError(
                f"Couldn't import {attr} '{path}' for {self.name} config"
            ) from e

    def __getattr__(self, attr: str) -> Any:
        """
        Retrieves a configuration value with lazy loading and caching.

        The lookup order is:
        1. Special '_class' suffix handling for importing classes
        2. Environment variables (uppercase)
        3. Provided configuration data
        4. Default values

        Args:
            attr: Name of the configuration attribute

        Returns:
            Configuration value

        Raises:
            AttributeError: If attribute doesn't exist
            ConfigurationError: If validation fails
        """
        name = f"{self.name}_{attr}"
        if attr.endswith("_class") and (
            dotted_path := getattr(self, attr.removesuffix("_class"), "")
        ):
            value = self._import_string(dotted_path, attr)
        elif (value := os.getenv(name.upper(), _SENTINEL)) is not _SENTINEL:
            assert isinstance(value, str)
            value = self._parse_value_from_env(value, attr)
        elif (value := self.get(attr, _SENTINEL)) is not _SENTINEL:
            self._check_value_type(value, attr)
        elif (value := self.defaults.get(attr, _SENTINEL)) is _SENTINEL:
            raise AttributeError(attr)

        # Handle nested configuration
        if isinstance(value, dict):
            types = self.types.get(attr)
            if not isinstance(types, dict):
                types = None
            value = Config(
                name=name,
                data=value,
                defaults=self.defaults.get(attr, {}),
                types=types,
            )

        # Cache the value
        setattr(self, attr, value)
        return value

    def __reduce__(self) -> tuple[type, tuple[str, dict, dict, dict]]:
        """Enables pickle support."""
        return type(self), (self.name, dict(self), self.defaults, self.types)
