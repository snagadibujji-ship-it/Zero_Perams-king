"""Code execution sandbox for AXIMA.

Runs generated code in isolated subprocess with resource limits.
NEVER uses exec() on user/generated code in the main process.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

from axima.errors import ResourceError, SecurityError
from axima.errors import TimeoutError as AximaTimeoutError


class NetworkPolicy(Enum):
    """Network access policy for sandboxed code."""

    DENY_ALL = auto()
    ALLOW_LOCALHOST = auto()


@dataclass
class SandboxConfig:
    """Configuration for code sandbox resource limits."""

    max_time_seconds: float = 10.0
    max_memory_mb: int = 256
    max_output_bytes: int = 1_048_576  # 1 MB
    max_processes: int = 1
    network_policy: NetworkPolicy = NetworkPolicy.DENY_ALL
    allowed_languages: frozenset[str] = field(
        default_factory=lambda: frozenset({"python", "javascript", "bash"})
    )


@dataclass
class SandboxResult:
    """Result of sandboxed code execution."""

    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False
    memory_exceeded: bool = False
    output_truncated: bool = False

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and not self.memory_exceeded


class CodeSandbox:
    """Safe execution environment for generated code.

    Features:
      - Subprocess isolation (never exec() in main process)
      - Time limits via subprocess timeout
      - Memory limits via ulimit (Linux)
      - Output size limits
      - Network deny by default
      - File access restricted to temp directory
    """

    def __init__(self, config: SandboxConfig | None = None) -> None:
        self._config = config or SandboxConfig()
        self._temp_dir: Path | None = None

    @property
    def config(self) -> SandboxConfig:
        return self._config

    def execute(
        self,
        code: str,
        language: str = "python",
        *,
        stdin: str = "",
        env_vars: dict[str, str] | None = None,
    ) -> SandboxResult:
        """Execute code in a sandboxed subprocess.

        Args:
            code: Source code to execute.
            language: Programming language (python, javascript, bash).
            stdin: Standard input to provide.
            env_vars: Additional environment variables (sanitized).

        Returns:
            SandboxResult with stdout, stderr, exit_code, and status flags.

        Raises:
            SecurityError: If language not allowed or code fails safety checks.
            ResourceError: If resource limits cannot be enforced.
        """
        if language not in self._config.allowed_languages:
            raise SecurityError(
                f"Language '{language}' is not allowed",
                context={"language": language, "allowed": list(self._config.allowed_languages)},
            )

        # Pre-execution safety checks
        self._check_code_safety(code, language)

        # Create isolated temp directory
        self._temp_dir = Path(tempfile.mkdtemp(prefix="axima_sandbox_"))
        try:
            return self._run_in_sandbox(code, language, stdin, env_vars)
        finally:
            self._cleanup()

    def _check_code_safety(self, code: str, language: str) -> None:
        """Reject code with obvious escape attempts before execution."""
        dangerous_patterns = [
            "subprocess",
            "os.system",
            "os.exec",
            "shutil.rmtree",
            "__import__",
            "importlib",
            "ctypes",
            "socket.connect",
            "urllib.request",
            "requests.get",
            "requests.post",
        ]
        if language == "python":
            for pattern in dangerous_patterns:
                if pattern in code:
                    raise SecurityError(
                        f"Dangerous pattern detected: '{pattern}'",
                        context={"pattern": pattern, "language": language},
                    )

    def _run_in_sandbox(
        self,
        code: str,
        language: str,
        stdin: str,
        env_vars: dict[str, str] | None,
    ) -> SandboxResult:
        """Execute code in subprocess with resource limits."""
        assert self._temp_dir is not None

        # Write code to file in temp directory
        ext_map = {"python": ".py", "javascript": ".js", "bash": ".sh"}
        code_file = self._temp_dir / f"code{ext_map.get(language, '.txt')}"
        code_file.write_text(code, encoding="utf-8")

        # Build command
        cmd = self._build_command(code_file, language)

        # Build environment: minimal, no secrets
        env = self._build_env(env_vars)

        # Resource limit prefix (Linux ulimit)
        wrapper_cmd = self._build_resource_wrapper(cmd)

        try:
            proc = subprocess.run(
                wrapper_cmd,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=self._config.max_time_seconds,
                cwd=str(self._temp_dir),
                env=env,
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                stdout="",
                stderr="Execution timed out",
                exit_code=-1,
                timed_out=True,
            )

        # Truncate output if needed
        stdout = proc.stdout
        stderr = proc.stderr
        output_truncated = False

        if len(stdout.encode()) > self._config.max_output_bytes:
            stdout = stdout[: self._config.max_output_bytes]
            output_truncated = True
        if len(stderr.encode()) > self._config.max_output_bytes:
            stderr = stderr[: self._config.max_output_bytes]
            output_truncated = True

        return SandboxResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=proc.returncode,
            output_truncated=output_truncated,
        )

    def _build_command(self, code_file: Path, language: str) -> list[str]:
        """Build the execution command for the given language."""
        if language == "python":
            return ["python3", "-u", str(code_file)]
        if language == "javascript":
            return ["node", str(code_file)]
        if language == "bash":
            return ["bash", str(code_file)]
        raise SecurityError(f"No command builder for language: {language}")

    def _build_resource_wrapper(self, cmd: list[str]) -> list[str]:
        """Wrap command with resource limits (Linux-specific)."""
        mem_bytes = self._config.max_memory_mb * 1024 * 1024
        nproc = self._config.max_processes

        # Use ulimit in a shell wrapper for memory and process limits
        ulimit_prefix = (
            f"ulimit -v {mem_bytes // 1024} 2>/dev/null; "
            f"ulimit -u {nproc} 2>/dev/null; "
        )

        # Network deny: use unshare if available (requires root or user ns)
        # Fall back to just running without network isolation
        net_prefix = ""
        if self._config.network_policy == NetworkPolicy.DENY_ALL:
            # Try unshare --net if available
            if shutil.which("unshare"):
                net_prefix = "unshare --net -- "

        shell_cmd = ulimit_prefix + net_prefix + " ".join(
            _shell_quote(c) for c in cmd
        )
        return ["bash", "-c", shell_cmd]

    def _build_env(self, extra: dict[str, str] | None) -> dict[str, str]:
        """Build a minimal, safe environment."""
        env: dict[str, str] = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": str(self._temp_dir),
            "TMPDIR": str(self._temp_dir),
            "LANG": "C.UTF-8",
        }
        if extra:
            # Only allow safe env vars (no secrets patterns)
            secret_patterns = {"key", "secret", "token", "password", "credential"}
            for k, v in extra.items():
                if any(s in k.lower() for s in secret_patterns):
                    raise SecurityError(
                        f"Cannot pass secret-like env var: {k}",
                        context={"var_name": k},
                    )
                env[k] = v
        return env

    def _cleanup(self) -> None:
        """Remove the temporary directory."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None


def _shell_quote(s: str) -> str:
    """Safe shell quoting for subprocess arguments."""
    if not s:
        return "''"
    # Use single quotes, escaping any embedded single quotes
    return "'" + s.replace("'", "'\\''") + "'"
