# Wikipedia Agent Design

## Agent Design

The agent design aimed to be highly configurable so it's easy to do side-by-side evals. It is also versioned so I can keep track of all changes along the way. The prompt design uses well defined blocks that specify the agent's role, principles, tools and response format. It goes from very general, high-level instructions to very specific instructions.

The agent and judge model was chosen to be `claude-haiku-4-5-20251001` without extended thinking due to budget constraints. 

## Eval Design



## Successes and Failures

### Successes

### Failures
- The judge's rubric on verbosity was not calibrated to my expectations. It would penalize the agent for including relevant information that was not strictly necessary to answer the question but was still useful context. I should have calibrated it by using human labeled rubric scores before using it for evals. Additionally asking the model for citations usually causes it to be more verbose which conflicts with its conciseness guidelines.

## Hill Climbing

### V0 -> V1

This compared a very simple generated V0 prompt with an initial designed one. Summary report in `eval_outputs/2026-02-22_00-08-25/report.md`

#### Issues

- V1 was skipping search_wikipedia for well-known topics like literary plot summaries and scientific concepts because it relied on its own confidence to decide whether to search. These caused a recall drop in triggering and and weak scores in disambiguation.
**Attempted Fix**: mentioned that the tool is required for any real-world topic for groundedness even if it knew the answer.

- V1 was picking the dominant interpretation of ambiguous terms (e.g. "jaguar" the animal, "renaissance" the European art movement) without checking whether the term had multiple well-known referents. This caused poor performance in disambiguation.
**Attempted Fix**: added parts to the prompt to always acknowledge possible ambiguity even if one interpretation is more likely.

- V1 was more verbose than desired, and references Wikipedia unnecessarily such as saying "the Wikipedia article does not contain this information".
**Attempted Fix**: in <response_format> block added instructions on limiting the amount of unnecessary detail in responses.

### V1 -> V2

Summary report in `eval_outputs/2026-02-22_21-04-30/report.md`.


#### Issues

- V2 was lacking in full correctness scores for both direct and multi-step. Some examples showed that the agent was not answering all parts of the question (e.g. highest melting point and who discovered it? only answered the first part) while some showed poor search quality when there is ambiguous information on the Wikipedia page (e.g. question on Jupiter's red spot).
**Attempted Fix**: Added a sub-section in <tool_usage_guidelines> for multi-part and query refinement to encourage the model to issue more queries as needed for better grounding.

- V2 was still lacking in disambiguation scores because it would still pick the dominant interpretation of ambiguous terms.
**Attempted Fix**: Flushed out <disambiguation> section in the system instructions to be more explicit about how to handle ambiguous terms. Specifically around acknowledgement and tying together related interpretations.

- V2 was still too verbose according to the scores, although upon further inspection I think the scores may be too strict on verbosity. For example the response for "Who wrote the novel 1984?" was penalized for mentioning the publication date. Other examples showed that it was citing Wikipedia which was in its system instructions.
**Attempted Fix**: I did not alter the judge prompt for consistency but instead made small tweaks to <response_format>.


## Future Work

With more time I would have liked to explore the following:

- More thorough groundedness eval, where the results of the search results are shown to the judge. This would allow the judge to determine if the answers are grounded in the content of the search results.
- True side-by-side evals where the judge is shown the responses from multiple agents and asked to compare them. This would allow for more nuanced comparisons between agents.
- Broader coverage of query types, such as open-ended questions, general conversation, adversarial questions, and multi-turn examples (all of my examples were single-turn).
- Quality evals for agent personality and more subtle behavior, such as politeness, delightfulness, and sycophancy.
- Evals on more powerful models and with thinking enabled.