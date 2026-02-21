# Wikipedia Agent

A CLI tool that uses a Claude-powered AI agent to answer questions using Wikipedia.

## Setup

### 1. Create the Conda environment

```bash
conda env create -f environment.yml
conda activate wikipedia-agent
```

### 2. Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

### Ask a question

```bash
python -m src.cli ask "What is quantum entanglement?"
```

### Options

```bash
# Use a different agent config
python -m src.cli ask "Who invented the telephone?" --config fast

# Verbose mode (prints tool calls to stderr)
python -m src.cli ask "What is CRISPR?" -v
```

### Evals (not yet implemented)

```bash
python -m src.cli evals default
```

## Project Structure

```
wikipedia-agent/
  environment.yml              # Conda environment
  requirements.txt             # Python dependencies
  prompts/
    system_instructions.yaml   # System prompts (keyed by name)
    tool_descriptions.yaml     # Tool description variants (keyed by name)
    autoevals.yaml             # Autoeval prompts (keyed by name)
  configs/
    agents.yaml                # Agent configs (keyed by name)
    evals.yaml                 # Eval configs (keyed by name)
  src/
    cli.py                     # Click CLI (ask + evals subcommands)
    agent.py                   # Agent loop + run_agent() entrypoint
    tools.py                   # search_wikipedia tool
    config.py                  # Config/prompt loading
    prompts.py                 # Prompt utilities for evals
  data/                        # Eval datasets
  outputs/                     # Eval outputs
```

## Agent Config

Agent configs live in `configs/agents.yaml` as top-level keys:

```yaml
default:
  model: claude-sonnet-4-20250514
  max_tokens: 4096
  max_turns: 10
  system_instruction: default    # -> key in prompts/system_instructions.yaml
  tool_description: default      # -> key in prompts/tool_descriptions.yaml

fast:
  model: claude-haiku-4-5-20251001
  max_tokens: 2048
  max_turns: 5
  system_instruction: default
  tool_description: default
```

## Programmatic Usage (for evals)

```python
from src.agent import run_agent
from src.config import AgentConfig

# Name-based (resolves from YAML files)
result = run_agent("What is DNA?", config_name="default")

# Object-based (for programmatic control)
config = AgentConfig(model="claude-sonnet-4-20250514", max_turns=5)
result = run_agent(
    "What is DNA?",
    agent_config=config,
    system_prompt="You are a concise research assistant...",
)

# Access results
print(result.final_text)
print(result.turn_count)
print(result.tool_calls_made)
```
