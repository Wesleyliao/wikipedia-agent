# Eval Report
**Generated:** {timestamp}
**Base agent:** `{base}`
**Test agent:** `{test}` (if applicable)

## Trajectory (Tool Triggering)

### Single agent

| Metric    | Value  |
|-----------|--------|
| Accuracy  | XX.XX% |
| Precision | XX.XX% |
| Recall    | XX.XX% |
| F1        | XX.XX% |

### Side-by-side (when test agent is configured)

| Metric | Base | Test |
|--------|------|------|
| Accuracy  | XX.XX% | XX.XX% |
| Precision | XX.XX% | XX.XX% |
| Recall    | XX.XX% | XX.XX% |
| F1        | XX.XX% | XX.XX% |

## Rubric Scores

### Summary (single agent)

| Dataset | Mean Score | 1 | 2 | 3 | 4 | 5 |
|---------|-----------|---|---|---|---|---|
| direct  | 4.20      | 0 | 1 | 2 | 10| 7 |

### Summary (side-by-side when test agent is configured)

| Dataset | Base Mean | Test Mean | Base Distribution (1-5) | Test Distribution (1-5) |
|---------|-----------|-----------|-------------------------|-------------------------|
| direct  | 4.20      | 3.80      | 0/1/2/10/7              | 1/2/4/8/5               |
