# The directive as a benchmark: plan and bars (written 2026-11-22, before any result)

Ken: "we need a language API so anyone could use it for AI-assisted programming, so basically a directive to give
to AI to program in that way ... OK so let's do this and benchmark it and see if it helps."

## The question

Does handing the model the directive (DIRECTIVE.md) make it program in relations unaided: hold the form without
the server forcing it, cite sources, and get more right with none wrong? And what does the directive itself cost
in tokens, since it rides in every prompt?

## The arms, same tasks, same models, same seeds, one call each

- **L, no directive** (already run): the form explained in the prompt, free text, nothing forcing it. Held the
  form 27.5 percent (3B) and 69.2 percent (7B).
- **E, the full directive:** DIRECTIVE.md's seven rules and output section as a prefix, then L's prompt. About
  900 tokens of prefix.
- **F, the short directive:** the seven rules in seven lines, about 120 tokens, then L's prompt.

Same gate as L: lines must parse, every source verbatim in the input, every number in a value in its source;
arithmetic by the rule. Dates read by the date relation (as in arm D), so a copied written date is not marked
wrong for its spelling.

## Bars

1. **The directive teaches the form:** E or F holds the form (all fields present, parsed) on at least 90 percent
   of answers on the 7B, unaided. Below that the directive is advice, not a language.
2. **It helps:** E or F is right at least as often as L with no more wrong answers, on both models.
3. **The short one is enough:** F matches E on right and wrong within three points at fewer tokens per correct
   answer. If so, the short directive is the one to ship; the full text is documentation.
4. Tokens per correct answer are reported for all, with the prefix counted, because that is what a user pays.
