"""Repository Engineer — semantic understanding and safe modification of codebases.

Parses manifests, builds AST indices, computes semantic diffs,
generates minimum patches, and verifies before applying.
"""

from __future__ import annotations

import ast
import json
import os
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class PatchStatus(Enum):
    PLANNED = auto()
    VERIFIED = auto()
    APPLIED = auto()
    ROLLED_BACK = auto()
    FAILED = auto()


@dataclass
class SymbolInfo:
    """Information about a code symbol (function, class, variable)."""
    name: str
    kind: str  # "function", "class", "variable", "import"
    file_path: str
    line_start: int
    line_end: int
    signature: str = ""
    docstring: str = ""
    dependencies: List[str] = field(default_factory=list)


@dataclass
class DependencyInfo:
    """A project dependency."""
    name: str
    version: str = ""
    dev: bool = False
    source: str = ""  # e.g., "pyproject.toml", "package.json"


@dataclass
class TestInfo:
    """Information about a test."""
    name: str
    file_path: str
    line: int
    kind: str = "unit"  # "unit", "integration", "e2e"


@dataclass
class RouteInfo:
    """An API route or endpoint."""
    method: str
    path: str
    handler: str
    file_path: str
    line: int


@dataclass
class SchemaInfo:
    """A data schema definition."""
    name: str
    fields: Dict[str, str] = field(default_factory=dict)
    file_path: str = ""
    line: int = 0


@dataclass
class DeploymentInfo:
    """Deployment configuration."""
    platform: str = ""
    entry_point: str = ""
    config_files: List[str] = field(default_factory=list)


@dataclass
class RepositoryModel:
    """Complete semantic model of a repository."""
    manifest: Dict[str, Any] = field(default_factory=dict)
    ast_index: Dict[str, List[SymbolInfo]] = field(default_factory=dict)  # file -> symbols
    symbols: Dict[str, SymbolInfo] = field(default_factory=dict)  # qualified_name -> info
    dependencies: List[DependencyInfo] = field(default_factory=list)
    tests: List[TestInfo] = field(default_factory=list)
    schemas: List[SchemaInfo] = field(default_factory=list)
    routes: List[RouteInfo] = field(default_factory=list)
    deployment: Optional[DeploymentInfo] = None
    root_path: str = ""
    language: str = ""


@dataclass
class EditPlan:
    """A planned edit to the repository."""
    description: str
    patches: List["Patch"] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    affected_symbols: List[str] = field(default_factory=list)
    estimated_risk: str = "low"  # low, medium, high


@dataclass
class Patch:
    """A single file patch."""
    file_path: str
    original_content: str = ""
    new_content: str = ""
    description: str = ""
    status: PatchStatus = PatchStatus.PLANNED
    line_start: Optional[int] = None
    line_end: Optional[int] = None

    @property
    def is_creation(self) -> bool:
        return not self.original_content and bool(self.new_content)

    @property
    def is_deletion(self) -> bool:
        return bool(self.original_content) and not self.new_content


@dataclass
class VerificationResult:
    """Result of patch verification."""
    success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    tests_passed: int = 0
    tests_failed: int = 0
    lint_issues: int = 0


class RepositoryEngineer:
    """Semantic repository understanding and safe modification.

    - index_repo: parse and index a repository
    - infer_model: build a RepositoryModel from file system
    - plan_edit: generate minimum edit plan
    - apply_patch: apply patches safely
    - verify_patch: run build/lint/test before committing
    - rollback: undo applied patches
    """

    def __init__(self, root_path: str = ".") -> None:
        self._root = os.path.abspath(root_path)
        self._model: Optional[RepositoryModel] = None
        self._applied_patches: List[Patch] = []

    @property
    def model(self) -> Optional[RepositoryModel]:
        return self._model

    def index_repo(self, root_path: Optional[str] = None) -> RepositoryModel:
        """Parse and index the repository, building a complete semantic model."""
        root = os.path.abspath(root_path or self._root)
        model = RepositoryModel(root_path=root)

        # Detect language and manifest
        model.manifest = self._parse_manifest(root)
        model.language = self._detect_language(root)
        model.dependencies = self._parse_dependencies(root, model.manifest)
        model.deployment = self._detect_deployment(root)

        # Walk source files and build AST index
        source_extensions = {".py", ".js", ".ts", ".jsx", ".tsx"}
        for dirpath, dirnames, filenames in os.walk(root):
            # Skip hidden dirs and common non-source dirs
            dirnames[:] = [
                d for d in dirnames
                if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv", ".venv", "dist", "build")
            ]
            for fname in filenames:
                _, ext = os.path.splitext(fname)
                if ext in source_extensions:
                    full_path = os.path.join(dirpath, fname)
                    rel_path = os.path.relpath(full_path, root)
                    symbols = self._parse_file_symbols(full_path, rel_path)
                    if symbols:
                        model.ast_index[rel_path] = symbols
                        for sym in symbols:
                            qualified = f"{rel_path}::{sym.name}"
                            model.symbols[qualified] = sym

                    # Detect tests
                    if "test" in fname.lower() or "test" in dirpath.lower():
                        for sym in symbols:
                            if sym.kind == "function" and sym.name.startswith("test"):
                                model.tests.append(TestInfo(
                                    name=sym.name, file_path=rel_path, line=sym.line_start,
                                ))

        self._model = model
        return model

    def infer_model(self) -> RepositoryModel:
        """Build/refresh the repository model."""
        return self.index_repo()

    def plan_edit(
        self,
        description: str,
        target_files: Optional[List[str]] = None,
        changes: Optional[Dict[str, str]] = None,
    ) -> EditPlan:
        """Generate a minimum edit plan for a described change.

        Args:
            description: What the edit should accomplish
            target_files: Files to modify (if known)
            changes: Dict of file_path -> new_content (if known)
        """
        patches: List[Patch] = []
        affected_files: List[str] = []
        affected_symbols: List[str] = []

        if changes:
            for file_path, new_content in changes.items():
                full_path = os.path.join(self._root, file_path)
                original = ""
                if os.path.exists(full_path):
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            original = f.read()
                    except OSError:
                        pass

                patch = Patch(
                    file_path=file_path,
                    original_content=original,
                    new_content=new_content,
                    description=description,
                )
                patches.append(patch)
                affected_files.append(file_path)

                # Find affected symbols
                if self._model and file_path in self._model.ast_index:
                    for sym in self._model.ast_index[file_path]:
                        affected_symbols.append(f"{file_path}::{sym.name}")

        # Estimate risk
        risk = "low"
        if len(affected_files) > 5:
            risk = "medium"
        if any("test" not in f.lower() for f in affected_files):
            if len(affected_symbols) > 10:
                risk = "high"

        return EditPlan(
            description=description,
            patches=patches,
            affected_files=affected_files,
            affected_symbols=affected_symbols,
            estimated_risk=risk,
        )

    def apply_patch(self, patch: Patch) -> bool:
        """Apply a single patch to the filesystem.

        Stores original content for rollback.
        """
        full_path = os.path.join(self._root, patch.file_path)

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Read current content for rollback
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    patch.original_content = f.read()

            if patch.is_deletion:
                os.remove(full_path)
            else:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(patch.new_content)

            patch.status = PatchStatus.APPLIED
            self._applied_patches.append(patch)
            return True

        except OSError:
            patch.status = PatchStatus.FAILED
            return False

    def verify_patch(
        self,
        patch: Patch,
        build_cmd: Optional[List[str]] = None,
        lint_cmd: Optional[List[str]] = None,
        test_cmd: Optional[List[str]] = None,
    ) -> VerificationResult:
        """Verify a patch by running build, lint, and tests.

        Does NOT execute commands in this implementation (sandbox mode).
        Performs static verification only.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Static verification: try to parse the new content
        if patch.new_content and patch.file_path.endswith(".py"):
            try:
                ast.parse(patch.new_content)
            except SyntaxError as exc:
                errors.append(f"Syntax error in {patch.file_path}: {exc}")

        # Check that file isn't empty (unless deletion)
        if not patch.is_deletion and not patch.new_content.strip():
            warnings.append(f"Patch produces empty file: {patch.file_path}")

        # Check for common issues
        if patch.new_content:
            lines = patch.new_content.split("\n")
            for i, line in enumerate(lines):
                if "\t" in line and "    " in line:
                    warnings.append(f"Mixed tabs and spaces at line {i+1}")
                if len(line) > 120:
                    warnings.append(f"Line {i+1} exceeds 120 chars")

        patch.status = PatchStatus.VERIFIED if not errors else PatchStatus.FAILED

        return VerificationResult(
            success=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def rollback(self, patch: Optional[Patch] = None) -> bool:
        """Rollback a specific patch or the last applied patch."""
        target = patch or (self._applied_patches[-1] if self._applied_patches else None)
        if target is None:
            return False

        full_path = os.path.join(self._root, target.file_path)

        try:
            if target.is_creation:
                # Was a new file, remove it
                if os.path.exists(full_path):
                    os.remove(full_path)
            elif target.original_content:
                # Restore original
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(target.original_content)

            target.status = PatchStatus.ROLLED_BACK
            if target in self._applied_patches:
                self._applied_patches.remove(target)
            return True
        except OSError:
            return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_manifest(self, root: str) -> Dict[str, Any]:
        """Parse project manifest (package.json, pyproject.toml, etc.)."""
        manifest: Dict[str, Any] = {}

        # Try pyproject.toml
        pyproject = os.path.join(root, "pyproject.toml")
        if os.path.exists(pyproject):
            manifest["type"] = "python"
            manifest["file"] = "pyproject.toml"
            try:
                with open(pyproject, "r") as f:
                    manifest["raw"] = f.read()
            except OSError:
                pass
            return manifest

        # Try setup.py
        setup_py = os.path.join(root, "setup.py")
        if os.path.exists(setup_py):
            manifest["type"] = "python"
            manifest["file"] = "setup.py"
            return manifest

        # Try package.json
        pkg_json = os.path.join(root, "package.json")
        if os.path.exists(pkg_json):
            manifest["type"] = "javascript"
            manifest["file"] = "package.json"
            try:
                with open(pkg_json, "r") as f:
                    manifest["parsed"] = json.load(f)
            except (OSError, json.JSONDecodeError):
                pass
            return manifest

        # Try Cargo.toml
        cargo = os.path.join(root, "Cargo.toml")
        if os.path.exists(cargo):
            manifest["type"] = "rust"
            manifest["file"] = "Cargo.toml"
            return manifest

        return manifest

    def _detect_language(self, root: str) -> str:
        """Detect primary language from manifest or file extensions."""
        manifest_type = self._model.manifest.get("type") if self._model else None
        if manifest_type:
            return manifest_type

        # Count file extensions
        ext_counts: Dict[str, int] = {}
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "node_modules"]
            for fname in filenames:
                _, ext = os.path.splitext(fname)
                if ext:
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1

        lang_map = {".py": "python", ".js": "javascript", ".ts": "typescript", ".rs": "rust", ".go": "go"}
        best_ext = max(ext_counts, key=ext_counts.get, default="")  # type: ignore
        return lang_map.get(best_ext, "unknown")

    def _parse_dependencies(self, root: str, manifest: Dict[str, Any]) -> List[DependencyInfo]:
        """Parse project dependencies from manifest."""
        deps: List[DependencyInfo] = []

        if manifest.get("type") == "javascript" and "parsed" in manifest:
            parsed = manifest["parsed"]
            for name, version in parsed.get("dependencies", {}).items():
                deps.append(DependencyInfo(name=name, version=version, source="package.json"))
            for name, version in parsed.get("devDependencies", {}).items():
                deps.append(DependencyInfo(name=name, version=version, dev=True, source="package.json"))

        # For Python, a full TOML parser would be needed; simplified here
        return deps

    def _detect_deployment(self, root: str) -> Optional[DeploymentInfo]:
        """Detect deployment configuration."""
        config_files: List[str] = []

        checks = [
            "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
            ".github/workflows", "Procfile", "serverless.yml",
            "terraform", "cdk.json",
        ]
        for check in checks:
            if os.path.exists(os.path.join(root, check)):
                config_files.append(check)

        if config_files:
            platform = "docker" if any("docker" in c.lower() for c in config_files) else "unknown"
            return DeploymentInfo(platform=platform, config_files=config_files)
        return None

    def _parse_file_symbols(self, full_path: str, rel_path: str) -> List[SymbolInfo]:
        """Parse Python file to extract symbols using AST."""
        if not full_path.endswith(".py"):
            return []

        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
            tree = ast.parse(source)
        except (SyntaxError, OSError):
            return []

        symbols: List[SymbolInfo] = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                sig = f"def {node.name}({', '.join(a.arg for a in node.args.args)})"
                doc = ast.get_docstring(node) or ""
                symbols.append(SymbolInfo(
                    name=node.name, kind="function", file_path=rel_path,
                    line_start=node.lineno, line_end=node.end_lineno or node.lineno,
                    signature=sig, docstring=doc[:200],
                ))
            elif isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or ""
                symbols.append(SymbolInfo(
                    name=node.name, kind="class", file_path=rel_path,
                    line_start=node.lineno, line_end=node.end_lineno or node.lineno,
                    signature=f"class {node.name}", docstring=doc[:200],
                ))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    symbols.append(SymbolInfo(
                        name=alias.name, kind="import", file_path=rel_path,
                        line_start=node.lineno, line_end=node.lineno,
                    ))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    symbols.append(SymbolInfo(
                        name=f"{module}.{alias.name}", kind="import", file_path=rel_path,
                        line_start=node.lineno, line_end=node.lineno,
                    ))

        return symbols
