"""Eval runner: orchestrates agent runs, rater dispatch, and report generation."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from src.agent import run_agent, AgentResult
from src.config import PROJECT_ROOT, load_agent_config
from src.eval.trajectory import evaluate_trajectory, TrajectoryResult
from src.eval.onesided import evaluate_onesided, OnesidedResult


def _load_eval_config() -> dict:
    path = PROJECT_ROOT / "configs" / "evals.yaml"
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _load_judge_prompts() -> dict[str, str]:
    path = PROJECT_ROOT / "prompts" / "evals.yaml"
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _load_dataset(path_str: str) -> list[dict]:
    path = PROJECT_ROOT / path_str
    with open(path) as f:
        return yaml.safe_load(f) or []


def _run_agent_on_dataset(
    dataset: list[dict],
    agent_config_name: str,
    verbose: bool = False,
) -> list[tuple[dict, AgentResult]]:
    """Run the agent on every item in a dataset."""
    config = load_agent_config(agent_config_name)
    results = []
    for i, item in enumerate(dataset):
        if verbose:
            print(
                f"  [{i + 1}/{len(dataset)}] {item['query'][:60]}...",
                file=sys.stderr,
            )
        result = run_agent(query=item["query"], agent_config=config)
        results.append((item, result))
    return results


def _dump_transcripts(
    run_dir: Path,
    side: str,
    dataset_name: str,
    agent_results: list[tuple[dict, AgentResult]],
) -> None:
    """Dump raw agent transcripts as JSON files."""
    transcript_dir = run_dir / f"transcripts_{side}"
    transcript_dir.mkdir(exist_ok=True)
    for i, (dataset_item, result) in enumerate(agent_results):
        record = {
            "query": dataset_item["query"],
            "dataset_item": dataset_item,
            "final_text": result.final_text,
            "turn_count": result.turn_count,
            "tool_calls_made": result.tool_calls_made,
            "messages": _serialize_messages(result.messages),
        }
        path = transcript_dir / f"{dataset_name}_{i + 1:03d}.json"
        path.write_text(json.dumps(record, indent=2, default=str))


def _serialize_messages(messages: list) -> list:
    """Convert message list to JSON-safe format."""
    serialized = []
    for msg in messages:
        if isinstance(msg, dict):
            serialized.append(msg)
        else:
            serialized.append(str(msg))
    return serialized


def _render_report(
    base_agent: str,
    test_agent: Optional[str],
    trajectory_results: dict[str, TrajectoryResult],
    onesided_base: dict[str, OnesidedResult],
    onesided_test: dict[str, OnesidedResult],
) -> str:
    """Render the summary markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    has_test = test_agent is not None

    lines = [
        "# Eval Report",
        f"**Generated:** {timestamp}",
        f"**Base agent:** `{base_agent}`",
    ]
    if has_test:
        lines.append(f"**Test agent:** `{test_agent}`")
    lines.append("")

    # --- Trajectory section ---
    if trajectory_results:
        lines.append("## Trajectory (Tool Triggering)")
        lines.append("")
        if has_test:
            base_tr = trajectory_results.get("triggering_base")
            test_tr = trajectory_results.get("triggering_test")
            if base_tr and test_tr:
                lines.append("| Metric | Base | Test |")
                lines.append("|--------|------|------|")
                lines.append(f"| Accuracy  | {base_tr.accuracy:.2%} | {test_tr.accuracy:.2%} |")
                lines.append(f"| Precision | {base_tr.precision:.2%} | {test_tr.precision:.2%} |")
                lines.append(f"| Recall    | {base_tr.recall:.2%} | {test_tr.recall:.2%} |")
                lines.append(f"| F1        | {base_tr.f1:.2%} | {test_tr.f1:.2%} |")
        else:
            for name, tr in trajectory_results.items():
                lines.append("| Metric    | Value  |")
                lines.append("|-----------|--------|")
                lines.append(f"| Accuracy  | {tr.accuracy:.2%} |")
                lines.append(f"| Precision | {tr.precision:.2%} |")
                lines.append(f"| Recall    | {tr.recall:.2%} |")
                lines.append(f"| F1        | {tr.f1:.2%} |")
        lines.append("")

    # --- Rubric scores section ---
    if onesided_base:
        lines.append("## Rubric Scores")
        lines.append("")

        if has_test and onesided_test:
            lines.append("| Dataset | Base Mean | Test Mean | Base Distribution (1-5) | Test Distribution (1-5) |")
            lines.append("|---------|-----------|-----------|-------------------------|-------------------------|")
            for ds_name, base_osr in onesided_base.items():
                test_osr = onesided_test.get(ds_name)
                bd = base_osr.score_distribution
                base_dist = f"{bd.get(1,0)}/{bd.get(2,0)}/{bd.get(3,0)}/{bd.get(4,0)}/{bd.get(5,0)}"
                if test_osr:
                    td = test_osr.score_distribution
                    test_dist = f"{td.get(1,0)}/{td.get(2,0)}/{td.get(3,0)}/{td.get(4,0)}/{td.get(5,0)}"
                    lines.append(
                        f"| {ds_name} | {base_osr.mean_score:.2f} | "
                        f"{test_osr.mean_score:.2f} | {base_dist} | {test_dist} |"
                    )
                else:
                    lines.append(
                        f"| {ds_name} | {base_osr.mean_score:.2f} | "
                        f"N/A | {base_dist} | N/A |"
                    )
        else:
            lines.append("| Dataset | Mean Score | 1 | 2 | 3 | 4 | 5 |")
            lines.append("|---------|-----------|---|---|---|---|---|")
            for ds_name, osr in onesided_base.items():
                d = osr.score_distribution
                lines.append(
                    f"| {ds_name} | {osr.mean_score:.2f} | "
                    f"{d.get(1,0)} | {d.get(2,0)} | {d.get(3,0)} | "
                    f"{d.get(4,0)} | {d.get(5,0)} |"
                )
        lines.append("")

    return "\n".join(lines)


def run_eval(
    base_agent: str,
    test_agent: Optional[str] = None,
    verbose: bool = False,
) -> Path:
    """Run all evals defined in configs/evals.yaml.

    Args:
        base_agent: Agent config name for the base side.
        test_agent: Agent config name for the test side (optional).
        verbose: Print progress to stderr.

    Returns:
        Path to the generated run directory.
    """
    config = _load_eval_config()
    judge_prompts = _load_judge_prompts()
    has_test = test_agent is not None

    # Create run directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = PROJECT_ROOT / "eval_outputs" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    trajectory_results: dict[str, TrajectoryResult] = {}
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
            if has_test and results_test:
                trajectory_results["triggering_base"] = evaluate_trajectory(results_base)
                trajectory_results["triggering_test"] = evaluate_trajectory(results_test)
            else:
                trajectory_results[ds_name] = evaluate_trajectory(results_base)

        elif rater == "onesided":
            judge_model = ds_config.get("judge_model", "claude-haiku-4-5-20251001")
            judge_max_tokens = ds_config.get("judge_max_tokens", 1024)

            if verbose:
                print(f"Judging base results for {ds_name}...", file=sys.stderr)
            onesided_base[ds_name] = evaluate_onesided(
                dataset_name=ds_name,
                agent_results=results_base,
                rubric=ds_config["rubric"],
                prompt_template=judge_prompts["onesided"],
                judge_model=judge_model,
                judge_max_tokens=judge_max_tokens,
            )
            if has_test and results_test:
                if verbose:
                    print(f"Judging test results for {ds_name}...", file=sys.stderr)
                onesided_test[ds_name] = evaluate_onesided(
                    dataset_name=ds_name,
                    agent_results=results_test,
                    rubric=ds_config["rubric"],
                    prompt_template=judge_prompts["onesided"],
                    judge_model=judge_model,
                    judge_max_tokens=judge_max_tokens,
                )

        else:
            raise ValueError(f"Unknown rater type: {rater}")

    # Write report
    report = _render_report(
        base_agent, test_agent, trajectory_results, onesided_base, onesided_test,
    )
    report_path = run_dir / "report.md"
    report_path.write_text(report)

    if verbose:
        print(f"\nReport written to: {report_path}", file=sys.stderr)

    return run_dir
