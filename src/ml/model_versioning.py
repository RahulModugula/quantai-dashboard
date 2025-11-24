"""Model versioning and management."""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class ModelStatus(str, Enum):
    """Model status values."""

    TRAINING = "training"
    READY = "ready"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ModelVersion:
    """Model version metadata."""

    def __init__(
        self,
        model_name: str,
        version: str,
        path: str,
        metrics: Dict = None,
    ):
        """Initialize model version.

        Args:
            model_name: Name of the model
            version: Version identifier
            path: Path to model file
            metrics: Performance metrics
        """
        self.model_name = model_name
        self.version = version
        self.path = path
        self.metrics = metrics or {}
        self.status = ModelStatus.TRAINING
        self.created_at = datetime.now()
        self.deployed_at = None
        self.accuracy = self.metrics.get("accuracy", 0)
        self.f1_score = self.metrics.get("f1_score", 0)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "model_name": self.model_name,
            "version": self.version,
            "path": self.path,
            "status": self.status.value,
            "metrics": self.metrics,
            "accuracy": self.accuracy,
            "f1_score": self.f1_score,
            "created_at": self.created_at.isoformat(),
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
        }


class ModelRegistry:
    """Registry for managing model versions."""

    def __init__(self, registry_dir: str = "./models"):
        """Initialize model registry.

        Args:
            registry_dir: Directory for model storage
        """
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(exist_ok=True)
        self.models: Dict[str, List[ModelVersion]] = {}
        self.current_versions: Dict[str, str] = {}

    def register_model(
        self,
        model_name: str,
        version: str,
        path: str,
        metrics: Dict = None,
    ) -> ModelVersion:
        """Register a new model version.

        Args:
            model_name: Name of the model
            version: Version identifier
            path: Path to model file
            metrics: Performance metrics

        Returns:
            Model version metadata
        """
        if model_name not in self.models:
            self.models[model_name] = []

        model_version = ModelVersion(model_name, version, path, metrics)
        self.models[model_name].append(model_version)

        logger.info(f"Model registered: {model_name} v{version}")

        return model_version

    def get_model(self, model_name: str, version: str = None) -> Optional[ModelVersion]:
        """Get a model version.

        Args:
            model_name: Name of the model
            version: Version identifier (latest if not specified)

        Returns:
            Model version or None
        """
        if model_name not in self.models:
            return None

        versions = self.models[model_name]

        if version:
            for v in versions:
                if v.version == version:
                    return v
        else:
            # Return current version if set, otherwise latest
            if model_name in self.current_versions:
                version_id = self.current_versions[model_name]
                for v in versions:
                    if v.version == version_id:
                        return v

            # Return latest ready version
            ready_versions = [v for v in versions if v.status == ModelStatus.READY]
            if ready_versions:
                return sorted(ready_versions, key=lambda v: v.created_at)[-1]

        return versions[-1] if versions else None

    def set_current_version(self, model_name: str, version: str) -> bool:
        """Set current active version.

        Args:
            model_name: Name of the model
            version: Version to activate

        Returns:
            Whether operation was successful
        """
        if model_name not in self.models:
            logger.error(f"Model not found: {model_name}")
            return False

        for v in self.models[model_name]:
            if v.version == version:
                self.current_versions[model_name] = version
                v.status = ModelStatus.READY
                v.deployed_at = datetime.now()
                logger.info(f"Current version set: {model_name} v{version}")
                return True

        logger.error(f"Version not found: {model_name} v{version}")
        return False

    def list_versions(self, model_name: str) -> List[Dict]:
        """List all versions of a model."""
        if model_name not in self.models:
            return []

        versions = sorted(
            self.models[model_name],
            key=lambda v: v.created_at,
            reverse=True,
        )

        return [v.to_dict() for v in versions]

    def get_model_comparison(self, model_name: str) -> Dict:
        """Compare all versions of a model."""
        if model_name not in self.models:
            return {}

        versions = sorted(
            self.models[model_name],
            key=lambda v: v.created_at,
        )

        return {
            "model_name": model_name,
            "total_versions": len(versions),
            "versions": [v.to_dict() for v in versions],
            "best_by_accuracy": max(versions, key=lambda v: v.accuracy).to_dict()
            if versions
            else None,
            "best_by_f1": max(versions, key=lambda v: v.f1_score).to_dict() if versions else None,
        }

    def deprecate_version(self, model_name: str, version: str) -> bool:
        """Deprecate a model version.

        Args:
            model_name: Name of the model
            version: Version to deprecate

        Returns:
            Whether operation was successful
        """
        if model_name not in self.models:
            return False

        for v in self.models[model_name]:
            if v.version == version:
                v.status = ModelStatus.DEPRECATED
                logger.info(f"Model deprecated: {model_name} v{version}")
                return True

        return False

    def get_stats(self) -> dict:
        """Get registry statistics."""
        total_versions = sum(len(v) for v in self.models.values())
        total_ready = sum(
            len([v for v in versions if v.status == ModelStatus.READY])
            for versions in self.models.values()
        )

        return {
            "total_models": len(self.models),
            "total_versions": total_versions,
            "ready_versions": total_ready,
            "models": list(self.models.keys()),
        }


# Global model registry
_registry = ModelRegistry()


def get_registry() -> ModelRegistry:
    """Get global model registry."""
    return _registry


def register_model(
    model_name: str,
    version: str,
    path: str,
    metrics: Dict = None,
) -> ModelVersion:
    """Register a model globally."""
    registry = get_registry()
    return registry.register_model(model_name, version, path, metrics)


def get_model(model_name: str, version: str = None) -> Optional[ModelVersion]:
    """Get a model globally."""
    registry = get_registry()
    return registry.get_model(model_name, version)
