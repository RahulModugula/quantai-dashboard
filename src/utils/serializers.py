"""Serialization utilities for JSON and data structures."""

import json
from datetime import datetime
from decimal import Decimal


class CustomEncoder(json.JSONEncoder):
    """Custom JSON encoder for special types."""

    def default(self, obj):
        """Handle non-standard types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


def serialize_to_json(obj) -> str:
    """Serialize object to JSON string."""
    return json.dumps(obj, cls=CustomEncoder)


def deserialize_from_json(json_str: str):
    """Deserialize JSON string to object."""
    return json.loads(json_str)


def to_dict(obj) -> dict:
    """Convert object to dictionary."""
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    elif isinstance(obj, dict):
        return obj
    return {}


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten nested dictionary."""
    items = []

    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))

    return dict(items)
