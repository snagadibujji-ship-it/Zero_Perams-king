"""
Metrics Collection
==================

Lightweight metrics collection for observability. Tracks:
- query_count: Total queries processed
- latency_ms: Query latency histogram
- engine_calls: Per-engine invocation counts
- error_rate: Error count and rate
- memory_usage: Memory consumption gauge
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = "counter"       # Monotonically increasing count
    GAUGE = "gauge"           # Point-in-time value
    HISTOGRAM = "histogram"   # Distribution of values


@dataclass
class Metric:
    """A single metric observation.

    Attributes:
        name: Metric name (e.g., 'query_count', 'latency_ms').
        type: Counter, gauge, or histogram.
        value: The metric value.
        labels: Dimensional labels (e.g., {'engine': 'math'}).
        timestamp: When this metric was recorded.
    """

    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class HistogramBucket:
    """A bucket in a histogram."""

    upper_bound: float
    count: int = 0


@dataclass
class HistogramState:
    """Internal state for a histogram metric."""

    buckets: List[HistogramBucket] = field(default_factory=list)
    sum_value: float = 0.0
    count: int = 0
    min_value: float = float("inf")
    max_value: float = float("-inf")

    def observe(self, value: float) -> None:
        """Record a value in the histogram."""
        self.sum_value += value
        self.count += 1
        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)
        for bucket in self.buckets:
            if value <= bucket.upper_bound:
                bucket.count += 1

    @property
    def mean(self) -> float:
        """Mean value."""
        return self.sum_value / max(self.count, 1)

    def percentile(self, p: float) -> float:
        """Approximate percentile from histogram buckets.

        Args:
            p: Percentile (0.0-1.0).

        Returns:
            Approximate value at the given percentile.
        """
        if self.count == 0:
            return 0.0

        target = p * self.count
        for bucket in self.buckets:
            if bucket.count >= target:
                return bucket.upper_bound

        return self.max_value

    def to_dict(self) -> Dict[str, Any]:
        """Serialize histogram state."""
        return {
            "count": self.count,
            "sum": self.sum_value,
            "min": self.min_value if self.min_value != float("inf") else 0.0,
            "max": self.max_value if self.max_value != float("-inf") else 0.0,
            "mean": self.mean,
            "buckets": [
                {"upper_bound": b.upper_bound, "count": b.count}
                for b in self.buckets
            ],
        }


# Default histogram buckets for latency (in milliseconds)
_DEFAULT_LATENCY_BUCKETS = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]


def _make_histogram(buckets: Optional[List[float]] = None) -> HistogramState:
    """Create a histogram with the given bucket boundaries."""
    bucket_bounds = buckets or _DEFAULT_LATENCY_BUCKETS
    return HistogramState(
        buckets=[HistogramBucket(upper_bound=b) for b in sorted(bucket_bounds)]
    )


class MetricsCollector:
    """Collects and manages system metrics.

    Tracks:
    - query_count: Total queries processed (counter)
    - latency_ms: Query latency distribution (histogram)
    - engine_calls: Per-engine invocation counts (counter)
    - error_rate: Errors (counter + gauge for rate)
    - memory_usage: Memory consumption (gauge)

    Thread-safe for basic operations (single-writer, multi-reader pattern).
    """

    def __init__(self) -> None:
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, HistogramState] = {}
        self._labels: Dict[str, Dict[str, str]] = {}
        self._history: List[Metric] = []
        self._start_time: float = time.time()

        # Initialize built-in metrics
        self._counters["query_count"] = 0
        self._counters["error_count"] = 0
        self._histograms["latency_ms"] = _make_histogram(_DEFAULT_LATENCY_BUCKETS)
        self._gauges["memory_usage_mb"] = 0.0
        self._gauges["error_rate"] = 0.0

    def record(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.COUNTER,
        labels: Optional[Dict[str, str]] = None,
    ) -> Metric:
        """Record a metric observation.

        Args:
            name: Metric name.
            value: The value to record.
            metric_type: Type of metric (counter, gauge, histogram).
            labels: Optional dimensional labels.

        Returns:
            The recorded Metric.
        """
        labels = labels or {}
        label_key = self._label_key(name, labels)

        if metric_type == MetricType.COUNTER:
            current = self._counters.get(label_key, 0.0)
            self._counters[label_key] = current + value
        elif metric_type == MetricType.GAUGE:
            self._gauges[label_key] = value
        elif metric_type == MetricType.HISTOGRAM:
            if label_key not in self._histograms:
                self._histograms[label_key] = _make_histogram()
            self._histograms[label_key].observe(value)

        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            labels=labels,
        )
        self._history.append(metric)
        self._labels[label_key] = labels

        # Update derived metrics
        if name == "error_count" or name.startswith("error"):
            self._update_error_rate()

        return metric

    def record_query(self, latency_ms: float, engine: str, success: bool = True) -> None:
        """Convenience: record a complete query observation.

        Args:
            latency_ms: Query latency in milliseconds.
            engine: Which engine handled the query.
            success: Whether the query succeeded.
        """
        self.record("query_count", 1, MetricType.COUNTER)
        self.record("latency_ms", latency_ms, MetricType.HISTOGRAM)
        self.record(
            "engine_calls", 1, MetricType.COUNTER,
            labels={"engine": engine},
        )
        if not success:
            self.record("error_count", 1, MetricType.COUNTER)

    def record_memory(self, memory_mb: float) -> None:
        """Record current memory usage.

        Args:
            memory_mb: Memory usage in megabytes.
        """
        self.record("memory_usage_mb", memory_mb, MetricType.GAUGE)

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value."""
        key = self._label_key(name, labels or {})
        return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value."""
        key = self._label_key(name, labels or {})
        return self._gauges.get(key, 0.0)

    def get_histogram(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[HistogramState]:
        """Get histogram state."""
        key = self._label_key(name, labels or {})
        return self._histograms.get(key)

    def get_all(self) -> Dict[str, Any]:
        """Get all current metric values.

        Returns:
            Dict with counters, gauges, and histograms.
        """
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: hist.to_dict()
                for name, hist in self._histograms.items()
            },
            "uptime_seconds": time.time() - self._start_time,
        }

    def export(self, format: str = "dict") -> Any:
        """Export all metrics.

        Args:
            format: Export format ('dict', 'prometheus', 'json_lines').

        Returns:
            Formatted metric data.
        """
        if format == "dict":
            return self.get_all()

        elif format == "prometheus":
            lines: List[str] = []

            for key, value in self._counters.items():
                labels_str = self._format_labels(self._labels.get(key, {}))
                base_name = key.split("{")[0] if "{" in key else key
                lines.append(f"# TYPE {base_name} counter")
                lines.append(f"{base_name}{labels_str} {value}")

            for key, value in self._gauges.items():
                labels_str = self._format_labels(self._labels.get(key, {}))
                base_name = key.split("{")[0] if "{" in key else key
                lines.append(f"# TYPE {base_name} gauge")
                lines.append(f"{base_name}{labels_str} {value}")

            for key, hist in self._histograms.items():
                base_name = key.split("{")[0] if "{" in key else key
                lines.append(f"# TYPE {base_name} histogram")
                lines.append(f"{base_name}_count {hist.count}")
                lines.append(f"{base_name}_sum {hist.sum_value}")
                for bucket in hist.buckets:
                    lines.append(
                        f'{base_name}_bucket{{le="{bucket.upper_bound}"}} {bucket.count}'
                    )

            return "\n".join(lines)

        elif format == "json_lines":
            import json
            lines = []
            for metric in self._history:
                lines.append(json.dumps({
                    "name": metric.name,
                    "type": metric.type.value,
                    "value": metric.value,
                    "labels": metric.labels,
                    "timestamp": metric.timestamp,
                }))
            return "\n".join(lines)

        return self.get_all()

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._labels.clear()
        self._history.clear()
        self._start_time = time.time()

        # Re-initialize built-in metrics
        self._counters["query_count"] = 0
        self._counters["error_count"] = 0
        self._histograms["latency_ms"] = _make_histogram(_DEFAULT_LATENCY_BUCKETS)
        self._gauges["memory_usage_mb"] = 0.0
        self._gauges["error_rate"] = 0.0

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------

    def _label_key(self, name: str, labels: Dict[str, str]) -> str:
        """Create a unique key combining metric name and labels."""
        if not labels:
            return name
        label_parts = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_parts}}}"

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus output."""
        if not labels:
            return ""
        parts = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{{{parts}}}"

    def _update_error_rate(self) -> None:
        """Update the error rate gauge."""
        total = self._counters.get("query_count", 0)
        errors = self._counters.get("error_count", 0)
        if total > 0:
            self._gauges["error_rate"] = errors / total
        else:
            self._gauges["error_rate"] = 0.0
