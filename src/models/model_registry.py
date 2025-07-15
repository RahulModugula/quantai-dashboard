"""Registry for managing multiple model versions."""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Manage and track multiple model versions."""

    def __init__(self):
        self.models = {}
        self.current_model = None

    def register_model(self, name: str, model, metadata: dict = None):
        """Register a new model version.

        Args:
            name: Model identifier
            model: Model object
            metadata: Additional metadata
        """
        self.models[name] = {
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        logger.info(f"Registered model: {name}")

    def get_model(self, name: str = None):
        """Get a specific model or current model.

        Args:
            name: Model name (if None, returns current)

        Returns:
            Model object
        """
        if name is None:
            if self.current_model is None:
                raise ValueError("No current model set")
            name = self.current_model

        if name not in self.models:
            raise ValueError(f"Model not found: {name}")

        return self.models[name]["model"]

    def set_current_model(self, name: str):
        """Set the current active model."""
        if name not in self.models:
            raise ValueError(f"Model not found: {name}")

        self.current_model = name
        logger.info(f"Current model set to: {name}")

    def list_models(self) -> list:
        """List all registered models."""
        return [
            {
                "name": name,
                "timestamp": data["timestamp"],
                "current": name == self.current_model,
            }
            for name, data in self.models.items()
        ]

    def remove_model(self, name: str):
        """Remove a model from registry."""
        if name in self.models:
            del self.models[name]
            if self.current_model == name:
                self.current_model = None
            logger.info(f"Removed model: {name}")
