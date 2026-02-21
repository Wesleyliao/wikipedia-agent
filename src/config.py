"""Config and prompt loading from YAML files."""

from dataclasses import dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class AgentConfig:
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    max_turns: int = 10
    system_instruction: str = "default"
    tool_description: str = "default"


def load_agent_config(name: str = "default") -> AgentConfig:
    """Load agent config from configs/agents.yaml under the given key."""
    path = PROJECT_ROOT / "configs" / "agents.yaml"
    if not path.exists():
        return AgentConfig()
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    entry = data.get(name)
    if entry is None:
        raise KeyError(f"Agent config '{name}' not found in {path}")
    return AgentConfig(**{k: v for k, v in entry.items() if k in AgentConfig.__dataclass_fields__})


def load_system_instruction(name: str = "default") -> str:
    """Load system instruction from prompts/system_instructions.yaml under the given key."""
    path = PROJECT_ROOT / "prompts" / "system_instructions.yaml"
    if not path.exists():
        raise FileNotFoundError(f"System instructions file not found: {path}")
    with open(path) as f:
        data = yaml.safe_load(f)
    if name not in data:
        raise KeyError(f"System instruction '{name}' not found in {path}")
    return data[name]


def load_tool_description(name: str = "default") -> dict[str, str]:
    """Load tool descriptions from prompts/tool_descriptions.yaml under the given key.

    Returns a dict mapping tool name to description string.
    """
    path = PROJECT_ROOT / "prompts" / "tool_descriptions.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Tool descriptions file not found: {path}")
    with open(path) as f:
        data = yaml.safe_load(f)
    if name not in data:
        raise KeyError(f"Tool description '{name}' not found in {path}")
    return data[name]
