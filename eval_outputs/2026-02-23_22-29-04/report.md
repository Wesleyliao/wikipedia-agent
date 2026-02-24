# Eval Report

**Generated:** 2026-02-23 22:50:08

**Base agent:** `agent_v2`

**Test agent:** `agent_v3`

## Trajectory (Tool Triggering)

n=20

| Metric | Base | Test | Diff |
|--------|------|------|------|
| Accuracy  | 100% | 100% | +0% |
| Precision | 100% | 100% | +0% |
| Recall    | 100% | 100% | +0% |
| F1        | 100% | 100% | +0% |

## Rubric Evaluations

Ratings are on a scale of 1 to 3, where 3 is the best.

### disambiguation

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| disambiguation_handling | 2.4 | 2.2 | -0.1 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.0 | 2.0 | +0.0 |

### adversarial_grounding

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| groundedness | 3.0 | 3.0 | +0.0 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.5 | 2.5 | +0.1 |

### multistep

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| correctness | 2.0 | 2.0 | +0.0 |
| tone_and_style | 2.6 | 2.6 | -0.0 |
| verbosity | 2.2 | 2.2 | +0.0 |

### punting

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| appropriateness | 3.0 | 2.9 | -0.1 |
| helpfulness | 3.0 | 2.9 | -0.1 |
| verbosity | 3.0 | 2.8 | -0.2 |

### direct

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| correctness | 2.0 | 2.0 | +0.0 |
| tone_and_style | 2.1 | 2.0 | -0.1 |
| verbosity | 2.0 | 2.0 | +0.0 |

### safety

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| refusal | 3.0 | 3.0 | +0.0 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.9 | 2.9 | +0.0 |
