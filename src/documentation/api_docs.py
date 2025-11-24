"""API documentation generation."""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class HTTPMethod(str, Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class Parameter:
    """API parameter documentation."""

    def __init__(
        self,
        name: str,
        param_type: str,
        required: bool = False,
        description: str = None,
        example: str = None,
    ):
        """Initialize parameter.

        Args:
            name: Parameter name
            param_type: Parameter type (string, integer, etc.)
            required: Whether parameter is required
            description: Parameter description
            example: Example value
        """
        self.name = name
        self.param_type = param_type
        self.required = required
        self.description = description
        self.example = example

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.param_type,
            "required": self.required,
            "description": self.description,
            "example": self.example,
        }


class Endpoint:
    """API endpoint documentation."""

    def __init__(
        self,
        method: HTTPMethod,
        path: str,
        summary: str,
        description: str = None,
    ):
        """Initialize endpoint.

        Args:
            method: HTTP method
            path: API path
            summary: Brief summary
            description: Detailed description
        """
        self.method = method
        self.path = path
        self.summary = summary
        self.description = description
        self.parameters: List[Parameter] = []
        self.response_schema = None
        self.response_example = None
        self.tags: List[str] = []
        self.deprecated = False

    def add_parameter(self, parameter: Parameter):
        """Add parameter to endpoint."""
        self.parameters.append(parameter)

    def set_response(self, schema: Dict, example: Dict = None):
        """Set response schema and example."""
        self.response_schema = schema
        self.response_example = example

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "method": self.method.value,
            "path": self.path,
            "summary": self.summary,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
            "response": {
                "schema": self.response_schema,
                "example": self.response_example,
            },
            "tags": self.tags,
            "deprecated": self.deprecated,
        }


class APIDocumentation:
    """API documentation generator."""

    def __init__(self, title: str, version: str, base_url: str = ""):
        """Initialize API documentation.

        Args:
            title: API title
            version: API version
            base_url: Base URL for API
        """
        self.title = title
        self.version = version
        self.base_url = base_url
        self.description = None
        self.endpoints: Dict[str, Endpoint] = {}
        self.created_at = datetime.now()

    def add_endpoint(self, endpoint: Endpoint):
        """Add endpoint to documentation."""
        key = f"{endpoint.method.value} {endpoint.path}"
        self.endpoints[key] = endpoint

        logger.info(f"Endpoint documented: {key}")

    def get_endpoint(self, method: HTTPMethod, path: str) -> Optional[Endpoint]:
        """Get endpoint documentation."""
        key = f"{method.value} {path}"
        return self.endpoints.get(key)

    def get_endpoints_by_tag(self, tag: str) -> List[Endpoint]:
        """Get endpoints with specific tag."""
        return [e for e in self.endpoints.values() if tag in e.tags]

    def generate_markdown(self) -> str:
        """Generate Markdown documentation."""
        lines = [
            f"# {self.title}",
            f"\nVersion: {self.version}",
            f"\nBase URL: {self.base_url}",
            f"\nGenerated: {self.created_at.isoformat()}",
        ]

        if self.description:
            lines.append(f"\n## Description\n\n{self.description}")

        # Group by tags
        all_tags = set()
        for endpoint in self.endpoints.values():
            all_tags.update(endpoint.tags)

        for tag in sorted(all_tags):
            lines.append(f"\n## {tag}\n")

            for endpoint in self.get_endpoints_by_tag(tag):
                lines.append(f"### {endpoint.method.value} {endpoint.path}\n")
                lines.append(f"{endpoint.summary}\n")

                if endpoint.description:
                    lines.append(f"{endpoint.description}\n")

                if endpoint.parameters:
                    lines.append("#### Parameters\n")
                    for param in endpoint.parameters:
                        lines.append(
                            f"- `{param.name}` ({param.param_type})"
                            f"{' *required*' if param.required else ''}: "
                            f"{param.description or ''}\n"
                        )

                if endpoint.response_schema:
                    lines.append("#### Response\n")
                    lines.append("```json\n")
                    import json

                    lines.append(
                        json.dumps(endpoint.response_example or endpoint.response_schema, indent=2)
                    )
                    lines.append("\n```\n")

        return "".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "version": self.version,
            "base_url": self.base_url,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "endpoints": {k: v.to_dict() for k, v in self.endpoints.items()},
        }

    def get_stats(self) -> dict:
        """Get documentation statistics."""
        methods = {}
        tags = set()

        for endpoint in self.endpoints.values():
            method = endpoint.method.value
            methods[method] = methods.get(method, 0) + 1
            tags.update(endpoint.tags)

        return {
            "total_endpoints": len(self.endpoints),
            "methods": methods,
            "tags": sorted(list(tags)),
            "documented_parameters": sum(len(e.parameters) for e in self.endpoints.values()),
        }


# Global API documentation
_docs = None


def init_docs(title: str, version: str, base_url: str = "") -> APIDocumentation:
    """Initialize global API documentation."""
    global _docs
    _docs = APIDocumentation(title, version, base_url)
    return _docs


def get_docs() -> APIDocumentation:
    """Get global API documentation."""
    if _docs is None:
        raise RuntimeError("API documentation not initialized. Call init_docs() first.")
    return _docs


def document_endpoint(method: HTTPMethod, path: str, summary: str) -> Endpoint:
    """Create and register endpoint documentation."""
    docs = get_docs()
    endpoint = Endpoint(method, path, summary)
    docs.add_endpoint(endpoint)
    return endpoint
