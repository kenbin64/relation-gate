# The native-language experiment: plan and bars (written 2026-11-21, before any result)

Ken's question, in his words: "the question really is not speed, it is AI reliability with using native AI
language as opposed to traditional programming language."

## The question

When the model has to produce its answer IN the relation language (every value as a relation with the piece of
input it came from, every computed value as a relation the checker recomputes), is it more reliable than the same
model writing a traditional program, or answering in prose? Reliability means wrong answers let through, first,
and right answers and tokens per correct answer after that.

## Three arms, same model, same tasks, same seeds

- **A, prose.** The existing one-call baseline: the mixed instruction, the answer in the task's required shape.
- **P, traditional program.** The model is asked to write a Python function `solve(text)` that returns the answer
  for this kind of task, output only code. The code is run on the task's input in a separate process with a
  10-second limit, and its printed result is graded. The model writes in a language it was trained on.
- **L, the relation language.** The model is asked to answer as relation lines, one per field, each with its
  source: `name = value from "the exact words in the input"`. For the arithmetic task it states the three figures
  with their sources and the gate recomputes the result from the rule `net = saving * uses - price`; the model's
  own arithmetic is never trusted. The gate checks: the lines parse; every quoted source occurs in the input
  verbatim; every number in a value occurs in its source; then the grader marks the values. A line that fails
  the gate is a refusal, not an answer (no retries: one call, so the arms cost the same number of calls).

The graders are the benchmark's fixed rules, ported line for line; never a model.

## Bars

1. **The model can speak it:** L's lines parse on the first try for at least 90% of answers. Below that, the
   language is not native enough to the model and the rest is moot.
2. **Reliability:** on the held-out tasks, L lets through fewer wrong answers than A and than P.
3. **Not at a price:** L is right at least as often as P, at no more tokens per correct answer than P. (P pays
   for the code it writes; L pays for the sources it quotes.)
4. **And fewer tokens** (Ken, 2026-11-21: "and less tokens"): on the held-out tasks, L's tokens per correct answer
   are below A's as well as P's. L quotes its sources, which costs output tokens, so this bar can fail while the
   reliability bar passes; if it does, both are reported and neither is argued away.
5. Everything else is reported as it is: by task kind, both sets, with the refusals separate from the wrong.

llama3.2:3b first (the same model as the checker experiment), three seeds; qwen2.5-coder:7b if the server is free,
because a coding model is the fair opponent for the program arm.
