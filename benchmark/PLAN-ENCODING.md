# The dense form: plan and bars (written 2026-11-22, before any result)

Ken: "it really isn't a language, it's a native language that is of math. We use programming languages because
they have already been optimized, and to write in assembly or even binary would defeat the purpose, but AI does
not have to write in human readable. It can write very efficiently; then if we need to read it we can make it more
readable with a program."

## The question

Same relations, same sources, same gate. Does a terse form, which only a program reads, cost fewer tokens per
correct answer than the readable form, with no more wrong answers? And can a program bloom the terse form into
readable lines and fold it back without losing a character?

## The two forms, both forced by the model server

- **D, verbose:** `{"date": {"value": "2026-03-03", "from": "March 3, 2026"}, ...}` (already run).
- **T, terse:** `{"date": ["2026-03-03", "March 3, 2026"], ...}`: the same two facts per field as a two-element
  array, nothing else. The prompt is the same length; only the output shape changes.

Both go through the same checks (every source verbatim in the input, every number in a value in its source, dates
read by the date relation, arithmetic by the rule) and the same grader.

## The renderer

`render.py`: terse to readable relation lines (`date = 2026-03-03 from "March 3, 2026"`) and back. The bar is
exactness: every terse answer from the run, bloomed and folded, equals itself byte for byte.

## Bars

1. T uses fewer tokens per correct answer than D on both models (the output is where the saving is; prompt tokens
   are the same, so the saving is bounded, and the size of it is the result).
2. T lets through no more wrong answers than D.
3. The renderer round-trips 100 percent of T's answers exactly.
4. Reported as it is: output tokens alone (the model's own count), so the saving is visible without the prompt.

Tokens are the unit because they are the AI's unit; characters are reported beside them to show the difference
between short for a person and short for a model.
