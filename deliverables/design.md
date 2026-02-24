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

Triggering is done as an objective verifier whereas the other categories are single-sided LLM judge evals. I did not have time to explore true side-by-side evals where the judge is shown the responses from multiple agents and asked to compare them. The rubrics can be found in `configs/evals.yaml`.

After these evals are run, results are summarized and compared side-by-side between a base model and a test model.

## Successes and Failures

### Successes

- The agent can reliably answer questions that require multiple steps and facts in a safe and grounded manner while maintaining a helpful yet professional tone with well-structured responses.

- The agent responds well to edge cases such as adversarial grounding questions and punts gracefully when the question is outside its scope.

- The agent performed well on safety questions, refusing to answer harmful or unethical requests.

- Through hill climbing we were able to improve the agent's triggering behavior and disambiguation behavior to an extent.

### Failures
- The judge's rubric on verbosity was not calibrated to my expectations. It would penalize the agent for including relevant information that was not strictly necessary to answer the question but was still useful context. I should have calibrated it by using human labeled rubric scores before using it for evals. Additionally asking the model for citations usually causes it to be more verbose which conflicts with its conciseness guidelines.

- The generated dataset had ground truths that lacked sufficient nuance for some questions. For example, the Jupyter red spot question had an answer that had been revised in 2024. The ground truth was not updated to reflect this, so the agent was penalized for providing the correct answer.

- Sometimes the eval rubrics were in conflict with the system instructions. For example, when it comes to disambiguation, it was difficult to have the agent acknowledge multiple interpretations while possibly also providing a helpful answer.

## Hill Climbing

### V0 -> V1

This compared a very simple generated V0 prompt with an initial designed one. Summary report in `eval_outputs/2026-02-22_00-08-25/report.md`

- V1 was skipping search_wikipedia for well-known topics like literary plot summaries and scientific concepts because it relied on its own confidence to decide whether to search. These caused a recall drop in triggering and and weak scores in disambiguation.
  > **Attempted Fix**: mentioned that the tool is required for any real-world topic for groundedness even if it knew the answer.

- V1 was picking the dominant interpretation of ambiguous terms (e.g. "jaguar" the animal, "renaissance" the European art movement) without checking whether the term had multiple well-known referents. This caused poor performance in disambiguation.
  > **Attempted Fix**: added parts to the prompt to always acknowledge possible ambiguity even if one interpretation is more likely.

- V1 was more verbose than desired, and references Wikipedia unnecessarily such as saying "the Wikipedia article does not contain this information".
  > **Attempted Fix**: in <response_format> block added instructions on limiting the amount of unnecessary detail in responses.

### V1 -> V2

Summary report in `eval_outputs/2026-02-22_21-04-30/report.md`.

- V2 was lacking in full correctness scores for both direct and multi-step. Some examples showed that the agent was not answering all parts of the question (e.g. highest melting point and who discovered it? only answered the first part) while some showed poor search quality when there is ambiguous information on the Wikipedia page (e.g. question on Jupiter's red spot).
  > **Attempted Fix**: Added a sub-section in <tool_usage_guidelines> for multi-part and query refinement to encourage the model to issue more queries as needed for better grounding.

- V2 was still lacking in disambiguation scores because it would still pick the dominant interpretation of ambiguous terms.
  > **Attempted Fix**: Flushed out <disambiguation> section in the system instructions to be more explicit about how to handle ambiguous terms. Specifically around acknowledgement and tying together related interpretations.

- V2 was still too verbose according to the scores, although upon further inspection I think the scores may be too strict on verbosity. For example the response for "Who wrote the novel 1984?" was penalized for mentioning the publication date. Other examples showed that it was citing Wikipedia which was in its system instructions.
  > **Attempted Fix**: I did not alter the judge prompt for consistency but instead made small tweaks to <response_format> system instructions.

### V2 -> V3

Summary report `eval_outputs/2026-02-23_22-29-04`.

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