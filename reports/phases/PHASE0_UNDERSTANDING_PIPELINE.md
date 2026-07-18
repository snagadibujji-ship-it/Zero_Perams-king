# Understanding Pipeline

## Purpose

The Understanding Pipeline provides a framework for **knowledge abstraction**, enabling the system to progressively elevate raw observations into deep, transferable understanding. It implements a four-level abstraction hierarchy:

```
Fact → Pattern → Rule → Principle
```

Each level represents increasing generality and explanatory power, allowing the system to move from isolated data points to universal principles that can be applied across domains.

## Abstraction Levels

| Level | Description | Storage Node Type | Example |
|-------|-------------|-------------------|---------|
| **Fact** | A concrete, verified observation | `fact` | "Water boils at 100°C at sea level" |
| **Pattern** | A recurring relationship across multiple facts | `concept` | "Boiling points decrease with altitude" |
| **Rule** | A causal or conditional generalization derived from patterns | `theory` | "Lower pressure → lower boiling point" |
| **Principle** | A fundamental, domain-spanning truth synthesized from rules | `theory` | "Phase transitions depend on thermodynamic conditions" |

### Level Details

#### 1. Fact (Ground Level)

Facts are atomic observations grounded in direct evidence. They are the raw material from which all higher understanding is built.

- **Example:** "Water boils at 100°C at sea level"
- **Stored as:** `fact` nodes in the Reality Graph
- **Characteristics:** Concrete, verifiable, context-specific

#### 2. Pattern (First Abstraction)

Patterns emerge when multiple facts reveal a recurring relationship or trend. They represent the first step toward generalization.

- **Example:** "Boiling points decrease with altitude"
- **Stored as:** `concept` nodes in the Reality Graph
- **Characteristics:** Observational, multi-fact, describes "what happens"

#### 3. Rule (Second Abstraction)

Rules capture causal or conditional relationships derived from patterns. They explain *why* patterns exist and allow prediction.

- **Example:** "Lower pressure → lower boiling point"
- **Stored as:** `theory` nodes in the Reality Graph
- **Characteristics:** Causal, predictive, describes "why it happens"

#### 4. Principle (Highest Abstraction)

Principles are fundamental truths that transcend specific domains. They synthesize multiple rules into universal understanding.

- **Example:** "Phase transitions depend on thermodynamic conditions"
- **Stored as:** `theory` nodes in the Reality Graph
- **Characteristics:** Universal, domain-spanning, describes "how things work"

## Architecture

### ABC Interfaces (Plugin Points)

The pipeline defines abstract base classes for future intelligence plugins:

```python
class PatternDetector(ABC):
    """Detects patterns from collections of facts."""

    @abstractmethod
    def detect(self, facts: List[Fact]) -> List[Pattern]:
        ...

class RuleExtractor(ABC):
    """Extracts causal rules from identified patterns."""

    @abstractmethod
    def extract(self, patterns: List[Pattern]) -> List[Rule]:
        ...

class PrincipleSynthesizer(ABC):
    """Synthesizes universal principles from rules."""

    @abstractmethod
    def synthesize(self, rules: List[Rule]) -> List[Principle]:
        ...
```

These interfaces allow swapping in different AI/ML backends (LLM-based reasoning, statistical analysis, symbolic logic engines) without changing the pipeline structure.

### Manual Promotion Helpers

For explicit, human-guided knowledge elevation:

```python
register_fact(domain, observation, evidence=None)
```
Records a new fact in the specified domain.

```python
promote_to_pattern(domain, facts, description)
```
Groups related facts into a named pattern.

```python
derive_rule(domain, patterns, causal_statement)
```
Derives a causal rule from one or more patterns.

```python
synthesize_principle(domain, rules, universal_statement)
```
Synthesizes a domain-spanning principle from rules.

### Automated Pipeline Runner

```python
run_pipeline(domain)
```
Executes the full abstraction pipeline for a given domain:
1. Collects all facts in the domain
2. Applies `PatternDetector` to identify patterns
3. Applies `RuleExtractor` to derive rules
4. Applies `PrincipleSynthesizer` to formulate principles
5. Stores all results in the Reality Graph

### Query Interface

```python
get_understanding(domain) -> DepthAssessment
```
Returns a depth assessment of the current understanding for a domain, including:
- Number of facts, patterns, rules, and principles
- Current abstraction depth reached
- Gaps where promotion may be possible
- Confidence scores at each level

## Storage in Reality Graph

The Understanding Pipeline integrates with the Reality Graph for persistent storage:

| Abstraction Level | Node Type | Relationships |
|-------------------|-----------|---------------|
| Fact | `fact` | Links to evidence, domain |
| Pattern | `concept` | Links to constituent facts |
| Rule | `theory` | Links to source patterns |
| Principle | `theory` | Links to derived rules |

Rules and Principles share the `theory` node type but are distinguished by metadata (abstraction level, scope, generality).

## Implementation

- **File:** `/root/hybrid-ai/src/python/core/understanding.py`
- **Size:** 442 lines
- **Dependencies:** Reality Graph, ABC plugin interfaces

## Status

✅ **Framework implemented** — The core pipeline structure, manual promotion helpers, query interface, and Reality Graph integration are complete.

⏳ **Intelligence plugins pending** — AI-powered `PatternDetector`, `RuleExtractor`, and `PrincipleSynthesizer` implementations are planned for future phases. Currently, knowledge promotion relies on manual helper functions.
