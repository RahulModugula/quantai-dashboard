"""Backup and recovery system."""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class BackupType(str, Enum):
    """Backup types."""

    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupMetadata:
    """Metadata for a backup."""

    def __init__(
        self,
        backup_id: str,
        backup_type: BackupType,
        timestamp: datetime,
        size_bytes: int,
        file_count: int,
    ):
        """Initialize backup metadata."""
        self.backup_id = backup_id
        self.backup_type = backup_type
        self.timestamp = timestamp
        self.size_bytes = size_bytes
        self.file_count = file_count

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "backup_id": self.backup_id,
            "backup_type": self.backup_type.value,
            "timestamp": self.timestamp.isoformat(),
            "size_bytes": self.size_bytes,
            "file_count": self.file_count,
        }


class BackupManager:
    """Manage system backups."""

    def __init__(self, backup_dir: str = "./backups"):
        """Initialize backup manager.

        Args:
            backup_dir: Directory for backup storage
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.backups: List[BackupMetadata] = []

    def create_backup(
        self,
        backup_type: BackupType = BackupType.FULL,
        description: str = None,
    ) -> BackupMetadata:
        """Create a new backup.

        Args:
            backup_type: Type of backup
            description: Backup description

        Returns:
            Backup metadata
        """
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_file = self.backup_dir / f"{backup_id}.tar.gz"

        # Create backup
        file_count = self._create_archive(backup_file)
        size_bytes = backup_file.stat().st_size if backup_file.exists() else 0

        metadata = BackupMetadata(
            backup_id,
            backup_type,
            datetime.now(),
            size_bytes,
            file_count,
        )

        self.backups.append(metadata)
        logger.info(f"Backup created: {backup_id} ({size_bytes} bytes, {file_count} files)")

        return metadata

    def _create_archive(self, backup_file: Path) -> int:
        """Create backup archive."""
        import tarfile
        import os

        file_count = 0

        try:
            with tarfile.open(backup_file, "w:gz") as tar:
                # Add data and config directories
                for directory in ["./data", "./config", "./src"]:
                    if os.path.exists(directory):
                        tar.add(directory, arcname=directory)
                        file_count += len([f for f in Path(directory).rglob("*")])
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

        return file_count

    def restore_backup(self, backup_id: str) -> bool:
        """Restore a backup.

        Args:
            backup_id: ID of backup to restore

        Returns:
            Whether restore was successful
        """
        backup_file = self.backup_dir / f"{backup_id}.tar.gz"

        if not backup_file.exists():
            logger.error(f"Backup not found: {backup_id}")
            return False

        try:
            import tarfile

            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(path="./")

            logger.info(f"Backup restored: {backup_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup.

        Args:
            backup_id: ID of backup to delete

        Returns:
            Whether deletion was successful
        """
        backup_file = self.backup_dir / f"{backup_id}.tar.gz"

        if not backup_file.exists():
            logger.error(f"Backup not found: {backup_id}")
            return False

        try:
            backup_file.unlink()
            self.backups = [b for b in self.backups if b.backup_id != backup_id]
            logger.info(f"Backup deleted: {backup_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False

    def list_backups(self) -> List[Dict]:
        """List all backups."""
        return [
            b.to_dict()
            for b in sorted(
                self.backups,
                key=lambda b: b.timestamp,
                reverse=True,
            )
        ]

    def get_backup_info(self, backup_id: str) -> Optional[Dict]:
        """Get information about a backup."""
        for backup in self.backups:
            if backup.backup_id == backup_id:
                return backup.to_dict()

        return None

    def get_total_backup_size(self) -> int:
        """Get total size of all backups."""
        return sum(b.size_bytes for b in self.backups)

    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """Remove old backups.

        Args:
            keep_count: Number of recent backups to keep

        Returns:
            Number of backups deleted
        """
        sorted_backups = sorted(
            self.backups,
            key=lambda b: b.timestamp,
            reverse=True,
        )

        to_delete = sorted_backups[keep_count:]
        deleted_count = 0

        for backup in to_delete:
            if self.delete_backup(backup.backup_id):
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old backups")
        return deleted_count

    def get_stats(self) -> dict:
        """Get backup statistics."""
        total_size = self.get_total_backup_size()

        return {
            "total_backups": len(self.backups),
            "total_size_bytes": total_size,
            "total_size_gb": round(total_size / (1024**3), 2),
            "oldest_backup": (self.backups[-1].timestamp.isoformat() if self.backups else None),
            "newest_backup": (self.backups[0].timestamp.isoformat() if self.backups else None),
        }


# Global backup manager
_manager = BackupManager()


def get_backup_manager() -> BackupManager:
    """Get global backup manager."""
    return _manager


def create_backup(backup_type: BackupType = BackupType.FULL) -> BackupMetadata:
    """Create a backup globally."""
    manager = get_backup_manager()
    return manager.create_backup(backup_type)


def restore_backup(backup_id: str) -> bool:
    """Restore a backup globally."""
    manager = get_backup_manager()
    return manager.restore_backup(backup_id)
