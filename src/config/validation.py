"""Configuration validation and schema enforcement."""

import logging
from typing import Any, Dict, List, Type
from enum import Enum

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Configuration validation error."""

    pass


class ConfigType(Enum):
    """Configuration value types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"


class ConfigValidator:
    """Validate configuration values."""

    @staticmethod
    def validate_string(value: Any, min_length: int = 0, max_length: int = None) -> str:
        """Validate string configuration."""
        if not isinstance(value, str):
            raise ConfigValidationError(f"Expected string, got {type(value).__name__}")

        if len(value) < min_length:
            raise ConfigValidationError(f"String length must be at least {min_length}")

        if max_length and len(value) > max_length:
            raise ConfigValidationError(f"String length must not exceed {max_length}")

        return value

    @staticmethod
    def validate_integer(value: Any, min_val: int = None, max_val: int = None) -> int:
        """Validate integer configuration."""
        if not isinstance(value, int) or isinstance(value, bool):
            raise ConfigValidationError(f"Expected integer, got {type(value).__name__}")

        if min_val is not None and value < min_val:
            raise ConfigValidationError(f"Value must be at least {min_val}")

        if max_val is not None and value > max_val:
            raise ConfigValidationError(f"Value must not exceed {max_val}")

        return value

    @staticmethod
    def validate_float(value: Any, min_val: float = None, max_val: float = None) -> float:
        """Validate float configuration."""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConfigValidationError(f"Expected float, got {type(value).__name__}")

        value = float(value)

        if min_val is not None and value < min_val:
            raise ConfigValidationError(f"Value must be at least {min_val}")

        if max_val is not None and value > max_val:
            raise ConfigValidationError(f"Value must not exceed {max_val}")

        return value

    @staticmethod
    def validate_boolean(value: Any) -> bool:
        """Validate boolean configuration."""
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            if value.lower() in ("true", "yes", "1"):
                return True
            if value.lower() in ("false", "no", "0"):
                return False

        raise ConfigValidationError(f"Expected boolean, got {type(value).__name__}")

    @staticmethod
    def validate_list(value: Any, item_type: Type = None) -> List:
        """Validate list configuration."""
        if not isinstance(value, list):
            raise ConfigValidationError(f"Expected list, got {type(value).__name__}")

        if item_type:
            for item in value:
                if not isinstance(item, item_type):
                    raise ConfigValidationError(
                        f"List item must be {item_type.__name__}, got {type(item).__name__}"
                    )

        return value

    @staticmethod
    def validate_dict(value: Any, key_type: Type = None, value_type: Type = None) -> Dict:
        """Validate dict configuration."""
        if not isinstance(value, dict):
            raise ConfigValidationError(f"Expected dict, got {type(value).__name__}")

        if key_type or value_type:
            for k, v in value.items():
                if key_type and not isinstance(k, key_type):
                    raise ConfigValidationError(
                        f"Dict key must be {key_type.__name__}, got {type(k).__name__}"
                    )
                if value_type and not isinstance(v, value_type):
                    raise ConfigValidationError(
                        f"Dict value must be {value_type.__name__}, got {type(v).__name__}"
                    )

        return value


class ConfigSchema:
    """Schema for configuration validation."""

    def __init__(self, name: str):
        """Initialize schema."""
        self.name = name
        self.fields = {}

    def add_field(
        self,
        field_name: str,
        field_type: ConfigType,
        required: bool = True,
        default: Any = None,
        **kwargs,
    ):
        """Add field to schema."""
        self.fields[field_name] = {
            "type": field_type,
            "required": required,
            "default": default,
            "kwargs": kwargs,
        }

    def validate(self, config: Dict) -> Dict:
        """Validate configuration against schema."""
        validated = {}
        errors = []

        for field_name, field_spec in self.fields.items():
            field_type = field_spec["type"]
            required = field_spec["required"]
            default = field_spec["default"]
            kwargs = field_spec["kwargs"]

            if field_name not in config:
                if required and default is None:
                    errors.append(f"Required field missing: {field_name}")
                    continue
                validated[field_name] = default
                continue

            value = config[field_name]

            try:
                if field_type == ConfigType.STRING:
                    validated[field_name] = ConfigValidator.validate_string(value, **kwargs)
                elif field_type == ConfigType.INTEGER:
                    validated[field_name] = ConfigValidator.validate_integer(value, **kwargs)
                elif field_type == ConfigType.FLOAT:
                    validated[field_name] = ConfigValidator.validate_float(value, **kwargs)
                elif field_type == ConfigType.BOOLEAN:
                    validated[field_name] = ConfigValidator.validate_boolean(value)
                elif field_type == ConfigType.LIST:
                    validated[field_name] = ConfigValidator.validate_list(value, **kwargs)
                elif field_type == ConfigType.DICT:
                    validated[field_name] = ConfigValidator.validate_dict(value, **kwargs)
            except ConfigValidationError as e:
                errors.append(f"Field {field_name}: {str(e)}")

        if errors:
            raise ConfigValidationError("; ".join(errors))

        return validated


class ApplicationConfigSchema(ConfigSchema):
    """Default application configuration schema."""

    def __init__(self):
        """Initialize app config schema."""
        super().__init__("application")

        self.add_field("APP_NAME", ConfigType.STRING, required=True, default="QuantAI")
        self.add_field("APP_VERSION", ConfigType.STRING, required=True, default="0.1.0")
        self.add_field("DEBUG", ConfigType.BOOLEAN, required=False, default=False)
        self.add_field("LOG_LEVEL", ConfigType.STRING, required=False, default="INFO")
        self.add_field("DATABASE_URL", ConfigType.STRING, required=True)
        self.add_field(
            "API_PORT", ConfigType.INTEGER, required=False, default=8000, min_val=1, max_val=65535
        )
        self.add_field("WORKERS", ConfigType.INTEGER, required=False, default=4, min_val=1)
        self.add_field("CORS_ORIGINS", ConfigType.LIST, required=False, default=["*"])
        self.add_field("SECRET_KEY", ConfigType.STRING, required=True, min_length=32)
        self.add_field("TIMEOUT", ConfigType.INTEGER, required=False, default=30, min_val=1)
