"""One-sided rubric autorater using LLM-as-judge."""

import re
from dataclasses import dataclass, field

import anthropic

from src.agent import AgentResult


@dataclass
class OnesidedItem:
    query: str
    response: str
    score: int
    explanation: str
    context: str


@dataclass
class OnesidedResult:
    dataset_name: str
    items: list[OnesidedItem] = field(default_factory=list)
    mean_score: float = 0.0
    score_distribution: dict[int, int] = field(default_factory=dict)


def _build_context(dataset_item: dict) -> str:
    """Build context string from dataset-specific fields for the judge."""
    parts = []
    if "ground_truth" in dataset_item:
        parts.append(f"Ground truth answer: {dataset_item['ground_truth']}")
    if "false_premise" in dataset_item:
        parts.append(f"False premise in query: {dataset_item['false_premise']}")
    if "ambiguous_entity" in dataset_item:
        parts.append(f"Ambiguous entity: {dataset_item['ambiguous_entity']}")
    return "\n".join(parts) if parts else "No additional context."


def _parse_score(judge_response: str) -> tuple[int, str]:
    """Extract score and explanation from judge response.

    Expects a line matching 'Score: N' near the end.
    """
    lines = judge_response.strip().split("\n")
    for i in range(len(lines) - 1, -1, -1):
        match = re.match(r"Score:\s*(\d)", lines[i].strip())
        if match:
            score = max(1, min(5, int(match.group(1))))
            explanation = "\n".join(lines[:i]).strip()
            return score, explanation
    return 3, f"[PARSE ERROR] {judge_response}"


def judge_onesided(
    query: str,
    response: str,
    context: str,
    rubric: str,
    prompt_template: str,
    client: anthropic.Anthropic,
    judge_model: str,
    judge_max_tokens: int,
) -> tuple[int, str]:
    """Make a single judge LLM call. Returns (score, explanation)."""
    prompt = prompt_template.format(
        rubric=rubric,
        query=query,
        context=context,
        response=response,
    )
    judge_response = client.messages.create(
        model=judge_model,
        max_tokens=judge_max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_score(judge_response.content[0].text)


def evaluate_onesided(
    dataset_name: str,
    agent_results: list[tuple[dict, AgentResult]],
    rubric: str,
    prompt_template: str,
    judge_model: str,
    judge_max_tokens: int,
) -> OnesidedResult:
    """Evaluate a dataset using one-sided LLM-as-judge.

    Args:
        dataset_name: Name of the dataset (for the report).
        agent_results: List of (dataset_item, AgentResult) pairs.
        rubric: The rubric text for this dataset.
        prompt_template: The onesided template from prompts/evals.yaml.
        judge_model: Model ID for the judge.
        judge_max_tokens: Max tokens for judge response.
    """
    client = anthropic.Anthropic()
    items = []

    for dataset_item, result in agent_results:
        context = _build_context(dataset_item)
        score, explanation = judge_onesided(
            query=dataset_item["query"],
            response=result.final_text,
            context=context,
            rubric=rubric,
            prompt_template=prompt_template,
            client=client,
            judge_model=judge_model,
            judge_max_tokens=judge_max_tokens,
        )
        items.append(OnesidedItem(
            query=dataset_item["query"],
            response=result.final_text,
            score=score,
            explanation=explanation,
            context=context,
        ))

    scores = [item.score for item in items]
    mean_score = sum(scores) / len(scores) if scores else 0.0
    distribution = {s: scores.count(s) for s in range(1, 6)}

    return OnesidedResult(
        dataset_name=dataset_name,
        items=items,
        mean_score=mean_score,
        score_distribution=distribution,
    )
