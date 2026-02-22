"""Trajectory autorater for tool-triggering evaluation."""

from dataclasses import dataclass, field

from src.agent import AgentResult


@dataclass
class TrajectoryItem:
    query: str
    expected: bool
    actual: bool
    correct: bool


@dataclass
class TrajectoryResult:
    items: list[TrajectoryItem] = field(default_factory=list)
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0


def evaluate_trajectory(
    agent_results: list[tuple[dict, AgentResult]],
) -> TrajectoryResult:
    """Evaluate tool-triggering accuracy from pre-computed agent results.

    Args:
        agent_results: List of (dataset_item, AgentResult) pairs.
            Each dataset_item has keys: query, wiki_tool_call_expected.
    """
    items = []
    tp = fp = tn = fn = 0

    for dataset_item, result in agent_results:
        expected = bool(dataset_item["wiki_tool_call_expected"])
        actual = any(
            tc["tool"] == "search_wikipedia" for tc in result.tool_calls_made
        )
        correct = expected == actual
        items.append(TrajectoryItem(
            query=dataset_item["query"],
            expected=expected,
            actual=actual,
            correct=correct,
        ))

        if expected and actual:
            tp += 1
        elif not expected and actual:
            fp += 1
        elif expected and not actual:
            fn += 1
        else:
            tn += 1

    n = len(items)
    accuracy = (tp + tn) / n if n else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return TrajectoryResult(
        items=items,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
    )
