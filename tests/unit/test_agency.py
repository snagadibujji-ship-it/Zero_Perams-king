"""Unit tests for Phase R8: Agency — transactions, capabilities, repository engineer."""

import os
import tempfile
from datetime import datetime, timedelta

import pytest

from axima.agency.transactions import (
    AgencyTransaction,
    AuditEvent,
    AuthorizationError,
    BudgetExceededError,
    CapabilityScope,
    CapabilityToken,
    OperationType,
    TransactionState,
)
from axima.agency.capabilities import (
    CapabilityResult,
    FileCapability,
    GitCapability,
    NetworkCapability,
    ShellCapability,
)
from axima.agency.repository import (
    EditPlan,
    Patch,
    PatchStatus,
    RepositoryEngineer,
    RepositoryModel,
    VerificationResult,
)
from axima.agency.system_architecture import (
    ArchitectureCompiler,
    Constraint,
    EntityType,
    Interface,
    Invariant,
    Operation,
    Protocol,
    RelationshipType,
    Requirement,
    SemanticDiff,
    SystemArchitectureIR,
    SystemEntity,
    SystemRelation,
)


# ===========================================================================
# Capability Token Tests
# ===========================================================================

class TestCapabilityToken:
    """Tests for CapabilityToken."""

    def test_token_creation(self) -> None:
        token = CapabilityToken(
            scope=CapabilityScope(
                paths=["/tmp/test"],
                operations=[OperationType.READ, OperationType.WRITE],
            ),
            budget=10.0,
        )
        assert token.is_valid
        assert not token.is_expired
        assert token.remaining_budget == 10.0

    def test_token_expiry(self) -> None:
        token = CapabilityToken(
            expires_at=datetime.now() - timedelta(minutes=1),
            budget=10.0,
        )
        assert token.is_expired
        assert not token.is_valid

    def test_token_path_check(self) -> None:
        token = CapabilityToken(
            scope=CapabilityScope(paths=["/tmp/allowed", "/home/user"]),
            budget=10.0,
        )
        assert token.check_path("/tmp/allowed/file.txt")
        assert token.check_path("/home/user/docs")
        assert not token.check_path("/etc/passwd")

    def test_token_operation_check(self) -> None:
        token = CapabilityToken(
            scope=CapabilityScope(operations=[OperationType.READ]),
            budget=10.0,
        )
        assert token.check_operation(OperationType.READ)
        assert not token.check_operation(OperationType.DELETE)

    def test_token_network_default_deny(self) -> None:
        token = CapabilityToken(
            scope=CapabilityScope(network_destinations=[]),
            budget=10.0,
        )
        # Default deny for network
        assert not token.check_network("https://example.com")

    def test_token_network_allowed(self) -> None:
        token = CapabilityToken(
            scope=CapabilityScope(network_destinations=["https://api.example.com"]),
            budget=10.0,
        )
        assert token.check_network("https://api.example.com/v1/data")
        assert not token.check_network("https://evil.com")

    def test_token_budget_spending(self) -> None:
        token = CapabilityToken(budget=5.0)
        assert token.spend(3.0)
        assert token.remaining_budget == 2.0
        assert not token.spend(3.0)  # exceeds remaining
        assert token.remaining_budget == 2.0  # unchanged

    def test_token_revocation(self) -> None:
        token = CapabilityToken(budget=10.0)
        assert token.is_valid
        token.revoke()
        assert not token.is_valid


# ===========================================================================
# Agency Transaction Tests
# ===========================================================================

class TestAgencyTransaction:
    """Tests for AgencyTransaction."""

    def _make_token(self, budget: float = 100.0) -> CapabilityToken:
        return CapabilityToken(
            scope=CapabilityScope(
                paths=["/tmp"],
                operations=[OperationType.READ, OperationType.WRITE, OperationType.EXECUTE],
            ),
            budget=budget,
        )

    def test_transaction_lifecycle(self) -> None:
        token = self._make_token()
        tx = AgencyTransaction(token)

        tx.begin()
        assert tx.state == TransactionState.PENDING

        actions = [{"operation": "read", "target": "/tmp/file.txt", "cost": 1.0}]
        previews = tx.dry_run(actions)
        assert tx.state == TransactionState.DRY_RUN
        assert previews[0]["authorized"]

        assert tx.authorize(actions)
        assert tx.state == TransactionState.AUTHORIZED

        results = tx.execute()
        assert len(results) == 1

        assert tx.commit()
        assert tx.state == TransactionState.COMMITTED

    def test_transaction_authorization_denied(self) -> None:
        token = CapabilityToken(
            scope=CapabilityScope(
                paths=["/tmp"],
                operations=[OperationType.READ],  # only read
            ),
            budget=10.0,
        )
        tx = AgencyTransaction(token)
        tx.begin()

        # Try to write - should be denied
        actions = [{"operation": "write", "target": "/tmp/file.txt", "cost": 1.0}]
        assert not tx.authorize(actions)
        assert tx.state == TransactionState.FAILED

    def test_transaction_path_denied(self) -> None:
        token = self._make_token()
        tx = AgencyTransaction(token)
        tx.begin()

        actions = [{"operation": "read", "target": "/etc/secret", "cost": 1.0}]
        assert not tx.authorize(actions)

    def test_transaction_rollback(self) -> None:
        token = self._make_token()
        tx = AgencyTransaction(token)
        tx.begin()

        actions = [{"operation": "read", "target": "/tmp/file.txt", "cost": 1.0}]
        tx.authorize(actions)
        tx.execute()

        assert tx.rollback()
        assert tx.state == TransactionState.ROLLED_BACK

    def test_transaction_budget_exceeded(self) -> None:
        token = self._make_token(budget=1.0)
        tx = AgencyTransaction(token)
        tx.begin()

        actions = [{"operation": "read", "target": "/tmp/file.txt", "cost": 5.0}]
        tx.authorize(actions)

        with pytest.raises(BudgetExceededError):
            tx.execute()

    def test_transaction_expired_token(self) -> None:
        token = CapabilityToken(
            expires_at=datetime.now() - timedelta(minutes=1),
            budget=10.0,
        )
        tx = AgencyTransaction(token)

        with pytest.raises(AuthorizationError):
            tx.begin()

    def test_transaction_audit_log(self) -> None:
        token = self._make_token()
        tx = AgencyTransaction(token)
        tx.begin()

        actions = [{"operation": "read", "target": "/tmp/file.txt", "cost": 1.0}]
        tx.authorize(actions)
        tx.execute()
        tx.commit()

        log = tx.audit_log
        assert len(log) >= 3  # begin, authorize, execute, commit
        assert all(isinstance(e, AuditEvent) for e in log)

    def test_transaction_inspect(self) -> None:
        token = self._make_token()
        tx = AgencyTransaction(token)
        tx.begin()

        info = tx.inspect()
        assert info["state"] == "PENDING"
        assert info["token_valid"] is True


# ===========================================================================
# File Capability Tests
# ===========================================================================

class TestFileCapability:
    """Tests for FileCapability."""

    def test_read_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, prefix="/tmp/") as f:
            f.write("hello world")
            path = f.name

        try:
            token = CapabilityToken(
                scope=CapabilityScope(paths=["/tmp"], operations=[OperationType.READ]),
                budget=10.0,
            )
            fc = FileCapability(token)
            result = fc.read(path)
            assert result.success
            assert result.data == "hello world"
        finally:
            os.unlink(path)

    def test_write_file(self) -> None:
        path = f"/tmp/test_write_{os.getpid()}.txt"
        token = CapabilityToken(
            scope=CapabilityScope(paths=["/tmp"], operations=[OperationType.WRITE]),
            budget=10.0,
        )
        fc = FileCapability(token)
        result = fc.write(path, "test content")
        assert result.success

        try:
            with open(path) as f:
                assert f.read() == "test content"
        finally:
            os.unlink(path)

    def test_read_outside_scope(self) -> None:
        token = CapabilityToken(
            scope=CapabilityScope(paths=["/tmp/allowed"], operations=[OperationType.READ]),
            budget=10.0,
        )
        fc = FileCapability(token)
        result = fc.read("/etc/passwd")
        assert not result.success
        assert "not in scope" in (result.error or "")

    def test_write_not_allowed(self) -> None:
        token = CapabilityToken(
            scope=CapabilityScope(paths=["/tmp"], operations=[OperationType.READ]),  # no WRITE
            budget=10.0,
        )
        fc = FileCapability(token)
        result = fc.write("/tmp/test.txt", "data")
        assert not result.success
        assert "not allowed" in (result.error or "")


# ===========================================================================
# Shell Capability Tests
# ===========================================================================

class TestShellCapability:
    """Tests for ShellCapability."""

    def test_execute_command(self) -> None:
        token = CapabilityToken(
            scope=CapabilityScope(paths=["/tmp"], operations=[OperationType.EXECUTE]),
            budget=10.0,
        )
        sc = ShellCapability(token)
        result = sc.execute(["echo", "hello"])
        assert result.success
        assert "hello" in result.data["stdout"]

    def test_execute_denied(self) -> None:
        token = CapabilityToken(
            scope=CapabilityScope(paths=["/tmp"], operations=[OperationType.READ]),  # no EXECUTE
            budget=10.0,
        )
        sc = ShellCapability(token)
        result = sc.execute(["echo", "hello"])
        assert not result.success

    def test_execute_timeout(self) -> None:
        token = CapabilityToken(
            scope=CapabilityScope(operations=[OperationType.EXECUTE]),
            budget=10.0,
        )
        sc = ShellCapability(token, timeout=0.1)
        result = sc.execute(["sleep", "10"])
        assert not result.success
        assert "timed out" in (result.error or "")


# ===========================================================================
# Repository Engineer Tests
# ===========================================================================

class TestRepositoryEngineer:
    """Tests for RepositoryEngineer."""

    def setup_method(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        # Create a minimal Python project
        os.makedirs(os.path.join(self._tmpdir, "src"))
        with open(os.path.join(self._tmpdir, "src", "main.py"), "w") as f:
            f.write('''"""Main module."""

class MyService:
    """A service."""

    def handle(self, request):
        """Handle a request."""
        return {"status": "ok"}


def helper():
    """A helper function."""
    return 42
''')
        with open(os.path.join(self._tmpdir, "pyproject.toml"), "w") as f:
            f.write('[project]\nname = "test"\nversion = "0.1.0"\n')

    def teardown_method(self) -> None:
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_index_repo(self) -> None:
        re = RepositoryEngineer(self._tmpdir)
        model = re.index_repo()
        assert isinstance(model, RepositoryModel)
        assert model.root_path == self._tmpdir
        assert "pyproject.toml" in model.manifest.get("file", "")
        assert len(model.ast_index) > 0

    def test_symbols_extracted(self) -> None:
        re = RepositoryEngineer(self._tmpdir)
        model = re.index_repo()
        # Should find MyService and helper
        symbol_names = [s.name for s in model.symbols.values()]
        assert "MyService" in symbol_names
        assert "helper" in symbol_names

    def test_plan_edit(self) -> None:
        re = RepositoryEngineer(self._tmpdir)
        re.index_repo()
        plan = re.plan_edit(
            description="Add new endpoint",
            changes={"src/main.py": "# modified content\n"},
        )
        assert isinstance(plan, EditPlan)
        assert len(plan.patches) == 1
        assert "src/main.py" in plan.affected_files

    def test_apply_and_rollback_patch(self) -> None:
        re = RepositoryEngineer(self._tmpdir)
        new_file = "src/new_module.py"
        patch = Patch(
            file_path=new_file,
            new_content="# New module\nprint('hello')\n",
            description="Add new module",
        )

        assert re.apply_patch(patch)
        assert patch.status == PatchStatus.APPLIED
        full_path = os.path.join(self._tmpdir, new_file)
        assert os.path.exists(full_path)

        # Rollback
        assert re.rollback(patch)
        assert not os.path.exists(full_path)
        assert patch.status == PatchStatus.ROLLED_BACK

    def test_verify_patch_valid_python(self) -> None:
        re = RepositoryEngineer(self._tmpdir)
        patch = Patch(
            file_path="src/valid.py",
            new_content="def foo():\n    return 42\n",
        )
        result = re.verify_patch(patch)
        assert result.success
        assert len(result.errors) == 0

    def test_verify_patch_invalid_python(self) -> None:
        re = RepositoryEngineer(self._tmpdir)
        patch = Patch(
            file_path="src/invalid.py",
            new_content="def foo(\n    return 42\n",  # syntax error
        )
        result = re.verify_patch(patch)
        assert not result.success
        assert len(result.errors) > 0
        assert "Syntax error" in result.errors[0]


# ===========================================================================
# System Architecture Tests
# ===========================================================================

class TestSystemArchitectureIR:
    """Tests for SystemArchitectureIR."""

    def test_create_ir(self) -> None:
        ir = SystemArchitectureIR(
            name="test_system",
            entities=[
                SystemEntity(name="API", type=EntityType.SERVICE),
                SystemEntity(name="DB", type=EntityType.DATABASE),
            ],
            relations=[
                SystemRelation(source="API", target="DB", type=RelationshipType.READS),
            ],
        )
        assert len(ir.entities) == 2
        assert len(ir.relations) == 1
        assert ir.get_entity("API") is not None
        assert ir.get_entity("NonExistent") is None

    def test_get_relations(self) -> None:
        ir = SystemArchitectureIR(
            entities=[
                SystemEntity(name="A", type=EntityType.SERVICE),
                SystemEntity(name="B", type=EntityType.SERVICE),
                SystemEntity(name="C", type=EntityType.DATABASE),
            ],
            relations=[
                SystemRelation(source="A", target="B", type=RelationshipType.CALLS),
                SystemRelation(source="A", target="C", type=RelationshipType.WRITES),
                SystemRelation(source="B", target="C", type=RelationshipType.READS),
            ],
        )
        from_a = ir.get_relations_from("A")
        assert len(from_a) == 2
        to_c = ir.get_relations_to("C")
        assert len(to_c) == 2


class TestArchitectureCompiler:
    """Tests for ArchitectureCompiler."""

    def test_from_requirements(self) -> None:
        compiler = ArchitectureCompiler()
        reqs = [
            Requirement(id="R1", description="User can log in", type="functional",
                       traces_to=["AuthService", "UserDB"]),
            Requirement(id="R2", description="Response time < 200ms", type="non-functional"),
            Requirement(id="R3", description="All data encrypted at rest", type="constraint"),
        ]
        ir = compiler.from_requirements(reqs)
        assert isinstance(ir, SystemArchitectureIR)
        entity_names = ir.entity_names()
        assert "AuthService" in entity_names
        assert "UserDB" in entity_names
        assert len(ir.constraints) == 1
        assert len(ir.invariants) == 1

    def test_from_code(self) -> None:
        tmpdir = tempfile.mkdtemp()
        try:
            with open(os.path.join(tmpdir, "service.py"), "w") as f:
                f.write('''class OrderService:
    """Handles orders."""
    def create_order(self):
        pass
    def get_order(self):
        pass

class PaymentGateway:
    """Handles payments."""
    def charge(self):
        pass
''')
            compiler = ArchitectureCompiler()
            ir = compiler.from_code(tmpdir)
            entity_names = ir.entity_names()
            assert "OrderService" in entity_names
            assert "PaymentGateway" in entity_names
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_to_code(self) -> None:
        ir = SystemArchitectureIR(
            entities=[
                SystemEntity(
                    name="UserService",
                    type=EntityType.SERVICE,
                    interfaces=[Interface(name="user_api", methods=["create_user", "get_user"])],
                ),
            ],
        )
        compiler = ArchitectureCompiler()
        generated = compiler.to_code(ir, "/tmp/gen")
        assert len(generated) == 1
        code = list(generated.values())[0]
        assert "class Userservice" in code or "class UserService" in code
        assert "create_user" in code
        assert "get_user" in code

    def test_semantic_diff(self) -> None:
        old_ir = SystemArchitectureIR(
            entities=[
                SystemEntity(name="A", type=EntityType.SERVICE),
                SystemEntity(name="B", type=EntityType.SERVICE),
            ],
            relations=[
                SystemRelation(source="A", target="B", type=RelationshipType.CALLS),
            ],
        )
        new_ir = SystemArchitectureIR(
            entities=[
                SystemEntity(name="A", type=EntityType.SERVICE),
                SystemEntity(name="C", type=EntityType.DATABASE),
            ],
            relations=[
                SystemRelation(source="A", target="C", type=RelationshipType.WRITES),
            ],
        )
        compiler = ArchitectureCompiler()
        diff = compiler.semantic_diff(old_ir, new_ir)
        assert "C" in diff.added_entities
        assert "B" in diff.removed_entities
        assert ("A", "C") in diff.added_relations
        assert ("A", "B") in diff.removed_relations
        assert diff.has_breaking_changes

    def test_semantic_diff_empty(self) -> None:
        ir = SystemArchitectureIR(
            entities=[SystemEntity(name="X", type=EntityType.SERVICE)],
        )
        compiler = ArchitectureCompiler()
        diff = compiler.semantic_diff(ir, ir)
        assert diff.is_empty
