# Eval Report

**Generated:** 2026-02-24 12:02:37

**Base agent:** `agent_v0`

**Test agent:** `agent_v1`

## Trajectory (Tool Triggering)

n=20

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
| disambiguation_handling | 1.7 | 1.9 | +0.2 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.1 | 2.5 | +0.3 |

### adversarial_grounding

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| groundedness | 3.0 | 2.9 | -0.1 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.1 | 2.7 | +0.6 |

### multistep

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| correctness | 2.9 | 2.7 | -0.2 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.0 | 2.6 | +0.6 |

### punting

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| appropriateness | 3.0 | 3.0 | +0.0 |
| helpfulness | 3.0 | 3.0 | +0.0 |
| verbosity | 2.4 | 2.6 | +0.2 |

### direct

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| correctness | 3.0 | 3.0 | +0.0 |
| tone_and_style | 3.0 | 3.0 | -0.0 |
| verbosity | 2.0 | 2.2 | +0.2 |

### safety

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| refusal | 3.0 | 3.0 | +0.0 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.5 | 2.8 | +0.2 |
