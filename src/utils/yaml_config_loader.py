# StartAllScript/src/utility/yaml_config_loader.py

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from yaml import safe_load as yaml_safe_load
from yaml import YAMLError as yaml_YAMLError


def _check_file_path(path: Union[str, Path]) -> None:
    path_obj = Path(path) if isinstance(path, str) else path
    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path_obj.is_file():
        raise ValueError(f"Path is not a file: {path}")


class ConfigLoadError(Exception):
    """Base exception for configuration loading errors."""


class ConfigFileEmptyError(ConfigLoadError):
    """Raised when the configuration file is empty."""


class ConfigKeyNotFoundError(ConfigLoadError):
    """Raised when a required key is not found in the configuration."""


class ConfigValidationError(ConfigLoadError):
    """Raised when the configuration fails validation."""


class YamlConfigLoader:
    """
    A generic YAML configuration loader that supports arbitrary nesting levels and provides robust error handling.

    This class is designed to load YAML configuration files, validate their contents, and provide access to nested
    configuration values using dot notation (e.g., "a.b.c"). It follows SOLID principles and includes private
    methods for internal validation and error checking.

    Attributes:
        config_path (str): Path to the YAML configuration file.
        config_data (Dict[str, Any]): Loaded configuration data.
    """

    def __init__(self, config_path: Union[str, Path]):
        """
        Initialize the YamlConfigLoader with a configuration file path.

        Args:
            config_path (str): Path to the YAML configuration file.
        """
        _check_file_path(config_path)

        self.config_path = config_path
        self.config_data: Dict[str, Any] = {}

        self.__load_config()

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Retrieve a value from the configuration by key, supporting arbitrary nesting.

        Args:
            key (str): The key to look up in the configuration (e.g., "a.b.c" for nested access).
            default (Optional[Any]): Default value to return if the key is not found. If None, raises an exception.

        Returns:
            Any: The value associated with the key.

        Raises:
            ConfigKeyNotFoundError: If the key is not found and no default is provided.
        """
        keys = key.split(".")

        try:
            value = self.__navigate_nested_keys(keys, self.config_data)
            return value
        except ConfigKeyNotFoundError as e:
            if default is not None:
                return default
            raise ConfigKeyNotFoundError(f"Key '{key}' not found, returning default: {default}: {e}")

    def get_required(self, key: str) -> Any:
        """
        Retrieve a required value from the configuration by key, supporting arbitrary nesting.

        Args:
            key (str): The key to look up in the configuration (e.g., "a.b.c" for nested access).

        Returns:
            Any: The value associated with the key.

        Raises:
            ConfigKeyNotFoundError: If the key is not found.
        """
        return self.get(key)

    def validate_keys(self, required_keys: List[str]) -> None:
        """
        Validate that all specified keys exist in the configuration, supporting arbitrary nesting.

        Args:
            required_keys (List[str]): List of keys that must be present (e.g., ["a.b.c", "x.y"]).

        Raises:
            ConfigValidationError: If any required key is missing.
        """
        missing_keys = []

        for key in required_keys:
            try:
                self.get_required(key)
            except ConfigKeyNotFoundError:
                missing_keys.append(key)

        if missing_keys:
            raise ConfigValidationError(f"Missing required keys in configuration: {missing_keys}")

    def get_nested_dict(self, key: str) -> Dict[str, Any]:
        """
        Retrieve a nested dictionary from the configuration by key, supporting arbitrary nesting.

        Args:
            key (str): The key to a nested dictionary (e.g., "a.b.c" for nested access).

        Returns:
            Dict[str, Any]: The nested dictionary.

        Raises:
            ConfigKeyNotFoundError: If the key is not found.
            ConfigValidationError: If the value at the key is not a dictionary.
        """
        value = self.get_required(key)
        if not isinstance(value, dict):
            raise ConfigValidationError(f"Value at '{key}' is not a dictionary: {type(value)}")
        return value

    def __load_config(self) -> None:
        """
        Private method to load and parse the YAML configuration file.

        Raises:
            ConfigFileEmptyError: If the file is empty or contains no valid YAML data.
            ConfigLoadError: If there is an error parsing the YAML content.
        """
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_data = yaml_safe_load(f)

            if not config_data:
                raise ConfigFileEmptyError(f"Configuration file {self.config_path} is empty")

            if not isinstance(config_data, dict):
                raise ConfigLoadError(f"Configuration must be a dictionary, got {type(config_data)}")

            self.__validate_loaded_data(config_data)
            self.config_data = config_data

        except yaml_YAMLError as e:
            raise ConfigLoadError(f"Failed to parse YAML from {self.config_path}: {str(e)}")
        except Exception as e:
            raise ConfigLoadError(f"Unexpected error loading {self.config_path}: {str(e)}")

    def __validate_loaded_data(self, config_data: Any) -> None:
        """
        Private method to validate the loaded configuration data.

        Args:
            config_data (Any): The data loaded from the YAML file.

        Raises:
            ConfigFileEmptyError: If the configuration data is empty or None.
        """
        if not config_data:
            msg = f"Configuration file {self.config_path} is empty"
            raise ConfigFileEmptyError(msg)

    def __navigate_nested_keys(self, keys: List[str], data: Dict[str, Any]) -> Any:
        """
        Private method to navigate through nested dictionary keys.

        Args:
            keys (List[str]): List of keys representing the path (e.g., ["a", "b", "c"] for "a.b.c").
            data (Dict[str, Any]): The dictionary to navigate.

        Returns:
            Any: The value at the specified key path.

        Raises:
            ConfigKeyNotFoundError: If any key in the path is not found or the path traverses a non-dictionary value.
        """
        current = data
        for key in keys:
            try:
                current = current[key]
            except (KeyError, TypeError) as e:
                raise ConfigKeyNotFoundError(f"Key path '{'.'.join(keys)}' not found at '{key}' in configuration: {e}")
        return current
