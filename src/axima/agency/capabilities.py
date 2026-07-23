"""Agency Capabilities — file, shell, git, network operations with token enforcement.

Every capability checks the CapabilityToken before executing.
"""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from axima.agency.transactions import (
    AuditEvent,
    AuthorizationError,
    BudgetExceededError,
    CapabilityToken,
    OperationType,
)


@dataclass
class CapabilityResult:
    """Result from a capability operation."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    audit: Optional[AuditEvent] = None
    cost: float = 0.0


class FileCapability:
    """File operations scoped by CapabilityToken.

    All operations validate path scope and operation type before executing.
    """

    def __init__(self, token: CapabilityToken) -> None:
        self._token = token
        self._audit_log: List[AuditEvent] = []

    @property
    def audit_log(self) -> List[AuditEvent]:
        return list(self._audit_log)

    def read(self, path: str) -> CapabilityResult:
        """Read a file within the token's allowed paths."""
        if not self._token.is_valid:
            return self._denied("read", path, "Token invalid")
        if not self._token.check_operation(OperationType.READ):
            return self._denied("read", path, "READ operation not allowed")
        if not self._token.check_path(path):
            return self._denied("read", path, f"Path not in scope: {path}")

        cost = 0.1
        if not self._token.spend(cost):
            return self._denied("read", path, "Budget exceeded")

        try:
            abs_path = os.path.abspath(path)
            if not os.path.exists(abs_path):
                return self._failure("read", path, f"File not found: {path}")
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return self._success("read", path, content, cost)
        except OSError as exc:
            return self._failure("read", path, str(exc))

    def write(self, path: str, content: str) -> CapabilityResult:
        """Write content to a file within the token's allowed paths."""
        if not self._token.is_valid:
            return self._denied("write", path, "Token invalid")
        if not self._token.check_operation(OperationType.WRITE):
            return self._denied("write", path, "WRITE operation not allowed")
        if not self._token.check_path(path):
            return self._denied("write", path, f"Path not in scope: {path}")

        cost = 0.5
        if not self._token.spend(cost):
            return self._denied("write", path, "Budget exceeded")

        try:
            abs_path = os.path.abspath(path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            return self._success("write", path, len(content), cost)
        except OSError as exc:
            return self._failure("write", path, str(exc))

    def delete(self, path: str) -> CapabilityResult:
        """Delete a file within the token's allowed paths."""
        if not self._token.is_valid:
            return self._denied("delete", path, "Token invalid")
        if not self._token.check_operation(OperationType.DELETE):
            return self._denied("delete", path, "DELETE operation not allowed")
        if not self._token.check_path(path):
            return self._denied("delete", path, f"Path not in scope: {path}")

        cost = 1.0
        if not self._token.spend(cost):
            return self._denied("delete", path, "Budget exceeded")

        try:
            abs_path = os.path.abspath(path)
            if not os.path.exists(abs_path):
                return self._failure("delete", path, f"File not found: {path}")
            os.remove(abs_path)
            return self._success("delete", path, True, cost)
        except OSError as exc:
            return self._failure("delete", path, str(exc))

    def _success(self, op: str, target: str, data: Any, cost: float) -> CapabilityResult:
        audit = AuditEvent(
            token_id=self._token.token_id, operation=op,
            target=target, result="success", success=True,
        )
        self._audit_log.append(audit)
        return CapabilityResult(success=True, data=data, audit=audit, cost=cost)

    def _failure(self, op: str, target: str, error: str) -> CapabilityResult:
        audit = AuditEvent(
            token_id=self._token.token_id, operation=op,
            target=target, result="failure", success=False, error=error,
        )
        self._audit_log.append(audit)
        return CapabilityResult(success=False, error=error, audit=audit)

    def _denied(self, op: str, target: str, reason: str) -> CapabilityResult:
        audit = AuditEvent(
            token_id=self._token.token_id, operation=op,
            target=target, result="denied", success=False, error=reason,
        )
        self._audit_log.append(audit)
        return CapabilityResult(success=False, error=reason, audit=audit)


class ShellCapability:
    """Shell command execution with timeout and output limits.

    Enforces EXECUTE operation type and budget.
    """

    def __init__(
        self,
        token: CapabilityToken,
        timeout: float = 30.0,
        max_output_bytes: int = 1_000_000,
    ) -> None:
        self._token = token
        self._timeout = timeout
        self._max_output = max_output_bytes
        self._audit_log: List[AuditEvent] = []

    @property
    def audit_log(self) -> List[AuditEvent]:
        return list(self._audit_log)

    def execute(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> CapabilityResult:
        """Execute a shell command with constraints."""
        cmd_str = " ".join(command)

        if not self._token.is_valid:
            return self._denied("execute", cmd_str, "Token invalid")
        if not self._token.check_operation(OperationType.EXECUTE):
            return self._denied("execute", cmd_str, "EXECUTE operation not allowed")

        # Check working directory is within scope
        if cwd and not self._token.check_path(cwd):
            return self._denied("execute", cmd_str, f"Working directory not in scope: {cwd}")

        cost = 1.0
        if not self._token.spend(cost):
            return self._denied("execute", cmd_str, "Budget exceeded")

        effective_timeout = timeout or self._timeout

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=cwd,
                env=env,
            )
            stdout = result.stdout[:self._max_output]
            stderr = result.stderr[:self._max_output]

            data = {
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
            }

            if result.returncode == 0:
                audit = AuditEvent(
                    token_id=self._token.token_id, operation="execute",
                    target=cmd_str, result="success", success=True,
                )
                self._audit_log.append(audit)
                return CapabilityResult(success=True, data=data, audit=audit, cost=cost)
            else:
                audit = AuditEvent(
                    token_id=self._token.token_id, operation="execute",
                    target=cmd_str, result="non_zero_exit", success=False,
                    error=f"Exit code: {result.returncode}",
                )
                self._audit_log.append(audit)
                return CapabilityResult(success=False, data=data, error=stderr, audit=audit, cost=cost)

        except subprocess.TimeoutExpired:
            return self._denied("execute", cmd_str, f"Command timed out after {effective_timeout}s")
        except OSError as exc:
            return self._denied("execute", cmd_str, str(exc))

    def _denied(self, op: str, target: str, reason: str) -> CapabilityResult:
        audit = AuditEvent(
            token_id=self._token.token_id, operation=op,
            target=target, result="denied", success=False, error=reason,
        )
        self._audit_log.append(audit)
        return CapabilityResult(success=False, error=reason, audit=audit)


class GitCapability:
    """Git operations scoped by CapabilityToken."""

    def __init__(self, token: CapabilityToken, repo_path: str = ".") -> None:
        self._token = token
        self._repo_path = os.path.abspath(repo_path)
        self._shell = ShellCapability(token, timeout=60.0)

    @property
    def audit_log(self) -> List[AuditEvent]:
        return self._shell.audit_log

    def status(self) -> CapabilityResult:
        """Get git status."""
        if not self._token.check_path(self._repo_path):
            return CapabilityResult(success=False, error="Repo path not in scope")
        return self._shell.execute(["git", "status", "--porcelain"], cwd=self._repo_path)

    def diff(self, staged: bool = False) -> CapabilityResult:
        """Get git diff."""
        if not self._token.check_path(self._repo_path):
            return CapabilityResult(success=False, error="Repo path not in scope")
        cmd = ["git", "diff"]
        if staged:
            cmd.append("--cached")
        return self._shell.execute(cmd, cwd=self._repo_path)

    def commit(self, message: str, files: Optional[List[str]] = None) -> CapabilityResult:
        """Stage files and commit."""
        if not self._token.check_operation(OperationType.WRITE):
            return CapabilityResult(success=False, error="WRITE operation not allowed")
        if not self._token.check_path(self._repo_path):
            return CapabilityResult(success=False, error="Repo path not in scope")

        # Stage files
        if files:
            for f in files:
                stage_result = self._shell.execute(["git", "add", f], cwd=self._repo_path)
                if not stage_result.success:
                    return stage_result
        else:
            stage_result = self._shell.execute(["git", "add", "-A"], cwd=self._repo_path)
            if not stage_result.success:
                return stage_result

        return self._shell.execute(["git", "commit", "-m", message], cwd=self._repo_path)

    def checkout(self, ref: str) -> CapabilityResult:
        """Checkout a branch or commit."""
        if not self._token.check_operation(OperationType.WRITE):
            return CapabilityResult(success=False, error="WRITE operation not allowed")
        if not self._token.check_path(self._repo_path):
            return CapabilityResult(success=False, error="Repo path not in scope")
        return self._shell.execute(["git", "checkout", ref], cwd=self._repo_path)


class NetworkCapability:
    """Network fetch operations restricted to allowed destinations."""

    def __init__(self, token: CapabilityToken, timeout: float = 30.0) -> None:
        self._token = token
        self._timeout = timeout
        self._audit_log: List[AuditEvent] = []

    @property
    def audit_log(self) -> List[AuditEvent]:
        return list(self._audit_log)

    def fetch(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
    ) -> CapabilityResult:
        """Fetch a URL, only if destination is in token's allowed list.

        Uses urllib from stdlib (no external deps).
        """
        if not self._token.is_valid:
            return self._denied("fetch", url, "Token invalid")
        if not self._token.check_operation(OperationType.NETWORK):
            return self._denied("fetch", url, "NETWORK operation not allowed")
        if not self._token.check_network(url):
            return self._denied("fetch", url, f"Destination not allowed: {url}")

        cost = 2.0
        if not self._token.spend(cost):
            return self._denied("fetch", url, "Budget exceeded")

        try:
            import urllib.request
            import urllib.error

            req = urllib.request.Request(url, method=method)
            if headers:
                for k, v in headers.items():
                    req.add_header(k, v)
            if body:
                req.data = body.encode("utf-8")

            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = {
                    "status": resp.status,
                    "headers": dict(resp.headers),
                    "body": resp.read().decode("utf-8", errors="replace"),
                }
            audit = AuditEvent(
                token_id=self._token.token_id, operation="fetch",
                target=url, result="success", success=True,
            )
            self._audit_log.append(audit)
            return CapabilityResult(success=True, data=data, audit=audit, cost=cost)

        except urllib.error.URLError as exc:
            return self._denied("fetch", url, f"Network error: {exc}")
        except Exception as exc:
            return self._denied("fetch", url, str(exc))

    def _denied(self, op: str, target: str, reason: str) -> CapabilityResult:
        audit = AuditEvent(
            token_id=self._token.token_id, operation=op,
            target=target, result="denied", success=False, error=reason,
        )
        self._audit_log.append(audit)
        return CapabilityResult(success=False, error=reason, audit=audit)
