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
python -m src.cli ask "What is quantum entanglement?" -v
```

### Options

```bash
# Use a different agent config
python -m src.cli ask "Who invented the telephone?" --config agent_v1

# Verbose mode (prints tool calls)
python -m src.cli ask "What is CRISPR?" -v
```

### Evals

To compare `agent_v2` as base model against `agent_v3` as test model:

```bash
python -m src.cli evals agent_v2 --test agent_v3 -v
```

This will run the evals and output a report in `eval_outputs/`.