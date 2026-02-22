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
python -m src.cli ask "Who invented the telephone?" --config agent_v1

# Verbose mode (prints tool calls to stderr)
python -m src.cli ask "What is CRISPR?" -v
```

### Evals (not yet implemented)

```bash
python -m src.cli evals default
```