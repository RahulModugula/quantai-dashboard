import json
import logging
from datetime import datetime
from pathlib import Path

import joblib

logger = logging.getLogger(__name__)

REGISTRY_DIR = Path("models/registry")


def save_model(
    model,
    metadata: dict,
    registry_dir: Path | str = REGISTRY_DIR,
) -> str:
    """Save model with joblib and write metadata JSON alongside it."""
    registry_dir = Path(registry_dir)
    registry_dir.mkdir(parents=True, exist_ok=True)

    version_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = registry_dir / f"model_{version_id}.joblib"
    meta_path = registry_dir / f"model_{version_id}_meta.json"

    joblib.dump(model, model_path)

    metadata.update(
        {
            "version_id": version_id,
            "saved_at": datetime.now().isoformat(),
            "model_path": str(model_path),
        }
    )

    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    logger.info(f"Saved model version {version_id} to {model_path}")
    return version_id


def load_model(version_id: str | None = None, registry_dir: Path | str = REGISTRY_DIR):
    """Load a model by version ID, or the latest if not specified."""
    registry_dir = Path(registry_dir)

    if version_id:
        model_path = registry_dir / f"model_{version_id}.joblib"
    else:
        # Find the latest model
        model_files = sorted(registry_dir.glob("model_*.joblib"))
        if not model_files:
            raise FileNotFoundError("No models found in registry")
        model_path = model_files[-1]

    model = joblib.load(model_path)
    logger.info(f"Loaded model from {model_path}")
    return model


def load_metadata(version_id: str | None = None, registry_dir: Path | str = REGISTRY_DIR) -> dict:
    """Load metadata for a model version."""
    registry_dir = Path(registry_dir)

    if version_id:
        meta_path = registry_dir / f"model_{version_id}_meta.json"
    else:
        meta_files = sorted(registry_dir.glob("model_*_meta.json"))
        if not meta_files:
            raise FileNotFoundError("No model metadata found")
        meta_path = meta_files[-1]

    with open(meta_path) as f:
        return json.load(f)


def list_models(registry_dir: Path | str = REGISTRY_DIR) -> list[dict]:
    """List all model versions with their metadata."""
    registry_dir = Path(registry_dir)
    models = []
    for meta_path in sorted(registry_dir.glob("model_*_meta.json")):
        with open(meta_path) as f:
            models.append(json.load(f))
    return models
