"""Score aggregation logic."""

from .rules import CATEGORIES, AnalyzerResult


def compute_score(results: list[AnalyzerResult]) -> int:
    """Compute the overall health score (0-100) from analyzer results."""
    total_deduction = sum(r.deduction for r in results)
    return max(0, int(100 - total_deduction))


def score_label(score: int) -> str:
    """Return a human-readable label for the given score."""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 50:
        return "Needs Work"
    else:
        return "Critical"


def category_score(result: AnalyzerResult) -> int:
    """Compute the score for a single category."""
    cat = CATEGORIES[result.category]
    return int(cat["max_deduction"] - result.deduction)
