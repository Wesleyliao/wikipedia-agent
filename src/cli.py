"""CLI entrypoint using Click."""

import click

from src.agent import run_agent
from src.config import load_agent_config


@click.group()
def cli():
    """Wikipedia agent CLI."""
    pass


@cli.command()
@click.argument("query")
@click.option(
    "--config",
    "config_name",
    default="agent_v1",
    help="Agent config name (top-level key in configs/agents.yaml).",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Print tool calls to stderr.",
)
def ask(query, config_name, verbose):
    """Ask the Wikipedia agent a question.

    \b
    Examples:
        python -m src.cli ask "What is the capital of France?"
        python -m src.cli ask "Explain quantum entanglement" --config agent_v1 -v
    """
    agent_config = load_agent_config(config_name)

    result = run_agent(
        query=query,
        agent_config=agent_config,
        verbose=verbose,
    )

    click.echo(result.final_text)


@cli.command()
@click.argument("base")
@click.option(
    "--test",
    default=None,
    help="Test agent config name for side-by-side comparison.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Print progress to stderr.",
)
@click.option(
    "--run-id",
    default=None,
    help="Resume a previous run by its folder name (e.g. 2026-02-22_14-30-00).",
)
def evals(base, test, verbose, run_id):
    """Run all evaluations defined in configs/evals.yaml.

    \b
    BASE is the agent config name for the base side.

    \b
    Examples:
        python -m src.cli evals agent_v1
        python -m src.cli evals agent_v0 --test agent_v1 -v
        python -m src.cli evals agent_v1 --run-id 2026-02-22_14-30-00
    """
    from src.eval.runner import run_eval

    run_dir = run_eval(base_agent=base, test_agent=test, verbose=verbose, run_id=run_id)
    click.echo(f"Eval run complete: {run_dir}")


if __name__ == "__main__":
    cli()
