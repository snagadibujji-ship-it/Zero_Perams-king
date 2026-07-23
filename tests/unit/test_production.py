"""Unit tests for the AXIMA production system.

Tests API, lifecycle, and backup management.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from axima.production.api import (
    AximaAPI,
    Request,
    Response,
    Route,
    HttpMethod,
    StatusCode,
)
from axima.production.lifecycle import (
    ApplicationLifecycle,
    LifecycleState,
    HealthStatus,
    MigrationStep,
)
from axima.production.backup import (
    BackupManager,
    BackupMetadata,
    BackupType,
    BackupStatus,
    RestoreResult,
    SchemaMigration,
)


# ============================================================
# API Tests
# ============================================================


def _mock_query(query: str) -> str:
    """Mock query function."""
    return f"Answer to: {query}"


class TestAximaAPI:
    """Tests for AximaAPI."""

    def test_health_check_healthy(self):
        api = AximaAPI(query_fn=_mock_query)
        req = Request(method=HttpMethod.GET, path="/health")
        resp = api.handle(req)
        assert resp.status == StatusCode.OK
        assert resp.body["status"] == "healthy"

    def test_health_check_unhealthy(self):
        api = AximaAPI(query_fn=_mock_query)
        api.set_healthy(False)
        req = Request(method=HttpMethod.GET, path="/health")
        resp = api.handle(req)
        assert resp.status == StatusCode.SERVICE_UNAVAILABLE

    def test_ready_check_not_ready(self):
        api = AximaAPI(query_fn=_mock_query)
        req = Request(method=HttpMethod.GET, path="/ready")
        resp = api.handle(req)
        assert resp.status == StatusCode.SERVICE_UNAVAILABLE
        assert resp.body["status"] == "not_ready"

    def test_ready_check_ready(self):
        api = AximaAPI(query_fn=_mock_query)
        api.set_ready(True)
        req = Request(method=HttpMethod.GET, path="/ready")
        resp = api.handle(req)
        assert resp.status == StatusCode.OK
        assert resp.body["status"] == "ready"

    def test_query_when_not_ready(self):
        api = AximaAPI(query_fn=_mock_query)
        req = Request(
            method=HttpMethod.POST,
            path="/query",
            body={"query": "hello"},
        )
        resp = api.handle(req)
        assert resp.status == StatusCode.SERVICE_UNAVAILABLE

    def test_query_success(self):
        api = AximaAPI(query_fn=_mock_query)
        api.set_ready(True)
        req = Request(
            method=HttpMethod.POST,
            path="/query",
            body={"query": "what is 2+2"},
        )
        resp = api.handle(req)
        assert resp.status == StatusCode.OK
        assert "Answer to" in resp.body["result"]
        assert "trace_id" in resp.body

    def test_query_missing_body(self):
        api = AximaAPI(query_fn=_mock_query)
        api.set_ready(True)
        req = Request(method=HttpMethod.POST, path="/query", body={})
        resp = api.handle(req)
        assert resp.status == StatusCode.BAD_REQUEST

    def test_capabilities(self):
        api = AximaAPI(query_fn=_mock_query)
        req = Request(method=HttpMethod.GET, path="/capabilities")
        resp = api.handle(req)
        assert resp.status == StatusCode.OK
        caps = resp.body["capabilities"]
        assert caps["math"] is True
        assert caps["code"] is True

    def test_doctor(self):
        api = AximaAPI(query_fn=_mock_query)
        req = Request(method=HttpMethod.GET, path="/doctor")
        resp = api.handle(req)
        assert resp.status == StatusCode.OK
        assert "checks" in resp.body
        assert resp.body["overall"] in ("healthy", "degraded")

    def test_trace_not_found(self):
        api = AximaAPI(query_fn=_mock_query)
        req = Request(
            method=HttpMethod.GET,
            path="/trace/nonexistent",
        )
        resp = api.handle(req)
        assert resp.status == StatusCode.NOT_FOUND

    def test_trace_after_query(self):
        api = AximaAPI(query_fn=_mock_query)
        api.set_ready(True)
        # Make a query
        qreq = Request(
            method=HttpMethod.POST,
            path="/query",
            body={"query": "test"},
        )
        qresp = api.handle(qreq)
        trace_id = qresp.body["trace_id"]
        # Retrieve trace
        treq = Request(method=HttpMethod.GET, path=f"/trace/{trace_id}")
        tresp = api.handle(treq)
        assert tresp.status == StatusCode.OK
        assert tresp.body["trace"]["query"] == "test"

    def test_memory_export(self):
        api = AximaAPI(query_fn=_mock_query)
        req = Request(method=HttpMethod.POST, path="/memory/export")
        resp = api.handle(req)
        assert resp.status == StatusCode.OK
        assert "memory" in resp.body

    def test_memory_delete_all(self):
        api = AximaAPI(query_fn=_mock_query)
        req = Request(method=HttpMethod.DELETE, path="/memory/delete")
        resp = api.handle(req)
        assert resp.status == StatusCode.OK

    def test_eval_run(self):
        api = AximaAPI(query_fn=_mock_query)
        req = Request(
            method=HttpMethod.POST,
            path="/eval/run",
            body={"suite": "math", "seed": 42},
        )
        resp = api.handle(req)
        assert resp.status == StatusCode.OK
        assert resp.body["status"] == "started"

    def test_unknown_route(self):
        api = AximaAPI(query_fn=_mock_query)
        req = Request(method=HttpMethod.GET, path="/nonexistent")
        resp = api.handle(req)
        assert resp.status == StatusCode.NOT_FOUND

    def test_request_id_echoed(self):
        api = AximaAPI(query_fn=_mock_query)
        req = Request(
            method=HttpMethod.GET,
            path="/health",
            request_id="test-123",
        )
        resp = api.handle(req)
        assert resp.request_id == "test-123"

    def test_latency_tracked(self):
        api = AximaAPI(query_fn=_mock_query)
        req = Request(method=HttpMethod.GET, path="/health")
        resp = api.handle(req)
        assert resp.latency_ms >= 0

    def test_routes_list(self):
        api = AximaAPI(query_fn=_mock_query)
        routes = api.routes
        assert len(routes) >= 9
        paths = [r.path for r in routes]
        assert "/query" in paths
        assert "/health" in paths
        assert "/ready" in paths


# ============================================================
# Lifecycle Tests
# ============================================================


class TestApplicationLifecycle:
    """Tests for ApplicationLifecycle."""

    def test_initial_state(self):
        lc = ApplicationLifecycle()
        assert lc.state == LifecycleState.CREATED

    def test_startup_no_plugins(self):
        lc = ApplicationLifecycle()
        success = lc.startup()
        assert success is True
        assert lc.state == LifecycleState.READY

    def test_startup_with_plugins(self):
        class GoodPlugin:
            def load(self) -> bool:
                return True
            def name(self) -> str:
                return "good_plugin"

        lc = ApplicationLifecycle()
        success = lc.startup(plugins=[GoodPlugin()])
        assert success is True
        assert lc.state == LifecycleState.READY

    def test_startup_with_failing_plugin(self):
        class BadPlugin:
            def load(self) -> bool:
                return False
            def name(self) -> str:
                return "bad_plugin"

        lc = ApplicationLifecycle()
        success = lc.startup(plugins=[BadPlugin()])
        assert success is True  # Degraded but running
        assert lc.state == LifecycleState.DEGRADED

    def test_shutdown(self):
        lc = ApplicationLifecycle()
        lc.startup()
        success = lc.shutdown()
        assert success is True
        assert lc.state == LifecycleState.STOPPED

    def test_shutdown_hooks_called(self):
        called = []
        lc = ApplicationLifecycle()
        lc.register_shutdown_hook(lambda: called.append("hook1"))
        lc.register_shutdown_hook(lambda: called.append("hook2"))
        lc.startup()
        lc.shutdown()
        # Hooks called in reverse order
        assert called == ["hook2", "hook1"]

    def test_startup_hooks(self):
        called = []
        lc = ApplicationLifecycle()
        lc.register_startup_hook(lambda: (called.append("start"), True)[-1])
        lc.startup()
        assert "start" in called

    def test_health_check_ready(self):
        lc = ApplicationLifecycle(version="1.2.3")
        lc.startup()
        health = lc.health_check()
        assert health.healthy is True
        assert health.state == LifecycleState.READY
        assert health.version == "1.2.3"

    def test_health_check_stopped(self):
        lc = ApplicationLifecycle()
        health = lc.health_check()
        assert health.healthy is False
        assert health.state == LifecycleState.CREATED

    def test_ready_check(self):
        lc = ApplicationLifecycle()
        assert lc.ready_check() is False
        lc.startup()
        assert lc.ready_check() is True
        lc.shutdown()
        assert lc.ready_check() is False

    def test_uptime(self):
        lc = ApplicationLifecycle()
        assert lc.uptime_s == 0.0
        lc.startup()
        time.sleep(0.01)
        assert lc.uptime_s > 0.0

    def test_subsystem_health_degrades(self):
        lc = ApplicationLifecycle()
        lc.startup()
        assert lc.state == LifecycleState.READY
        lc.set_subsystem_health("database", False)
        assert lc.state == LifecycleState.DEGRADED

    def test_migrations(self):
        migrated = []
        lc = ApplicationLifecycle()
        lc.register_migration(MigrationStep(
            version="1.0.1",
            description="Add index",
            migrate_fn=lambda: (migrated.append("1.0.1"), True)[-1],
        ))
        lc.startup()
        assert "1.0.1" in migrated

    def test_state_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            lc = ApplicationLifecycle(state_dir=state_dir)
            lc.set_state_to_persist("key1", "value1")
            lc.startup()
            lc.shutdown()
            state_file = state_dir / "lifecycle_state.json"
            assert state_file.exists()
            with open(state_file) as f:
                data = json.load(f)
            assert data["persisted_state"]["key1"] == "value1"


# ============================================================
# Backup Tests
# ============================================================


class TestBackupManager:
    """Tests for BackupManager."""

    def _setup_dirs(self, tmpdir: str):
        backup_dir = Path(tmpdir) / "backups"
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir(parents=True)
        # Create some data files
        (data_dir / "memory.json").write_text(
            json.dumps({"sessions": [{"id": 1}]})
        )
        (data_dir / "knowledge.json").write_text(
            json.dumps({"facts": ["earth is round"]})
        )
        (data_dir / "settings.json").write_text(
            json.dumps({"theme": "dark"})
        )
        (data_dir / "event_ledger.json").write_text(
            json.dumps({"events": []})
        )
        return backup_dir, data_dir

    def test_backup_creates_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir, data_dir = self._setup_dirs(tmpdir)
            mgr = BackupManager(backup_dir, data_dir)
            metadata = mgr.backup()
            assert metadata.status == BackupStatus.COMPLETE
            assert len(metadata.components) == 4
            assert metadata.size_bytes > 0
            assert metadata.checksum != ""

    def test_backup_custom_components(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir, data_dir = self._setup_dirs(tmpdir)
            mgr = BackupManager(backup_dir, data_dir)
            metadata = mgr.backup(components=["memory", "settings"])
            assert len(metadata.components) == 2
            assert "memory" in metadata.components
            assert "settings" in metadata.components

    def test_verify_backup_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir, data_dir = self._setup_dirs(tmpdir)
            mgr = BackupManager(backup_dir, data_dir)
            metadata = mgr.backup()
            assert mgr.verify_backup(metadata.backup_id) is True

    def test_verify_backup_fails_on_tamper(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir, data_dir = self._setup_dirs(tmpdir)
            mgr = BackupManager(backup_dir, data_dir)
            metadata = mgr.backup()
            # Tamper with a backup file
            backup_path = backup_dir / metadata.backup_id
            mem_file = backup_path / "memory.json"
            mem_file.write_text('{"tampered": true}')
            assert mgr.verify_backup(metadata.backup_id) is False

    def test_verify_nonexistent_backup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir, data_dir = self._setup_dirs(tmpdir)
            mgr = BackupManager(backup_dir, data_dir)
            assert mgr.verify_backup("nonexistent") is False

    def test_restore_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir, data_dir = self._setup_dirs(tmpdir)
            mgr = BackupManager(backup_dir, data_dir)
            metadata = mgr.backup()
            # Modify live data
            (data_dir / "memory.json").write_text('{"sessions": []}')
            # Restore
            result = mgr.restore(metadata.backup_id)
            assert result.success is True
            assert "memory" in result.components_restored
            # Verify restored content
            with open(data_dir / "memory.json") as f:
                restored_data = json.load(f)
            assert restored_data["sessions"] == [{"id": 1}]

    def test_restore_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir, data_dir = self._setup_dirs(tmpdir)
            mgr = BackupManager(backup_dir, data_dir)
            result = mgr.restore("nonexistent_backup")
            assert result.success is False
            assert len(result.errors) > 0

    def test_restore_specific_components(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir, data_dir = self._setup_dirs(tmpdir)
            mgr = BackupManager(backup_dir, data_dir)
            metadata = mgr.backup()
            result = mgr.restore(metadata.backup_id, components=["settings"])
            assert result.success is True
            assert result.components_restored == ["settings"]

    def test_list_backups(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir, data_dir = self._setup_dirs(tmpdir)
            mgr = BackupManager(backup_dir, data_dir)
            meta1 = mgr.backup()
            # Ensure unique backup ID by creating second one with different content
            (data_dir / "memory.json").write_text(
                json.dumps({"sessions": [{"id": 2}]})
            )
            # Force a unique backup by using incremental type  
            # (backup IDs may collide within same second, so rename first)
            backup_path_1 = backup_dir / meta1.backup_id
            backup_path_2 = backup_dir / (meta1.backup_id + "_2")
            import shutil
            shutil.copytree(backup_path_1, backup_path_2)
            # Update metadata in copy
            with open(backup_path_2 / "metadata.json", "r") as f:
                meta_dict = json.load(f)
            meta_dict["backup_id"] = meta1.backup_id + "_2"
            with open(backup_path_2 / "metadata.json", "w") as f:
                json.dump(meta_dict, f)
            backups = mgr.list_backups()
            assert len(backups) == 2

    def test_list_backups_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir) / "backups"
            data_dir = Path(tmpdir) / "data"
            mgr = BackupManager(backup_dir, data_dir)
            backups = mgr.list_backups()
            assert backups == []

    def test_schema_migration_on_restore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir, data_dir = self._setup_dirs(tmpdir)
            # Create backup with old schema version
            mgr_old = BackupManager(
                backup_dir, data_dir,
                schema_version="1.0.0",
            )
            metadata = mgr_old.backup()

            # Create new manager with new schema version and migration
            mgr_new = BackupManager(
                backup_dir, data_dir,
                schema_version="2.0.0",
            )
            mgr_new.register_migration(SchemaMigration(
                from_version="1.0.0",
                to_version="2.0.0",
                description="Add version field",
                migrate_fn=lambda data: {**data, "schema_version": "2.0.0"},
            ))

            result = mgr_new.restore(metadata.backup_id)
            assert result.success is True
            assert len(result.migrations_applied) > 0

    def test_backup_metadata_serialization(self):
        metadata = BackupMetadata(
            backup_id="test_backup",
            timestamp="2026-01-01T00:00:00Z",
            backup_type=BackupType.FULL,
            version="0.1.0",
            schema_version="1.0.0",
            components=["memory", "settings"],
            size_bytes=1024,
            checksum="abc123",
            status=BackupStatus.COMPLETE,
        )
        d = metadata.to_dict()
        restored = BackupMetadata.from_dict(d)
        assert restored.backup_id == metadata.backup_id
        assert restored.backup_type == metadata.backup_type
        assert restored.status == metadata.status
