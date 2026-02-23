# Eval Report

**Generated:** 2026-02-22 21:22:27

**Base agent:** `agent_v1`

**Test agent:** `agent_v2`

## Trajectory (Tool Triggering)

n=20

| Metric | Base | Test | Diff |
|--------|------|------|------|
| Accuracy  | 90% | 100% | +10% |
| Precision | 100% | 100% | +0% |
| Recall    | 82% | 100% | +18% |
| F1        | 90% | 100% | +10% |

## Rubric Evaluations

Ratings are on a scale of 1 to 3, where 3 is the best.

### disambiguation

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| disambiguation_handling | 2.1 | 2.3 | +0.2 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.1 | 2.0 | -0.1 |

### adversarial_grounding

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| groundedness | 3.0 | 3.0 | +0.0 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.4 | 2.5 | +0.2 |

### multistep

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| correctness | 2.0 | 2.0 | +0.0 |
| tone_and_style | 2.6 | 2.6 | +0.0 |
| verbosity | 2.1 | 2.1 | +0.0 |

### punting

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| appropriateness | 3.0 | 3.0 | -0.0 |
| helpfulness | 3.0 | 3.0 | -0.0 |
| verbosity | 3.0 | 2.9 | -0.1 |

### direct

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| correctness | 2.0 | 2.0 | +0.0 |
| tone_and_style | 2.2 | 2.2 | +0.0 |
| verbosity | 2.0 | 2.0 | +0.0 |

### safety

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| refusal | 3.0 | 3.0 | +0.0 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.7 | 2.9 | +0.1 |
