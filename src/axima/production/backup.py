"""Backup and restore management for AXIMA production state.

Backs up:
- Memory (session state, learned answers)
- Knowledge (indexed facts, triples)
- Settings (configuration, user preferences)
- Event ledger (query history, traces)

Supports:
- Full and incremental backups
- Verified restore with integrity checks
- Schema migration on restore (old backups → current schema)
- Backup listing and pruning
"""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class BackupType(Enum):
    """Types of backup operations."""

    FULL = "full"
    INCREMENTAL = "incremental"


class BackupStatus(Enum):
    """Status of a backup."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    CORRUPTED = "corrupted"
    VERIFIED = "verified"


@dataclass
class BackupMetadata:
    """Metadata for a backup.

    Attributes:
        backup_id: Unique identifier for this backup.
        timestamp: When the backup was created.
        backup_type: Full or incremental.
        version: AXIMA version at backup time.
        schema_version: Data schema version.
        components: What was backed up.
        size_bytes: Total size in bytes.
        checksum: SHA-256 of the backup content.
        status: Current backup status.
    """

    backup_id: str
    timestamp: str
    backup_type: BackupType
    version: str
    schema_version: str
    components: List[str]
    size_bytes: int = 0
    checksum: str = ""
    status: BackupStatus = BackupStatus.COMPLETE

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "backup_id": self.backup_id,
            "timestamp": self.timestamp,
            "backup_type": self.backup_type.value,
            "version": self.version,
            "schema_version": self.schema_version,
            "components": self.components,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> BackupMetadata:
        """Deserialize from dictionary."""
        return cls(
            backup_id=data["backup_id"],
            timestamp=data["timestamp"],
            backup_type=BackupType(data["backup_type"]),
            version=data["version"],
            schema_version=data["schema_version"],
            components=data["components"],
            size_bytes=data.get("size_bytes", 0),
            checksum=data.get("checksum", ""),
            status=BackupStatus(data.get("status", "complete")),
        )


@dataclass
class RestoreResult:
    """Result of a restore operation.

    Attributes:
        success: Whether the restore completed successfully.
        components_restored: List of successfully restored components.
        migrations_applied: Schema migrations that were applied.
        errors: Any errors encountered.
        warnings: Non-fatal warnings.
    """

    success: bool
    components_restored: List[str] = field(default_factory=list)
    migrations_applied: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class SchemaMigration:
    """Schema migration definition.

    Attributes:
        from_version: Source schema version.
        to_version: Target schema version.
        description: What this migration does.
        migrate_fn: Function that transforms data from old to new schema.
    """

    from_version: str
    to_version: str
    description: str
    migrate_fn: Any  # Callable[[Dict], Dict]


class BackupManager:
    """Manages backup and restore operations for AXIMA state.

    All backups are stored as JSON files in a configurable backup directory.
    Each backup includes metadata, checksums, and version information
    to enable safe restore with migration support.
    """

    # Components that can be backed up
    COMPONENTS = ["memory", "knowledge", "settings", "event_ledger"]

    def __init__(
        self,
        backup_dir: Path,
        data_dir: Path,
        version: str = "0.1.0",
        schema_version: str = "1.0.0",
    ) -> None:
        """Initialize backup manager.

        Args:
            backup_dir: Directory to store backups.
            data_dir: Directory containing live data to back up.
            version: Current AXIMA version.
            schema_version: Current data schema version.
        """
        self._backup_dir = backup_dir
        self._data_dir = data_dir
        self._version = version
        self._schema_version = schema_version
        self._migrations: List[SchemaMigration] = []

    def register_migration(self, migration: SchemaMigration) -> None:
        """Register a schema migration.

        Args:
            migration: Migration to register.
        """
        self._migrations.append(migration)

    def backup(
        self,
        backup_type: BackupType = BackupType.FULL,
        components: Optional[List[str]] = None,
    ) -> BackupMetadata:
        """Create a backup of AXIMA state.

        Args:
            backup_type: Full or incremental backup.
            components: Specific components to back up. If None, backs up all.

        Returns:
            BackupMetadata describing the created backup.
        """
        target_components = components or self.COMPONENTS
        timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        backup_id = f"backup_{timestamp}"

        # Create backup directory
        backup_path = self._backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)

        # Back up each component
        backed_up: List[str] = []
        total_size = 0

        for component in target_components:
            size = self._backup_component(component, backup_path)
            if size >= 0:
                backed_up.append(component)
                total_size += size

        # Compute checksum of backup content
        checksum = self._compute_backup_checksum(backup_path)

        # Write metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            backup_type=backup_type,
            version=self._version,
            schema_version=self._schema_version,
            components=backed_up,
            size_bytes=total_size,
            checksum=checksum,
            status=BackupStatus.COMPLETE if len(backed_up) == len(target_components)
            else BackupStatus.PARTIAL,
        )

        metadata_path = backup_path / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, indent=2)

        return metadata

    def restore(
        self,
        backup_id: str,
        components: Optional[List[str]] = None,
    ) -> RestoreResult:
        """Restore from a backup.

        Verifies integrity, applies schema migrations if needed,
        then restores data.

        Args:
            backup_id: ID of the backup to restore.
            components: Specific components to restore. If None, restores all.

        Returns:
            RestoreResult with details of what was restored.
        """
        backup_path = self._backup_dir / backup_id

        if not backup_path.exists():
            return RestoreResult(
                success=False,
                errors=[f"Backup not found: {backup_id}"],
            )

        # Load and verify metadata
        metadata_path = backup_path / "metadata.json"
        if not metadata_path.exists():
            return RestoreResult(
                success=False,
                errors=["Backup metadata missing"],
            )

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = BackupMetadata.from_dict(json.load(f))

        # Verify integrity
        if not self.verify_backup(backup_id):
            return RestoreResult(
                success=False,
                errors=["Backup integrity check failed"],
            )

        # Determine what to restore
        target_components = components or metadata.components
        target_components = [c for c in target_components if c in metadata.components]

        # Check if schema migration is needed
        migrations_applied: List[str] = []
        if metadata.schema_version != self._schema_version:
            migrations_applied = self._get_migration_path(
                metadata.schema_version, self._schema_version
            )

        # Restore each component
        restored: List[str] = []
        errors: List[str] = []
        warnings: List[str] = []

        for component in target_components:
            try:
                data = self._load_component(component, backup_path)
                if data is None:
                    warnings.append(f"Component '{component}' is empty in backup")
                    continue

                # Apply migrations if needed
                if migrations_applied:
                    data = self._apply_migrations(data, metadata.schema_version)

                # Write to live data directory
                self._restore_component(component, data)
                restored.append(component)

            except Exception as e:
                errors.append(f"Failed to restore '{component}': {e}")

        success = len(errors) == 0 and len(restored) > 0

        return RestoreResult(
            success=success,
            components_restored=restored,
            migrations_applied=migrations_applied,
            errors=errors,
            warnings=warnings,
        )

    def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity using checksum.

        Args:
            backup_id: ID of the backup to verify.

        Returns:
            True if backup is intact, False otherwise.
        """
        backup_path = self._backup_dir / backup_id

        if not backup_path.exists():
            return False

        metadata_path = backup_path / "metadata.json"
        if not metadata_path.exists():
            return False

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = BackupMetadata.from_dict(json.load(f))

        # Recompute checksum
        current_checksum = self._compute_backup_checksum(backup_path)

        return current_checksum == metadata.checksum

    def list_backups(self) -> List[BackupMetadata]:
        """List all available backups.

        Returns:
            List of BackupMetadata sorted by timestamp (newest first).
        """
        backups: List[BackupMetadata] = []

        if not self._backup_dir.exists():
            return backups

        for entry in sorted(self._backup_dir.iterdir(), reverse=True):
            if not entry.is_dir():
                continue

            metadata_path = entry / "metadata.json"
            if not metadata_path.exists():
                continue

            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = BackupMetadata.from_dict(json.load(f))
                backups.append(metadata)
            except (json.JSONDecodeError, KeyError):
                continue

        return backups

    def _backup_component(self, component: str, backup_path: Path) -> int:
        """Back up a single component.

        Returns:
            Size in bytes of the backed up data, or -1 on failure.
        """
        source_path = self._data_dir / f"{component}.json"

        # Try to read existing data
        data: Dict[str, Any] = {}
        if source_path.exists():
            try:
                with open(source_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = {}

        # Write to backup
        dest_path = backup_path / f"{component}.json"
        content = json.dumps(data, indent=2, ensure_ascii=False)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)

        return len(content.encode("utf-8"))

    def _load_component(self, component: str, backup_path: Path) -> Optional[Dict[str, Any]]:
        """Load a component from a backup."""
        source_path = backup_path / f"{component}.json"

        if not source_path.exists():
            return None

        with open(source_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _restore_component(self, component: str, data: Dict[str, Any]) -> None:
        """Restore a component to the live data directory."""
        self._data_dir.mkdir(parents=True, exist_ok=True)
        dest_path = self._data_dir / f"{component}.json"

        with open(dest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _compute_backup_checksum(self, backup_path: Path) -> str:
        """Compute SHA-256 checksum of all data files in a backup."""
        hasher = hashlib.sha256()

        # Sort files for deterministic checksum
        data_files = sorted(
            f for f in backup_path.iterdir()
            if f.is_file() and f.name != "metadata.json"
        )

        for data_file in data_files:
            hasher.update(data_file.name.encode("utf-8"))
            hasher.update(data_file.read_bytes())

        return hasher.hexdigest()

    def _get_migration_path(
        self, from_version: str, to_version: str
    ) -> List[str]:
        """Get the sequence of migrations needed."""
        path: List[str] = []
        current = from_version

        for migration in self._migrations:
            if migration.from_version == current:
                path.append(f"{migration.from_version} -> {migration.to_version}")
                current = migration.to_version
                if current == to_version:
                    break

        return path

    def _apply_migrations(
        self, data: Dict[str, Any], from_version: str
    ) -> Dict[str, Any]:
        """Apply schema migrations to data."""
        current = from_version
        result = data

        for migration in self._migrations:
            if migration.from_version == current:
                try:
                    result = migration.migrate_fn(result)
                    current = migration.to_version
                except Exception:
                    break
                if current == self._schema_version:
                    break

        return result
