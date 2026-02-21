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
@click.argument("eval_config", default="default")
def evals(eval_config):
    """Run evaluations against the agent.

    \b
    EVAL_CONFIG is the eval config name (top-level key in configs/evals.yaml).
    """
    # TODO: implement eval runner
    #   - load eval config from configs/evals.yaml[eval_config]
    #   - load dataset from the path specified in eval config
    #   - for each question, call run_agent() with the configured agent_config/prompts
    #   - write results to outputs/
    raise click.ClickException("Eval runner not yet implemented.")


if __name__ == "__main__":
    cli()
