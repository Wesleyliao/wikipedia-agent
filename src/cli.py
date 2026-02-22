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
    "--config", "config_name",
    default="default",
    help="Agent config name (top-level key in configs/agents.yaml).",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Print tool calls to stderr.",
)
def ask(query, config_name, verbose):
    """Ask the Wikipedia agent a question.

    \b
    Examples:
        python -m src.cli ask "What is the capital of France?"
        python -m src.cli ask "Explain quantum entanglement" --config fast -v
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
    "--verbose", "-v",
    is_flag=True,
    help="Print progress to stderr.",
)
def evals(base, test, verbose):
    """Run all evaluations defined in configs/evals.yaml.

    \b
    BASE is the agent config name for the base side.

    \b
    Examples:
        python -m src.cli evals default
        python -m src.cli evals default --test fast -v
    """
    from src.eval.runner import run_eval

    run_dir = run_eval(base_agent=base, test_agent=test, verbose=verbose)
    click.echo(f"Eval run complete: {run_dir}")


if __name__ == "__main__":
    cli()
