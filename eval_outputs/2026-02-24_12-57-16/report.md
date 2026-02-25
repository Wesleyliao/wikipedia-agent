# Eval Report

**Generated:** 2026-02-24 13:17:06

**Base agent:** `agent_v1`

**Test agent:** `agent_v2`

## Trajectory (Tool Triggering)

n=20

| Metric | Base | Test | Diff |
|--------|------|------|------|
| Accuracy  | 85% | 100% | +15% |
| Precision | 100% | 100% | +0% |
| Recall    | 73% | 100% | +27% |
| F1        | 84% | 100% | +16% |

## Rubric Evaluations

Ratings are on a scale of 1 to 3, where 3 is the best.

### disambiguation

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| disambiguation_handling | 1.9 | 2.4 | +0.5 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.4 | 2.5 | +0.1 |

### adversarial_grounding

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| groundedness | 2.9 | 2.9 | +0.0 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.7 | 2.6 | -0.1 |

### multistep

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| correctness | 2.8 | 2.7 | -0.0 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.4 | 2.4 | +0.0 |

### punting

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| appropriateness | 3.0 | 3.0 | +0.0 |
| helpfulness | 3.0 | 3.0 | +0.0 |
| verbosity | 2.8 | 2.7 | -0.1 |

### direct

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| correctness | 3.0 | 3.0 | +0.0 |
| tone_and_style | 3.0 | 3.0 | -0.0 |
| verbosity | 2.3 | 2.0 | -0.2 |

### safety

n=20

| Dimension | Base | Test | Diff |
|-----------|------|------|------|
| refusal | 3.0 | 3.0 | +0.0 |
| tone_and_style | 3.0 | 3.0 | +0.0 |
| verbosity | 2.9 | 2.8 | -0.1 |
