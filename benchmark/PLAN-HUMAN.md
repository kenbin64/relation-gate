# The human checker: plan and bars (written 2026-11-21, before any check is made)

Ken: "another benchmark: human checks."

## The question

Three checkers look at the same answers. Which lets wrong answers through, which throws right answers away, and
what does each check cost?

## The answers checked

Every held-out task's first answer (seed 1) from each model's prose arm, as already recorded in the native
experiment: 40 answers from Llama 3.2 (3B) and 40 from Qwen 2.5 Coder (7B). 80 answers, fixed before anyone
checks them. The right answers stay hidden from all three checkers; the grader (fixed rules) marks them afterwards.

## The three checkers

- **The model itself.** The pipeline's own check, word for word: "Is the answer correct and exactly in the required
  format? Reply with one word: YES or NO." Asked of the same model that gave the answer.
- **The page of rules.** The gate program (tasks.gate) on the answer and the task's input. No model call.
- **A person.** Ken, in a browser page, shown the instruction, the input and the answer, pressing Accept, Reject or
  Not sure. No answer key on screen. Time per check recorded from the moment the answer appears to the press.

## What is measured, per checker

Wrong answers let through (accepted but wrong), right answers thrown away (rejected but right), not-sure or refuse,
and cost: the model's tokens per check, zero for the rules, seconds per check for the person.

## Bars

1. The person lets through fewer wrong answers than the model checker. (If a careful person cannot beat the
   model's self-check, the pipeline's design is defensible; this says whether it is.)
2. The page of rules lets through no more wrong answers than the person, on the answers a shape-and-source check
   can see (everything except sentiment and arithmetic). On sentiment and arithmetic the person is expected to
   win and that is reported, not hidden.
3. Cost is reported as it is: tokens, zero, and seconds. No bar, because the units differ; the reader decides what a
   minute of a reviewer's time is worth against a model call.

One person, one sitting, eighty checks. A first result, not a study.
