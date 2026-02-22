# Eval Report

**Generated:** 2026-02-22 08:24:07

**Base agent:** `agent_v0`

**Test agent:** `agent_v1`

## Trajectory (Tool Triggering)

| Metric | Base | Test | Diff |
|--------|------|------|------|
| Accuracy  | 100% | 90% | -10% |
| Precision | 100% | 100% | +0% |
| Recall    | 100% | 82% | -18% |
| F1        | 100% | 90% | -10% |

## Rubric Evaluations

Ratings are on a scale of 1 to 3, where 3 is the best.

### disambiguation

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| disambiguation_handling | 1.8 | 2.2 | +0.4 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.0 | 2.0 | +0.0 |

### adversarial_grounding

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| groundedness | 3.0 | 3.0 | +0.0 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.1 | 2.6 | +0.5 |

### multistep

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| correctness | 2.0 | 2.0 | +0.0 |
| tone_and_style | 2.8 | 2.6 | -0.1 |
| verbosity | 2.0 | 2.2 | +0.2 |

### punting

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| appropriateness | 3.0 | 2.9 | -0.1 |
| helpfulness | 3.0 | 2.9 | -0.1 |
| verbosity | 2.6 | 2.8 | +0.2 |

### direct

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| correctness | 2.0 | 2.0 | +0.0 |
| tone_and_style | 2.3 | 2.2 | -0.1 |
| verbosity | 2.0 | 2.0 | +0.0 |

### safety

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| refusal | 3.0 | 3.0 | +0.0 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.5 | 2.8 | +0.3 |
