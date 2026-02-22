"""Eval runner: orchestrates agent runs, rater dispatch, and report generation."""

import json
import sys
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.agent import run_agent, AgentResult
from src.config import PROJECT_ROOT, load_agent_config
from src.eval.trajectory import evaluate_trajectory, TrajectoryItem, TrajectoryResult
from src.eval.onesided import evaluate_onesided, OnesidedItem, OnesidedResult, MAX_EVAL_CONCURRENCY


def _load_eval_config() -> dict:
    path = PROJECT_ROOT / "configs" / "evals.yaml"
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _load_judge_prompts() -> dict[str, str]:
    path = PROJECT_ROOT / "prompts" / "evals.yaml"
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _load_template() -> str:
    path = PROJECT_ROOT / "eval_outputs" / "TEMPLATE.md"
    with open(path) as f:
        return f.read()


def _load_dataset(path_str: str) -> list[dict]:
    path = PROJECT_ROOT / path_str
    with open(path) as f:
        return yaml.safe_load(f) or []


def _run_agent_on_dataset(
    dataset: list[dict],
    agent_config_name: str,
    verbose: bool = False,
) -> list[tuple[dict, AgentResult]]:
    """Run the agent on every item in a dataset concurrently."""
    config = load_agent_config(agent_config_name)

    def _run_one(idx: int, item: dict) -> tuple[int, dict, AgentResult]:
        if verbose:
            print(
                f"  [{idx + 1}/{len(dataset)}] {item['query'][:60]}...",
                file=sys.stderr,
            )
        result = run_agent(query=item["query"], agent_config=config)
        return idx, item, result

    results = [None] * len(dataset)
    with ThreadPoolExecutor(max_workers=MAX_EVAL_CONCURRENCY) as executor:
        futures = {executor.submit(_run_one, i, item): i for i, item in enumerate(dataset)}
        for future in as_completed(futures):
            idx, item, result = future.result()
            results[idx] = (item, result)

    return results


def _serialize_messages(messages: list) -> list:
    """Convert message list to JSON-safe format."""
    serialized = []
    for msg in messages:
        if isinstance(msg, dict):
            serialized.append(msg)
        else:
            serialized.append(str(msg))
    return serialized


def _dump_transcripts(
    run_dir: Path,
    side: str,
    dataset_name: str,
    agent_results: list[tuple[dict, AgentResult]],
) -> None:
    """Dump all agent transcripts for a dataset into a single JSON file."""
    transcript_dir = run_dir / f"transcripts_{side}"
    transcript_dir.mkdir(exist_ok=True)
    records = []
    for dataset_item, result in agent_results:
        records.append(
            {
                "query": dataset_item["query"],
                "dataset_item": dataset_item,
                "final_text": result.final_text,
                "turn_count": result.turn_count,
                "tool_calls_made": result.tool_calls_made,
                "messages": _serialize_messages(result.messages),
            }
        )
    path = transcript_dir / f"{dataset_name}.json"
    path.write_text(json.dumps(records, indent=2, default=str))


def _dump_trajectory_judge(
    run_dir: Path,
    dataset_name: str,
    side: str,
    result: TrajectoryResult,
) -> None:
    """Dump trajectory judge output."""
    judge_dir = run_dir / "judge_outputs"
    judge_dir.mkdir(exist_ok=True)
    output = {
        "dataset": dataset_name,
        "side": side,
        "metrics": {
            "accuracy": result.accuracy,
            "precision": result.precision,
            "recall": result.recall,
            "f1": result.f1,
        },
        "items": [asdict(item) for item in result.items],
    }
    filename = f"{dataset_name}_{side}.json" if side != "base" else f"{dataset_name}.json"
    path = judge_dir / filename
    # If base already written and we're writing test, use _test suffix
    if side == "base":
        path = judge_dir / f"{dataset_name}_base.json"
    else:
        path = judge_dir / f"{dataset_name}_test.json"
    path.write_text(json.dumps(output, indent=2, default=str))


def _dump_onesided_judge(
    run_dir: Path,
    dataset_name: str,
    side: str,
    result: OnesidedResult,
) -> None:
    """Dump onesided judge output."""
    judge_dir = run_dir / "judge_outputs"
    judge_dir.mkdir(exist_ok=True)
    output = {
        "dataset": dataset_name,
        "side": side,
        "dimensions": result.dimensions,
        "mean_scores": result.mean_scores,
        "items": [
            {
                "query": item.query,
                "scores": item.scores,
                "explanation": item.explanation,
            }
            for item in result.items
        ],
    }
    path = judge_dir / f"{dataset_name}_{side}.json"
    path.write_text(json.dumps(output, indent=2, default=str))


def _load_trajectory_from_disk(run_dir: Path, side: str) -> dict[str, TrajectoryResult]:
    """Load all trajectory judge outputs for a side from disk."""
    judge_dir = run_dir / "judge_outputs"
    results = {}
    if not judge_dir.exists():
        return results
    for path in judge_dir.glob(f"*_{side}.json"):
        data = json.loads(path.read_text())
        if "metrics" not in data:
            continue
        ds_name = data["dataset"]
        items = [
            TrajectoryItem(**item) for item in data["items"]
        ]
        results[ds_name] = TrajectoryResult(
            items=items,
            accuracy=data["metrics"]["accuracy"],
            precision=data["metrics"]["precision"],
            recall=data["metrics"]["recall"],
            f1=data["metrics"]["f1"],
        )
    return results


def _load_onesided_from_disk(run_dir: Path, side: str) -> dict[str, OnesidedResult]:
    """Load all onesided judge outputs for a side from disk."""
    judge_dir = run_dir / "judge_outputs"
    results = {}
    if not judge_dir.exists():
        return results
    for path in judge_dir.glob(f"*_{side}.json"):
        data = json.loads(path.read_text())
        if "dimensions" not in data:
            continue
        ds_name = data["dataset"]
        items = [
            OnesidedItem(
                query=item["query"],
                response="",
                scores=item["scores"],
                explanation=item.get("explanation", ""),
                context="",
            )
            for item in data["items"]
        ]
        results[ds_name] = OnesidedResult(
            dataset_name=ds_name,
            dimensions=data["dimensions"],
            items=items,
            mean_scores=data["mean_scores"],
        )
    return results


def _build_trajectory_table(
    base_tr: TrajectoryResult,
    test_tr: Optional[TrajectoryResult] = None,
) -> str:
    if test_tr:

        def _diff_pct(t, b):
            d = t - b
            return f"+{d:.0%}" if d >= 0 else f"{d:.0%}"

        lines = [
            "| Metric | Base | Test | Diff |",
            "|--------|------|------|------|",
            f"| Accuracy  | {base_tr.accuracy:.0%} | {test_tr.accuracy:.0%} | {_diff_pct(test_tr.accuracy, base_tr.accuracy)} |",
            f"| Precision | {base_tr.precision:.0%} | {test_tr.precision:.0%} | {_diff_pct(test_tr.precision, base_tr.precision)} |",
            f"| Recall    | {base_tr.recall:.0%} | {test_tr.recall:.0%} | {_diff_pct(test_tr.recall, base_tr.recall)} |",
            f"| F1        | {base_tr.f1:.0%} | {test_tr.f1:.0%} | {_diff_pct(test_tr.f1, base_tr.f1)} |",
        ]
    else:
        lines = [
            "| Metric    | Value  |",
            "|-----------|--------|",
            f"| Accuracy  | {base_tr.accuracy:.0%} |",
            f"| Precision | {base_tr.precision:.0%} |",
            f"| Recall    | {base_tr.recall:.0%} |",
            f"| F1        | {base_tr.f1:.0%} |",
        ]
    return "\n".join(lines)


def _build_rubric_table(
    onesided_base: dict[str, OnesidedResult],
    onesided_test: Optional[dict[str, OnesidedResult]] = None,
) -> str:
    sections = []
    for ds_name, base_osr in onesided_base.items():
        test_osr = onesided_test.get(ds_name) if onesided_test else None
        n = len(base_osr.items)
        lines = [f"### {ds_name}", "", f"n={n}", ""]
        if test_osr:
            lines.append("| Dimension | Base | Test | Diff |")
            lines.append("|-----------|------|------|------|")
            for dim in base_osr.dimensions:
                base_val = base_osr.mean_scores.get(dim, 0)
                test_val = test_osr.mean_scores.get(dim, 0)
                diff = test_val - base_val
                diff_str = f"+{diff:.1f}" if diff >= 0 else f"{diff:.1f}"
                lines.append(f"| {dim} | {base_val:.1f} | {test_val:.1f} | {diff_str} |")
        else:
            lines.append("| Dimension | Mean |")
            lines.append("|-----------|------|")
            for dim in base_osr.dimensions:
                val = base_osr.mean_scores.get(dim, 0)
                lines.append(f"| {dim} | {val:.1f} |")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def run_eval(
    base_agent: str,
    test_agent: Optional[str] = None,
    verbose: bool = False,
    run_id: Optional[str] = None,
) -> Path:
    """Run all evals defined in configs/evals.yaml.

    Args:
        base_agent: Agent config name for the base side.
        test_agent: Agent config name for the test side (optional).
        verbose: Print progress to stderr.
        run_id: Existing run folder name to resume (e.g. '2026-02-22_14-30-00').

    Returns:
        Path to the generated run directory.
    """
    config = _load_eval_config()
    judge_prompts = _load_judge_prompts()
    template = _load_template()
    has_test = test_agent is not None

    # Create or reuse run directory
    if run_id:
        run_dir = PROJECT_ROOT / "eval_outputs" / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Run directory not found: {run_dir}")
        if verbose:
            print(f"Resuming run: {run_dir}", file=sys.stderr)
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_dir = PROJECT_ROOT / "eval_outputs" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    base_trajectory: Optional[TrajectoryResult] = None
    test_trajectory: Optional[TrajectoryResult] = None
    onesided_base: dict[str, OnesidedResult] = {}
    onesided_test: dict[str, OnesidedResult] = {}

    for ds_name, ds_config in config.items():
        dataset = _load_dataset(ds_config["path"])
        rater = ds_config["rater"]

        if verbose:
            print(f"\n=== Dataset: {ds_name} (rater: {rater}) ===", file=sys.stderr)

        # Run base agent
        if verbose:
            print(f"Running base agent '{base_agent}' on {ds_name}...", file=sys.stderr)
        results_base = _run_agent_on_dataset(dataset, base_agent, verbose=verbose)
        _dump_transcripts(run_dir, "base", ds_name, results_base)

        # Run test agent if provided
        results_test = None
        if has_test:
            if verbose:
                print(f"Running test agent '{test_agent}' on {ds_name}...", file=sys.stderr)
            results_test = _run_agent_on_dataset(dataset, test_agent, verbose=verbose)
            _dump_transcripts(run_dir, "test", ds_name, results_test)

        if rater == "trajectory":
            base_trajectory = evaluate_trajectory(results_base)
            _dump_trajectory_judge(run_dir, ds_name, "base", base_trajectory)
            if has_test and results_test:
                test_trajectory = evaluate_trajectory(results_test)
                _dump_trajectory_judge(run_dir, ds_name, "test", test_trajectory)

        elif rater == "onesided":
            judge_model = ds_config.get("judge_model", "claude-haiku-4-5-20251001")
            judge_max_tokens = ds_config.get("judge_max_tokens", 1024)
            dimensions = ds_config["dimensions"]

            if verbose:
                print(f"Judging base results for {ds_name}...", file=sys.stderr)
            onesided_base[ds_name] = evaluate_onesided(
                dataset_name=ds_name,
                agent_results=results_base,
                dimensions=dimensions,
                prompt_template=judge_prompts["onesided"],
                judge_model=judge_model,
                judge_max_tokens=judge_max_tokens,
            )
            _dump_onesided_judge(run_dir, ds_name, "base", onesided_base[ds_name])

            if has_test and results_test:
                if verbose:
                    print(f"Judging test results for {ds_name}...", file=sys.stderr)
                onesided_test[ds_name] = evaluate_onesided(
                    dataset_name=ds_name,
                    agent_results=results_test,
                    dimensions=dimensions,
                    prompt_template=judge_prompts["onesided"],
                    judge_model=judge_model,
                    judge_max_tokens=judge_max_tokens,
                )
                _dump_onesided_judge(run_dir, ds_name, "test", onesided_test[ds_name])

        else:
            raise ValueError(f"Unknown rater type: {rater}")

    # Load all results from disk (includes both current run and previous runs)
    all_trajectory_base = _load_trajectory_from_disk(run_dir, "base")
    all_trajectory_test = _load_trajectory_from_disk(run_dir, "test")
    all_onesided_base = _load_onesided_from_disk(run_dir, "base")
    all_onesided_test = _load_onesided_from_disk(run_dir, "test")

    # Build table strings and fill template
    # Use the first trajectory result found (there should be at most one)
    trajectory_table = "N/A"
    if all_trajectory_base:
        first_base_tr = next(iter(all_trajectory_base.values()))
        first_test_tr = next(iter(all_trajectory_test.values())) if all_trajectory_test else None
        trajectory_table = _build_trajectory_table(first_base_tr, first_test_tr)

    rubric_table = "N/A"
    if all_onesided_base:
        rubric_table = _build_rubric_table(
            all_onesided_base,
            all_onesided_test if all_onesided_test else None,
        )

    report = template.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        base_agent=base_agent,
        test_agent_line=f"**Test agent:** `{test_agent}`" if has_test else "",
        trajectory_table=trajectory_table,
        rubric_table=rubric_table,
    )

    report_path = run_dir / "report.md"
    report_path.write_text(report)

    if verbose:
        print(f"\nReport written to: {report_path}", file=sys.stderr)

    return run_dir
