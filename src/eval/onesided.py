"""One-sided rubric autorater using LLM-as-judge with multi-dimension scoring."""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import anthropic

from src.agent import AgentResult

MAX_EVAL_CONCURRENCY = 2


@dataclass
class OnesidedItem:
    query: str
    response: str
    scores: dict[str, int]
    explanation: str
    context: str


@dataclass
class OnesidedResult:
    dataset_name: str
    dimensions: list[str] = field(default_factory=list)
    items: list[OnesidedItem] = field(default_factory=list)
    mean_scores: dict[str, float] = field(default_factory=dict)


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


def _format_dimensions(dimensions: dict[str, str]) -> str:
    """Format dimension rubrics for the judge prompt."""
    parts = []
    for name, rubric in dimensions.items():
        parts.append(f"### {name}\n{rubric.strip()}")
    return "\n\n".join(parts)


def _format_score_keys(dimensions: dict[str, str]) -> str:
    """Build the JSON keys hint for the prompt, e.g. '"correctness": N, "tone_and_style": N'."""
    return ", ".join(f'"{name}": N' for name in dimensions)


def _parse_scores(
    judge_response: str,
    dimensions: dict[str, str],
) -> tuple[dict[str, int], str]:
    """Parse multi-dimension scores from judge JSON response.

    Returns (scores_dict, explanation).
    """
    # Try to extract JSON from the response
    try:
        # Find JSON object in response
        match = re.search(r"\{.*\}", judge_response, re.DOTALL)
        if match:
            data = json.loads(match.group())
            raw_scores = data.get("scores", {})
            explanation = data.get("reasoning", data.get("explanation", ""))
            scores = {}
            for dim in dimensions:
                val = raw_scores.get(dim, 2)
                scores[dim] = max(1, min(3, int(val)))
            return scores, explanation
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    # Fallback: default scores
    return {dim: 2 for dim in dimensions}, f"[PARSE ERROR] {judge_response}"


def judge_onesided(
    query: str,
    response: str,
    context: str,
    dimensions: dict[str, str],
    prompt_template: str,
    client: anthropic.Anthropic,
    judge_model: str,
    judge_max_tokens: int,
) -> tuple[dict[str, int], str]:
    """Make a single judge LLM call. Returns (scores_dict, explanation)."""
    prompt = prompt_template.format(
        dimensions=_format_dimensions(dimensions),
        query=query,
        context=context,
        response=response,
        score_keys=_format_score_keys(dimensions),
    )
    judge_response = client.messages.create(
        model=judge_model,
        max_tokens=judge_max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_scores(judge_response.content[0].text, dimensions)


def evaluate_onesided(
    dataset_name: str,
    agent_results: list[tuple[dict, AgentResult]],
    dimensions: dict[str, str],
    prompt_template: str,
    judge_model: str,
    judge_max_tokens: int,
) -> OnesidedResult:
    """Evaluate a dataset using one-sided LLM-as-judge with multiple dimensions.

    Args:
        dataset_name: Name of the dataset (for the report).
        agent_results: List of (dataset_item, AgentResult) pairs.
        dimensions: Dict mapping dimension name to rubric text.
        prompt_template: The onesided template from prompts/evals.yaml.
        judge_model: Model ID for the judge.
        judge_max_tokens: Max tokens for judge response.
    """
    client = anthropic.Anthropic()
    dim_names = list(dimensions.keys())

    def _judge_item(idx: int, dataset_item: dict, result: AgentResult) -> tuple[int, OnesidedItem]:
        context = _build_context(dataset_item)
        scores, explanation = judge_onesided(
            query=dataset_item["query"],
            response=result.final_text,
            context=context,
            dimensions=dimensions,
            prompt_template=prompt_template,
            client=client,
            judge_model=judge_model,
            judge_max_tokens=judge_max_tokens,
        )
        return idx, OnesidedItem(
            query=dataset_item["query"],
            response=result.final_text,
            scores=scores,
            explanation=explanation,
            context=context,
        )

    # Run judge calls concurrently
    items = [None] * len(agent_results)
    with ThreadPoolExecutor(max_workers=MAX_EVAL_CONCURRENCY) as executor:
        futures = {
            executor.submit(_judge_item, i, dataset_item, result): i
            for i, (dataset_item, result) in enumerate(agent_results)
        }
        for future in as_completed(futures):
            idx, item = future.result()
            items[idx] = item

    # Compute per-dimension means
    mean_scores = {}
    for dim in dim_names:
        vals = [item.scores[dim] for item in items]
        mean_scores[dim] = sum(vals) / len(vals) if vals else 0.0

    return OnesidedResult(
        dataset_name=dataset_name,
        dimensions=dim_names,
        items=items,
        mean_scores=mean_scores,
    )
