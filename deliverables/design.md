# Wikipedia Agent Design

## Agent Design

The agent design aimed to be highly configurable so it's easy to do side-by-side evals. It is also versioned so I can keep track of all changes along the way. The prompt design uses well defined blocks that specify the agent's role, principles, tools and response format. It goes from very general, high-level instructions to very specific instructions.

The agent and judge model was chosen to be `claude-haiku-4-5-20251001` without extended thinking due to budget constraints. 

## Eval Design

The eval suite has 7 categories of 20 examples each (140 total) which covers the main use cases and failure modes of the Wikipedia agent:

- **Triggering** — does the agent invoke the Wikipedia tool when and only when appropriate? Evaluated as binary pass/fail on the trajectory (objective, no LLM judge needed). Metrics are accuracy, precision, recall, and f1.
- **Direct** — single-fact lookup accuracy against ground truth. Judged on correctness, tone, and verbosity.
- **Multistep** — compound questions requiring multiple facts. Same rubric as direct, but correctness requires all parts answered.
- **Adversarial grounding** — queries containing false premises (e.g. "Why did Napoleon lose at Waterloo to the Americans?"). Judged on whether the agent catches and corrects the false premise rather than building on it.
- **Disambiguation** — short ambiguous queries with multiple valid interpretations. Judged on whether the agent acknowledges multiple interpretations rather than silently picking one.
- **Punting** — queries outside the agent's scope (real-time data, personal context, action requests). Judged on appropriate decline, helpfulness, and conciseness.
- **Safety** — harmful or unethical requests. Judged on refusal, tone, and conciseness.

Triggering is done as an objective verifier whereas the other categories are single-sided LLM judge evals. I did not have time to explore true side-by-side evals where the judge is shown the responses from multiple agents and asked to compare them. The rubrics can be found in `configs/evals.yaml` and the data in `eval_data/`.

After these evals are run, results are summarized and compared side-by-side between a base model and a test model.

## Successes and Failures

### Successes

- The agent can reliably answer questions that require multiple steps and facts in a safe and grounded manner while maintaining a helpful yet professional tone with well-structured responses.

- The agent responds well to edge cases such as adversarial grounding questions and punts gracefully when the question is outside its scope.

- The agent performed well on safety questions, refusing to answer harmful or unethical requests.

- Through hill climbing we were able to improve the agent's triggering behavior and disambiguation behavior to an extent.

### Failures
- The judge's rubric on verbosity was not calibrated to my expectations. It would penalize the agent for including relevant information that was not strictly necessary to answer the question but was still useful context. I should have calibrated it by using human labeled rubric scores before using it for evals. Additionally asking the model for citations usually causes it to be more verbose which conflicts with its conciseness guidelines.

- The generated dataset that had ground truths that lacked sufficient nuance for some questions. For example, the Jupyter red spot question had an answer that had been revised in 2024. The ground truth was not updated to reflect this, so the agent was penalized for providing the correct answer.

- The agent sometimes failed to ...

The biggest takeaway was that in order to do meaningful hill climbing, we need to have eval rubrics and ground truths that are calibrated to our expectations. This is sometimes hard to do in practice because it's hard to anticipate all the ways the agent might behave.

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

- V2 has a very slight regression in verbosity, especially in the direct dataset. V2 adds tangentially relevant context beyond what's asked.
  > **Attempted Fix**: in `<response_format>` remove the citation requirement and add a sentence about only providing extra context if it's necessary to fully answer the question.

### V2 -> V3

Summary report in `eval_outputs/2026-02-24_17-03-19/report.md`.

- V3 has a slight regression in disambiguation. Previously clarifying queries like "what is amazon?" now silently pick one interpretation without noting alternatives. Many of the failures from V2 remain.
  > **Possible Explaination**: the `disambiguation_handling` rubric scores 3 only when multiple interpretations are acknowledged. The SI prompt allows answering the likely interpretation with a trailing note — but the judge still scored those as 2 rather than 3, so the rubric and SI are misaligned.

- V3's multi-step correctness remained flat at 2.0. The new per-part search instruction did not resolve the two main misses: the tungsten discovery and the Great Red Spot observation history.
  > **Further Analysis**: in both of those cases the ground truth label is potentially incorrect or at least does not reflect the nuance of multiple possible answers. This is a weakness in the dataset.


## Future Work

With more time I would have liked to explore the following:

- More thorough groundedness eval, where the results of the search results are shown to the judge. This would allow the judge to determine if the answers are grounded in the content of the search results.
- True side-by-side evals where the judge is shown the responses from multiple agents and asked to compare them. This would allow for more nuanced comparisons between agents.
- Broader coverage of query types, such as open-ended questions, general conversation, adversarial questions, and multi-turn examples (all of my examples were single-turn).
- Quality evals for agent personality and more subtle behavior, such as politeness, delightfulness, and sycophancy.
- Evals on more powerful models and with thinking enabled.


Time spent on project: 4-5 hours.