"""Agent loop using Anthropic SDK tool-use."""

import sys
from dataclasses import dataclass, field
from typing import Optional

import anthropic

from src.config import AgentConfig, load_agent_config, load_system_instruction, load_tool_description
from src.tools import TOOL_MAP, build_tool_definition


@dataclass
class AgentResult:
    """Return value from run_agent, useful for evals."""

    final_text: str
    messages: list = field(repr=False)
    turn_count: int = 0
    tool_calls_made: list = field(default_factory=list)


def run_agent(
    query: str,
    *,
    agent_config: Optional[AgentConfig] = None,
    system_prompt: Optional[str] = None,
    tool_descriptions: Optional[dict[str, str]] = None,
    config_name: str = "default",
    verbose: bool = False,
) -> AgentResult:
    """Run the Wikipedia agent on a single query.

    Can be called from the CLI with a config name, or from evals
    with pre-loaded objects.

    Args:
        query: The user question to answer.
        agent_config: Pre-built config. If None, loaded from config_name.
        system_prompt: Pre-built system prompt. If None, loaded per agent_config.system_instruction.
        tool_descriptions: Pre-loaded tool descriptions dict. If None, loaded per agent_config.tool_description.
        config_name: Name of agent config YAML (without .yaml).
        verbose: Print intermediate tool calls to stderr.

    Returns:
        AgentResult with final response, message history, turn count,
        and tool call records.
    """
    if agent_config is None:
        agent_config = load_agent_config(config_name)
    if system_prompt is None:
        system_prompt = load_system_instruction(agent_config.system_instruction)
    if tool_descriptions is None:
        tool_descriptions = load_tool_description(agent_config.tool_description)

    client = anthropic.Anthropic()
    tools = [build_tool_definition(tool_descriptions)]
    messages = [{"role": "user", "content": query}]
    tool_calls_made = []

    turn_count = 0
    for turn_count in range(1, agent_config.max_turns + 1):
        response = client.messages.create(
            model=agent_config.model,
            max_tokens=agent_config.max_tokens,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason != "tool_use":
            break

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if verbose:
                print(f"[tool call] {block.name}({block.input})", file=sys.stderr)

            tool_fn = TOOL_MAP.get(block.name)
            if tool_fn is None:
                result_text = f"Error: unknown tool '{block.name}'"
            else:
                try:
                    result_text = tool_fn(**block.input)
                except Exception as e:
                    result_text = f"Error calling {block.name}: {e}"

            tool_calls_made.append({
                "tool": block.name,
                "input": block.input,
                "output": result_text,
            })
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_text,
            })

        messages.append({"role": "user", "content": tool_results})

    # Extract final text from last assistant response
    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text

    return AgentResult(
        final_text=final_text,
        messages=messages,
        turn_count=turn_count,
        tool_calls_made=tool_calls_made,
    )
