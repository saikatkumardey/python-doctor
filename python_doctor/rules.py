"""Rule definitions and scoring categories."""

from dataclasses import dataclass, field

CATEGORIES = {
    "security": {"emoji": "🔒", "label": "Security", "max_deduction": 25},
    "lint": {"emoji": "🧹", "label": "Lint", "max_deduction": 20},
    "complexity": {"emoji": "🔄", "label": "Complexity", "max_deduction": 15},
    "structure": {"emoji": "🏗", "label": "Structure", "max_deduction": 10},
    "imports": {"emoji": "🔗", "label": "Imports", "max_deduction": 5},
    "exceptions": {"emoji": "⚡", "label": "Exceptions", "max_deduction": 10},
    "zen": {"emoji": "🧘", "label": "Zen", "max_deduction": 15},
}

# Security
BANDIT_SEVERITY_COST = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

# Lint
RUFF_ERROR_COST = 1.0
RUFF_WARNING_COST = 0.5

# Complexity
COMPLEXITY_COST = {10: 2, 20: 5}

# Structure
LARGE_FILE_THRESHOLD = 500
LARGE_FILE_COST = 2
NO_TESTS_COST = 5
LOW_TYPE_HINTS_COST = 5
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
DEEP_NESTING_COST = 2
LONG_FUNCTION_COST = 2
MANY_PARAMS_COST = 1
LARGE_CLASS_COST = 2
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
