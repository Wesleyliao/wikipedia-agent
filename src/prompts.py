"""Prompt utilities for building system prompts programmatically."""

from src.config import load_system_instruction, load_tool_description


def get_system_instruction(name: str = "default") -> str:
    """Load a named system instruction. Convenience wrapper for evals."""
    return load_system_instruction(name)


def get_tool_description(name: str = "default") -> dict[str, str]:
    """Load named tool descriptions. Convenience wrapper for evals."""
    return load_tool_description(name)


def build_system_instruction(base_name: str = "default", suffix: str = "") -> str:
    """Load a base system instruction and append a suffix. Useful for eval variants."""
    base = load_system_instruction(base_name)
    if suffix:
        return base.rstrip() + "\n\n" + suffix
    return base
