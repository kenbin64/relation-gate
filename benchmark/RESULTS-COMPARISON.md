# Mine against the common designs, on the same held-out tasks (compiled 2026-11-21)

Forty held-out tasks (classify, extract, calculate, format), three seeds, two local models, fixed-rule graders.
"No answer" is an abstention or a refusal: counted as not right, reported apart from wrong, because a wrong answer
handed over is worse than an honest "no answer". Tokens are the model's own counts over every call a design makes.
The heavy workflow and the panel were run on 2026-10-26 (seed-bloom benchmark); everything else on 2026-11-21.

## Llama 3.2, 3 billion parameters

| Side | Design | Right | Wrong | No answer | Tokens per correct |
|---|---|---|---|---|---|
| common | one call, prose | 50.8% | 49.2% | 0.0% | 218 |
| common | agent pipeline: the model checks the model, retries | 31.7% | 68.3% | 0.0% | 2,749 |
| common | heavy workflow: planner, worker, critic, reviser, formatter | 56.7% | 43.3% | 0.0% | 2,851 |
| common | self-consistency: a panel of five, majority or abstain | 50.8% | 7.5% | 41.7% | 1,085 |
| common | the model writes a program, we run it | 18.3% | 81.7% | 0.0% | 1,037 |
| mine | the relation gate in place of the model checker | 60.0% | 3.3% | 36.7% | 464 |
| mine | the model answers in relations with sources, free text | 30.0% | 0.0% | 70.0% | 570 |
| mine | the same, form forced by the server | 40.0% | 8.3% | 51.7% | 407 |
| mine | the same, form forced, with the date relation (arm D) | 50.0% | 0.0% | 50.0% | 326 |
| mine | relation lines with the seven-rule directive in the prompt, nothing forced (arm F) | 44.2% | 4.2% | 51.7% | 762 |
| mine | seed and bloom: software first, the model fills a shape, a gate (the answerer library) | 97.5% | 0.0% | 2.5% | 107 |

## Qwen 2.5 Coder, 7 billion parameters

| Side | Design | Right | Wrong | No answer | Tokens per correct |
|---|---|---|---|---|---|
| common | one call, prose | 69.2% | 30.8% | 0.0% | 168 |
| common | agent pipeline: the model checks the model, retries | 68.3% | 31.7% | 0.0% | 520 |
| common | heavy workflow: planner, worker, critic, reviser, formatter | 65.0% | 35.0% | 0.0% | 2,002 |
| common | self-consistency: a panel of five, majority or abstain | 69.2% | 3.3% | 27.5% | 833 |
| common | the model writes a program, we run it | 60.8% | 39.2% | 0.0% | 308 |
| mine | the relation gate in place of the model checker | 69.2% | 8.3% | 22.5% | 325 |
| mine | the model answers in relations with sources, free text | 68.3% | 0.0% | 31.7% | 284 |
| mine | the same, form forced by the server | 59.2% | 20.0% | 20.8% | 309 |
| mine | the same, form forced, with the date relation (arm D) | 79.2% | 0.0% | 20.8% | 231 |
| mine | relation lines with the seven-rule directive in the prompt, nothing forced (arm F) | 84.2% | 1.7% | 14.2% | 414 |
| mine | the same with the full directive (arm E) | 87.5% | 1.7% | 10.8% | 1,069 |
| mine | seed and bloom: software first, the model fills a shape, a gate (the answerer library) | 95.8% | 2.5% | 1.7% | 117 |

## The reading

- **Every common design that adds model calls to check or improve the model (the pipeline, the heavy workflow)
  cost five to thirteen times more per correct answer than one call and was not more right.** On the small model
  the pipeline was less right than one call. The checking step is where the tokens went and where nothing was caught.
- **The one common design that cuts wrong answers is the panel**, and it does it the expensive way: five answers
  per task, 833 to 1,085 tokens per correct answer, and it still let 3 to 8 percent wrong through.
- **The relation gate cuts wrong answers to the panel's level or below at a third to a half of the panel's tokens,**
  with no extra model calls: on the 3B, 3.3 percent wrong at 464 tokens; on the 7B, 8.3 percent at 325. Its
  remaining wrong answers are sentiment and arithmetic, which a shape-and-source check does not see.
- **The model answering in relations with sources never guessed** (0.0 percent wrong on both models, free text),
  at tokens between one call and the pipeline; what it could not do was hold the form unaided. Forcing the form
  removed that and exposed the next relation needed (dates in any written form). With both in place (arm D) the 7B
  coding model was right more often than in prose, 79.2 against 69.2 percent, with none wrong, at 1.4 times prose's
  tokens per correct answer; the 3B matched prose on right answers with none wrong.
- **The directive, handed to the 7B coding model with nothing forcing the output,** made it hold the form 97.5
  percent of the time and get 87.5 percent right with 1.7 percent wrong, against 69 right and 31 wrong answering
  plainly: the best non-library number in the study, at the cost of the directive's own tokens on every call
  (RESULTS-DIRECTIVE.md). The 3B model could not use a directive and needs the form forced.
- **Seed and bloom is in a different league from all of them**, common and mine: 97.5 and 95.8 percent right at
  about 110 tokens per correct answer, because software does the exact work at zero tokens and the model is
  asked only for judgment, through a shape it must fill. The relation gate is one part of that design, written
  in a language a reviewer can read; the whole design is the private library.
- **What this does not claim:** two models, one machine, tasks written by the author of the designs (the held-out
  set is the guard). Nothing here is a speed claim. "Common" names the patterns, not any product or team.
