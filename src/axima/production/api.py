"""AXIMA Production API: Local HTTP-like contract.

Defines the API surface for AXIMA in production mode, with routes
for querying, health checks, diagnostics, memory management,
and evaluation.

This is a contract definition — actual HTTP serving is handled
by the deployment layer. The API class processes requests and
returns structured responses.
"""

from __future__ import annotations

import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol


class HttpMethod(Enum):
    """Supported HTTP methods."""

    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"


class StatusCode(Enum):
    """HTTP status codes used by the API."""

    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    NOT_FOUND = 404
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503


@dataclass
class Request:
    """API request object.

    Attributes:
        method: HTTP method.
        path: Request path (e.g., '/query').
        body: Request body (parsed JSON).
        headers: Request headers.
        params: Path parameters (e.g., trace_id from /trace/{id}).
        query_params: Query string parameters.
        request_id: Unique request identifier.
    """

    method: HttpMethod
    path: str
    body: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Response:
    """API response object.

    Attributes:
        status: HTTP status code.
        body: Response body (will be serialized to JSON).
        headers: Response headers.
        request_id: Echoed request identifier.
        latency_ms: Processing time in milliseconds.
    """

    status: StatusCode
    body: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    request_id: str = ""
    latency_ms: float = 0.0

    def to_dict(self) -> dict:
        """Serialize response to dictionary."""
        return {
            "status": self.status.value,
            "body": self.body,
            "headers": self.headers,
            "request_id": self.request_id,
            "latency_ms": self.latency_ms,
        }


@dataclass
class Route:
    """API route definition.

    Attributes:
        method: HTTP method.
        path: URL path pattern (supports {param} placeholders).
        handler: Function that processes requests.
        description: Human-readable description.
    """

    method: HttpMethod
    path: str
    handler: Callable[[Request], Response]
    description: str = ""


class QueryFn(Protocol):
    """Protocol for the AXIMA query function."""

    def __call__(self, query: str) -> str: ...


@dataclass
class Capabilities:
    """AXIMA capability declaration.

    Attributes:
        math: Math solving available.
        physics: Physics solving available.
        code: Code generation available.
        web: Web generation available.
        multilingual: Multilingual support available.
        knowledge: Knowledge base available.
        creator: Content generation available.
    """

    math: bool = True
    physics: bool = True
    code: bool = True
    web: bool = True
    multilingual: bool = True
    knowledge: bool = True
    creator: bool = True

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "math": self.math,
            "physics": self.physics,
            "code": self.code,
            "web": self.web,
            "multilingual": self.multilingual,
            "knowledge": self.knowledge,
            "creator": self.creator,
        }


class AximaAPI:
    """Local HTTP-like API for AXIMA production deployment.

    Routes:
        POST /query            - Submit a query to AXIMA
        GET  /health           - Health check (is the process alive?)
        GET  /ready            - Readiness check (is the system ready to serve?)
        GET  /doctor           - Diagnostic self-check
        GET  /capabilities     - List available capabilities
        GET  /trace/{id}       - Retrieve trace for a query
        POST /memory/export    - Export memory state
        DELETE /memory/delete  - Delete memory entries
        POST /eval/run         - Trigger evaluation run
    """

    def __init__(
        self,
        query_fn: Optional[QueryFn] = None,
        version: str = "0.1.0",
    ) -> None:
        """Initialize the API.

        Args:
            query_fn: Function to process queries. If None, /query returns 503.
            version: AXIMA version string.
        """
        self._query_fn = query_fn
        self._version = version
        self._ready = False
        self._healthy = True
        self._start_time = time.time()
        self._request_count = 0
        self._error_count = 0
        self._traces: Dict[str, Dict[str, Any]] = {}
        self._memory: Dict[str, Any] = {}
        self._capabilities = Capabilities()
        self._routes = self._register_routes()

    @property
    def routes(self) -> List[Route]:
        """All registered routes."""
        return list(self._routes.values())

    def set_ready(self, ready: bool = True) -> None:
        """Set the readiness state."""
        self._ready = ready

    def set_healthy(self, healthy: bool = True) -> None:
        """Set the health state."""
        self._healthy = healthy

    def handle(self, request: Request) -> Response:
        """Route and handle a request.

        Args:
            request: The incoming request.

        Returns:
            Response object.
        """
        start = time.time()
        self._request_count += 1

        try:
            # Match route
            handler = self._match_route(request)
            if handler is None:
                response = Response(
                    status=StatusCode.NOT_FOUND,
                    body={"error": f"Route not found: {request.method.value} {request.path}"},
                    request_id=request.request_id,
                )
            else:
                response = handler(request)
                response.request_id = request.request_id
        except Exception as e:
            self._error_count += 1
            response = Response(
                status=StatusCode.INTERNAL_ERROR,
                body={
                    "error": str(e),
                    "type": type(e).__name__,
                },
                request_id=request.request_id,
            )

        response.latency_ms = (time.time() - start) * 1000
        return response

    def _register_routes(self) -> Dict[str, Route]:
        """Register all API routes."""
        routes: Dict[str, Route] = {}

        routes["POST /query"] = Route(
            method=HttpMethod.POST,
            path="/query",
            handler=self._handle_query,
            description="Submit a query to AXIMA",
        )
        routes["GET /health"] = Route(
            method=HttpMethod.GET,
            path="/health",
            handler=self._handle_health,
            description="Health check",
        )
        routes["GET /ready"] = Route(
            method=HttpMethod.GET,
            path="/ready",
            handler=self._handle_ready,
            description="Readiness check",
        )
        routes["GET /doctor"] = Route(
            method=HttpMethod.GET,
            path="/doctor",
            handler=self._handle_doctor,
            description="Diagnostic self-check",
        )
        routes["GET /capabilities"] = Route(
            method=HttpMethod.GET,
            path="/capabilities",
            handler=self._handle_capabilities,
            description="List capabilities",
        )
        routes["GET /trace/{id}"] = Route(
            method=HttpMethod.GET,
            path="/trace/{id}",
            handler=self._handle_trace,
            description="Get query trace",
        )
        routes["POST /memory/export"] = Route(
            method=HttpMethod.POST,
            path="/memory/export",
            handler=self._handle_memory_export,
            description="Export memory state",
        )
        routes["DELETE /memory/delete"] = Route(
            method=HttpMethod.DELETE,
            path="/memory/delete",
            handler=self._handle_memory_delete,
            description="Delete memory entries",
        )
        routes["POST /eval/run"] = Route(
            method=HttpMethod.POST,
            path="/eval/run",
            handler=self._handle_eval_run,
            description="Run evaluation",
        )

        return routes

    def _match_route(self, request: Request) -> Optional[Callable[[Request], Response]]:
        """Match a request to a route handler."""
        # Direct match
        key = f"{request.method.value} {request.path}"
        if key in self._routes:
            return self._routes[key].handler

        # Pattern matching for parameterized routes
        for route_key, route in self._routes.items():
            if route.method != request.method:
                continue
            if self._path_matches(route.path, request.path, request):
                return route.handler

        return None

    def _path_matches(self, pattern: str, path: str, request: Request) -> bool:
        """Check if a path matches a route pattern, extracting params."""
        pattern_parts = pattern.strip("/").split("/")
        path_parts = path.strip("/").split("/")

        if len(pattern_parts) != len(path_parts):
            return False

        for pp, pathp in zip(pattern_parts, path_parts):
            if pp.startswith("{") and pp.endswith("}"):
                param_name = pp[1:-1]
                request.params[param_name] = pathp
            elif pp != pathp:
                return False

        return True

    # --- Route Handlers ---

    def _handle_query(self, request: Request) -> Response:
        """Handle POST /query."""
        if not self._ready:
            return Response(
                status=StatusCode.SERVICE_UNAVAILABLE,
                body={"error": "Service not ready"},
            )

        if self._query_fn is None:
            return Response(
                status=StatusCode.SERVICE_UNAVAILABLE,
                body={"error": "Query function not configured"},
            )

        query = request.body.get("query", "")
        if not query:
            return Response(
                status=StatusCode.BAD_REQUEST,
                body={"error": "Missing 'query' field in request body"},
            )

        # Execute query
        trace_id = str(uuid.uuid4())
        start = time.time()

        try:
            result = self._query_fn(query)
            latency = (time.time() - start) * 1000

            # Store trace
            self._traces[trace_id] = {
                "query": query,
                "result": result,
                "latency_ms": latency,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

            return Response(
                status=StatusCode.OK,
                body={
                    "result": result,
                    "trace_id": trace_id,
                    "latency_ms": latency,
                },
            )
        except Exception as e:
            self._error_count += 1
            return Response(
                status=StatusCode.INTERNAL_ERROR,
                body={
                    "error": f"Query failed: {e}",
                    "type": type(e).__name__,
                },
            )

    def _handle_health(self, request: Request) -> Response:
        """Handle GET /health."""
        if self._healthy:
            return Response(
                status=StatusCode.OK,
                body={
                    "status": "healthy",
                    "uptime_s": time.time() - self._start_time,
                    "version": self._version,
                },
            )
        else:
            return Response(
                status=StatusCode.SERVICE_UNAVAILABLE,
                body={"status": "unhealthy"},
            )

    def _handle_ready(self, request: Request) -> Response:
        """Handle GET /ready."""
        if self._ready:
            return Response(
                status=StatusCode.OK,
                body={
                    "status": "ready",
                    "request_count": self._request_count,
                    "error_count": self._error_count,
                },
            )
        else:
            return Response(
                status=StatusCode.SERVICE_UNAVAILABLE,
                body={"status": "not_ready"},
            )

    def _handle_doctor(self, request: Request) -> Response:
        """Handle GET /doctor — diagnostic self-check."""
        checks: Dict[str, Dict[str, Any]] = {}

        # Check query function
        checks["query_fn"] = {
            "status": "ok" if self._query_fn is not None else "missing",
            "description": "Query function availability",
        }

        # Check memory
        checks["memory"] = {
            "status": "ok",
            "entries": len(self._memory),
            "description": "Memory subsystem",
        }

        # Check traces
        checks["traces"] = {
            "status": "ok",
            "stored": len(self._traces),
            "description": "Trace storage",
        }

        # Overall health
        all_ok = all(c["status"] == "ok" for c in checks.values())

        return Response(
            status=StatusCode.OK,
            body={
                "overall": "healthy" if all_ok else "degraded",
                "checks": checks,
                "version": self._version,
                "uptime_s": time.time() - self._start_time,
            },
        )

    def _handle_capabilities(self, request: Request) -> Response:
        """Handle GET /capabilities."""
        return Response(
            status=StatusCode.OK,
            body={
                "capabilities": self._capabilities.to_dict(),
                "version": self._version,
            },
        )

    def _handle_trace(self, request: Request) -> Response:
        """Handle GET /trace/{id}."""
        trace_id = request.params.get("id", "")
        if not trace_id:
            return Response(
                status=StatusCode.BAD_REQUEST,
                body={"error": "Missing trace ID"},
            )

        trace = self._traces.get(trace_id)
        if trace is None:
            return Response(
                status=StatusCode.NOT_FOUND,
                body={"error": f"Trace not found: {trace_id}"},
            )

        return Response(
            status=StatusCode.OK,
            body={"trace": trace},
        )

    def _handle_memory_export(self, request: Request) -> Response:
        """Handle POST /memory/export."""
        return Response(
            status=StatusCode.OK,
            body={
                "memory": dict(self._memory),
                "count": len(self._memory),
                "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )

    def _handle_memory_delete(self, request: Request) -> Response:
        """Handle DELETE /memory/delete."""
        keys = request.body.get("keys", [])

        if not keys:
            # Delete all
            count = len(self._memory)
            self._memory.clear()
            return Response(
                status=StatusCode.OK,
                body={"deleted": count, "message": "All memory cleared"},
            )

        deleted = 0
        for key in keys:
            if key in self._memory:
                del self._memory[key]
                deleted += 1

        return Response(
            status=StatusCode.OK,
            body={"deleted": deleted, "requested": len(keys)},
        )

    def _handle_eval_run(self, request: Request) -> Response:
        """Handle POST /eval/run."""
        suite = request.body.get("suite", "all")
        categories = request.body.get("categories")
        seed = request.body.get("seed", 42)

        return Response(
            status=StatusCode.OK,
            body={
                "status": "started",
                "suite": suite,
                "categories": categories,
                "seed": seed,
                "message": "Evaluation run initiated. Check /trace for results.",
            },
        )
