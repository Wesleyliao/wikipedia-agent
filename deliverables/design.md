# Wikipedia Agent Design

## Agent Design

The agent design aimed to be highly configurable so it's easy to do side-by-side evals. It is also versioned so I can keep track of all changes along the way. The prompt design uses well defined blocks that specify the agent's role, principles, tools and response format. It goes from very general, high-level instructions to very specific instructions.

The agent and judge model was chosen to be `claude-haiku-4-5-20251001` without extended thinking due to budget constraints. The tool used was MediaWiki API.

## Eval Design

The eval suite has 7 categories of 20 examples each (140 total) which covers the main use cases and failure modes of the Wikipedia agent:

- **Triggering** — does the agent invoke the Wikipedia tool when and only when appropriate? Evaluated as binary pass/fail on the trajectory (objective, no LLM judge needed). Metrics are accuracy, precision, recall, and f1.
- **Direct** — single-fact lookup accuracy against ground truth. Judged on correctness, tone, and verbosity.
- **Multi-step** — compound questions requiring multiple facts. Same rubric as direct, but correctness requires all parts answered. This is to test the agent's ability to chain together multiple tool calls to answer a complex question.
- **Adversarial grounding** — queries containing false premises (e.g. "Why did Napoleon lose at Waterloo to the Americans?"). Judged on whether the agent catches and corrects the false premise rather than building on it.
- **Disambiguation** — short ambiguous queries with multiple valid interpretations. Judged on whether the agent acknowledges multiple interpretations rather than silently picking one.
- **Punting** — queries outside the agent's scope (real-time data, personal context, action requests). Judged on whether the agent gracefully declines and provides helpful alternatives.
- **Safety** — harmful or unethical requests. Judged on refusal, tone, and conciseness. It is expected that the agent should respectfully decline and offer helpful / safe / empathetic alternatives.

Triggering is done as an objective verifier whereas the other categories are single-sided LLM judge evals. I did not have time to explore true side-by-side evals where the judge is shown the responses from multiple agents and asked to compare them. The rubrics can be found in `configs/evals.yaml` and the data in `eval_data/`.

After these evals are run, results are summarized and compared side-by-side between a base model and a test model.

## Successes and Failures

### Successes

- The agent provides correct, helpful, and grounded answers. In terms of eval scores, direct correctness is perfect, adversarial groundedness is near perfect, and safety refusal is perfect. This means the agent is obeying safety guardrails well, not hallucinating even when the user is trying to trick it, and can give correct answers to queries. Tone and style also were consistently good across all evals.

- The agent handles out-of-scope queries gracefully. Punting had perfect scores on appropriateness and helpfulness, meaning the agent consistently declines unanswerable questions while offering useful alternatives. Safety refusals are equally strong.

- Hill climbing produced measurable gains where the fix matched the failure mode. Triggering went from 85% accuracy / 73% recall (V1) to a perfect 100% (V2) by loosening the criteria on when the tool should be used. Adversarial grounding verbosity improved by +0.3 (V2 to V3) after removing the citation requirement.

### Failures
- The judge's rubric on verbosity was not calibrated to my expectations. It would penalize the agent for including relevant information that was not strictly necessary to answer the question but was still useful context. Also different types of responses should have different expectations for verbosity which I did not account for in both the SI nor the eval rubrics. I should have 1) calibrated it by using human labeled rubric scores before using it for evals and 2) used different SI and verbosity score definitions for different types of responses.

- The generated dataset that had ground truths that lacked sufficient nuance for some questions. For example, the Jupyter red spot question had an answer that had been revised in 2024 and the ambiguous melting point question. The ground truth was not updated to reflect this nuance, so the agent was penalized for providing an arguably correct answer.

- Disambiguation was unsolved. Despite three iterations of prompt refinement, the agent still fails to disambiguate terms where one meaning strongly dominates (e.g. jaguar, cell, saturn). The model's prior about which meaning is intended is so strong the prompt changes could not override it. Trying a more nuanced disambiguation strategy in V3 ("answer the likely interpretation with a note") seemed to have backfired where the model used it as permission to skip disambiguation entirely in certain cases.

The biggest takeaway is that meaningful hill climbing requires eval rubrics and ground truths that are well-calibrated to expectations. When the rubric, the system instruction, and the ground truth aren't aligned, it's hard to tell whether a score change reflects a real improvement or just noise from the evaluation setup itself.

## Hill Climbing

The evolution of the system instructions can be found in `prompts/system_instructions.yaml`. Below are the findings and rationale for the changes.

### V0 -> V1

This compared a very simple generated V0 prompt with an initial designed one. Summary report in `eval_outputs/2026-02-24_11-43-09/report.md`

- V1 was skipping search_wikipedia for well-known topics like literary plot summaries and scientific concepts because it relied on its own confidence to decide whether to search. These caused a recall drop in triggering and and weak scores in disambiguation.
  > **Attempted Fix**: mentioned that the tool is required for any real-world topic for groundedness even if it knew the answer both in the system instruction and in the tool description.

- V1 sometimes picked the dominant interpretation for ambiguous terms like Mercury, Python, Amazon, and Java without acknowledging alternatives. This causes poor performance in disambiguation and could lead to bad user experience if the model guessed incorrectly.
  > **Attempted Fix**: added a `<disambiguation>` section instructing the model to check whether the key noun has multiple well-known referents and ask for clarification even if one seems more likely.

- V1's multi-step correctness scores dropped from 2.9 to 2.7. V1 missed sub-parts of compound questions (e.g. Sagrada Familia completion date not found). V1 doesn't issue enough searches for multi-part questions.
  > **Attempted Fix**: added MULTI-PART QUESTIONS guidance in `<tool_usage_guidelines>` instructing the model to search for each part independently.

### V1 -> V2

Summary report in `eval_outputs/2026-02-24_12-57-16/report.md`.

- V2 achieved perfect 100% across all triggering metrics (up from 85% acc / 73% recall). The broadened WHEN TO USE SEARCH from the previous iteration fully resolved triggering. No further fix needed.

- V2 has improved disambiguation by 0.5, but 6 of the 20 queries still score 1. We'll need to reinforce the importance of disambiguation and make it more objective.
  > **Attempted Fix**: strengthen `<disambiguation>` with rationale of why we need to disambiguate and add more detailed instructions on how to handle ambiguous queries with a logical structure.

- V2 has slight regression in multi-step correctness. It seems to be occuring to superlative questions, where there could be multiple valid answers depending on the interpretation of the question. For example the longest border vs longest continuous border.
  > **Attempted Fix**: add approach on how to handle superlative questions with multiple possible interpretations in MULTI-PART QUESTIONS.

- V2 has a slight regression in verbosity, especially in the direct dataset. V2 adds tangentially relevant context beyond what's asked.
  > **Attempted Fix**: in `<response_format>` remove the citation requirement and add a sentence about only providing extra context if it's necessary to fully answer the question.

### V2 -> V3

Summary report in `eval_outputs/2026-02-24_17-03-19/report.md`.

- V3's new disambiguation instruction, "if one interpretation is much more likely, provide that answer with a trailing note", seemed to have caused a slight regression by giving the model an "escape hatch". It also did not obey the trailing note instruction for the cases where it decided to provide the likely interpretation. V2's stricter rule ("always ask for clarification") was more reliable at forcing the behavior.
  > **Observation**: there's some prompt-rubric misalignment. V3's SI suggestes answering the dominant interpretation with a brief note, but the rubric scores a 3 only when multiple interpretations are explicitly acknowledged. The model seems to use the "much more likely" case too often, effectively treating it as a way to skip disambiguation.

- Removing the citation requirement improved adversarial grounding verbosity (+0.3) but had almost no net effect on direct. In adversarial grounding, dropping citations seemed to have cut preamble like "Based on the search results...". In direct, the model basically replaced citations with additional facts from the search results, making total length similar. The V3 instruction "only provide extra context if necessary" is probably too subjective.
  > **Observation**: the direct verbosity problem is likely the model's tendency to try and pack lots of interesting tidbits into the answer even if they're not very related. The system instruction nudge needs to be more objective.

- Multistep correctness remained flat despite new superlative-handling instructions. The agent still latches onto the first search result without issuing follow-up searches to check for competing candidates (e.g. the oldest university query). There's also an instance where the data point has debatable ground truth: the great red spot on Jupyter has an updated answer as of 2024. and another is a somewhat ambiguous scientific question (carbon vs tungsten "melting" point).
  > **Observation**: this highlights issues both in the SI in terms of tool use failures (no second search to verify superlatives), and the dataset in terms of ground truth labels lacking nuance for debatable questions.

- Safety verbosity regressed (-0.2) while punting verbosity improved (+0.2). In punting, V3 trimmed alternative lists and removed redundant explanations. In safety, V3 responded with some additional info on specific help programs in the form of bullet points (e.g. SNAP, TANF, and housing assistance for a shoplifting refusal).
  > **Observation**: this highlights the need for response-type specific verbosity constraints as well as response-type specific rubrics for verbosity in the judge.


## Future Work

With more time I would have liked to explore the following:

- More thorough groundedness eval, where the results of the search results are shown to the judge. This would allow the judge to determine if the answers are grounded in the content of the search results.
- True side-by-side evals where the judge is shown the responses from multiple agents and asked to compare them. This would allow for more nuanced comparisons between agents.
- More nuanced treatment of verbosity, specifically defining different expected behavior for different eval types and reflecting that in the rubrics.
- Broader coverage of query types, such as open-ended questions, general conversation, adversarial questions, and multi-turn examples (all of my examples were single-turn). Also more examples for each eval type since 20 is quite low for getting statistically significant signal.
- Quality evals for agent personality and more subtle behavior, such as politeness, delightfulness, and sycophancy.
- Evals on more powerful models and with thinking enabled.


Time spent on project: 4-5 hours.