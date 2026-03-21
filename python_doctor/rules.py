"""Rule definitions and scoring categories."""

from dataclasses import dataclass, field

_CATEGORY_DEFS = {
    "security": {"emoji": "🔒", "label": "Security", "weight": 5},
    "lint": {"emoji": "🧹", "label": "Lint", "weight": 4},
    "complexity": {"emoji": "🔄", "label": "Complexity", "weight": 3},
    "structure": {"emoji": "🏗", "label": "Structure", "weight": 2},
    "imports": {"emoji": "🔗", "label": "Imports", "weight": 1},
    "exceptions": {"emoji": "⚡", "label": "Exceptions", "weight": 2},
    "zen": {"emoji": "🧘", "label": "Zen", "weight": 3},
}

def _build_categories(defs: dict) -> dict:
    """Compute max_deduction from weights so they always sum to exactly 100."""
    total_weight = sum(d["weight"] for d in defs.values())
    cats = {
        name: {**d, "max_deduction": round(d["weight"] / total_weight * 100)}
        for name, d in defs.items()
    }
    # Fix rounding residual by adjusting the highest-weight category
    residual = 100 - sum(c["max_deduction"] for c in cats.values())
    if residual:
        top = max(cats, key=lambda k: cats[k]["weight"])
        cats[top]["max_deduction"] += residual
    return cats

CATEGORIES = _build_categories(_CATEGORY_DEFS)

# Security
BANDIT_SEVERITY_COST = {"HIGH": 2, "MEDIUM": 1, "LOW": 0.5}

# Lint
RUFF_ERROR_COST = 1.0
RUFF_WARNING_COST = 0.5

# Complexity
COMPLEXITY_COST = {15: 2, 25: 5}

# Structure
LARGE_FILE_THRESHOLD = 1000
LARGE_FILE_COST = 1
NO_TESTS_COST = 5
LOW_TYPE_HINTS_COST = 2
TYPE_HINT_THRESHOLD = 0.5
NO_README_COST = 2
NO_LICENSE_COST = 1
NO_GITIGNORE_COST = 1
NO_LINTER_CONFIG_COST = 1
NO_TYPE_CHECKER_COST = 1
NO_PY_TYPED_COST = 1
LOW_TEST_RATIO_COST = 2
VERY_LOW_TEST_RATIO_COST = 4

# Imports
STAR_IMPORT_COST = 1
CIRCULAR_IMPORT_COST = 3

# Exceptions
BARE_EXCEPT_COST = 2
SILENT_EXCEPTION_COST = 1

# Zen
DEEP_NESTING_COST = 1
LONG_FUNCTION_COST = 1
MANY_PARAMS_COST = 0.5
LARGE_CLASS_COST = 1
DENSE_LINE_COST = 0.5


@dataclass
class Finding:
    """A single diagnostic finding from an analyzer."""
    category: str
    rule: str
    message: str
    file: str = ""
    line: int = 0
    severity: str = "medium"
    cost: float = 0.0


@dataclass
class AnalyzerResult:
    """Result from running an analyzer, containing findings and deduction."""
    category: str
    findings: list[Finding] = field(default_factory=list)
    deduction: float = 0.0
    error: str | None = None
