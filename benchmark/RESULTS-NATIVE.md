# The native-language experiment: results (2026-11-21)

Plan and bars: PLAN-NATIVE.md, written before the run. Runner: native.py. Raw rows: results/native-<model>.jsonl.
Three arms, one call each, same model, same tasks, same seeds: A prose, P a Python program the model writes and we
run, L the relation language (every value with its source, arithmetic recomputed by the rule).

## llama3.2:3b, held-out (40 tasks, three seeds)

| Arm | Right | Wrong | Refused | Tokens per correct |
|---|---|---|---|---|
| A prose | 50.8% | 49.2% | 0.0% | 218 |
| P program the model writes | 18.3% | 81.7% | 0.0% | 1,037 |
| L relation lines, gated | 30.0% | **0.0%** | 70.0% | 570 |

Bars: 1 (the model can speak it, parse rate 90%): **NO**, 27.5%. 2 (fewer wrong than prose and program): **PASS**,
none at all. 3 (right at least as often as the program, at no more tokens): **PASS**, 30.0 against 18.3 percent at
570 against 1,037. 4 (fewer tokens per correct than prose as well): **NO**, 570 against 218.

What the rows say:

- The 3B model cannot hold the line form. 72.5 percent of its answers were missing a field; many wrote the word
  "field" literally ("field = cracked"), or split a sentence into one line per word. A language is native to a model
  only if the model can speak it, and on this model it cannot. That is the plain reading of bar 1.
- When it did speak it, nothing wrong got through. Every line that parsed had a verbatim source 99 percent of the
  time and a value consistent with its source 100 percent of the time, and the arithmetic came from the rule, not
  the model: on calculate, L was right 57 percent against prose 0 and program 13, because the model only had to
  find three figures and the relation did the sum.
- The traditional-program arm was the worst of the three on this model: 46 percent of the programs crashed and
  most of the rest returned the wrong shape. Writing code is not where a 3B model is reliable either.
- Prose is cheap and half wrong. The relation form is dearer per correct answer than prose because its sources
  cost output tokens and its refusals cost input tokens with nothing to show; it is cheaper than the program.

## qwen2.5-coder:7b, held-out (40 tasks, three seeds)

| Arm | Right | Wrong | Refused | Tokens per correct |
|---|---|---|---|---|
| A prose | 69.2% | 30.8% | 0.0% | 168 |
| P program the model writes | 60.8% | 39.2% | 0.0% | 308 |
| L relation lines, gated | 68.3% | **0.0%** | 31.7% | 284 |

Bars: 1 (parse rate 90%): **NO**, 69.2%. 2 (fewer wrong than prose and program): **PASS**, none at all against
30.8 and 39.2 percent. 3 (right at least as often as the program, at no more tokens): **PASS**, 68.3 against 60.8
percent at 284 against 308. 4 (fewer tokens per correct than prose): **NO**, 284 against 168.

What the rows say:

- The coding model is right as often in relations as in prose (68.3 against 69.2 percent) and never wrong, where
  prose was wrong 31 percent of the time. The 31.7 percent it did not answer were refusals, not errors.
- Every refusal but one was the same thing: the model gave the right values and left the source off.
  `title = Fix the gallery signature` with no `from "..."`. All 60 format answers and 12 extract answers. The
  values were correct; the model would not cite. In the free-text form, nothing stopped it skipping the clause.
  That is the one gap the constrained arm (C, post hoc) closes by construction: the server cannot emit a field
  without its source.
- Calculate: 100 percent right, against prose 0 and the program 83. The model only had to find three figures
  with their sources; the relation did the arithmetic. This is the clearest case of the language doing what it is
  for: the model reads, the rule computes.
- Tokens: relations cost 1.7 times prose per correct answer, because sources are output tokens and refusals are
  spent input with nothing to show. They cost less than the program.

## The constrained arm (C), post hoc: the form forced, held-out

| Model | Arm | Right | Wrong | Refused | Tokens per correct | Parse rate |
|---|---|---|---|---|---|---|
| Llama 3.2, 3B | L free text | 30.0% | 0.0% | 70.0% | 570 | 27.5% |
| Llama 3.2, 3B | C constrained | 40.0% | 8.3% | 51.7% | 407 | 99.6% |
| Qwen 2.5 Coder, 7B | L free text | 68.3% | 0.0% | 31.7% | 284 | 69.2% |
| Qwen 2.5 Coder, 7B | C constrained | 59.2% | 20.0% | 20.8% | 309 | 100% |

Constraining the server fixed the speaking problem completely: 99.6 and 100 percent of answers held the form.
It also let wrong answers through for the first time, and every one of them is the same thing: the model copied
the date exactly as the input wrote it ("March 3, 2026"), with a true source, and the grader wants YYYY-MM-DD. The
source facts passed because the copy was honest; the form was wrong. That is not the model lying, it is the
arm lacking the relation that reads a date in any written form, which the gate already has. Arm D adds it (post
hoc, labelled): a copied date is read by that relation into the required form, or refused when it cannot be read.

## Arm D (constrained + the date relation), post hoc, held-out

| Model | Arm | Right | Wrong | Refused | Tokens per correct | Spoke the form |
|---|---|---|---|---|---|---|
| Llama 3.2, 3B | A prose | 50.8% | 49.2% | 0.0% | 218 | |
| Llama 3.2, 3B | D relations, form forced, date relation | 50.0% | **0.0%** | 50.0% | 326 | 100% |
| Qwen 2.5 Coder, 7B | A prose | 69.2% | 30.8% | 0.0% | 168 | |
| Qwen 2.5 Coder, 7B | D relations, form forced, date relation | **79.2%** | **0.0%** | 20.8% | 231 | 100% |

With the form forced and the date relation in place, the coding model answering in relations with sources was
right more often than in prose (79.2 against 69.2 percent), never wrong (prose: 30.8 percent wrong), at 1.4 times
prose's tokens per correct answer. The small model matched prose on right answers with none wrong. Against the
bars written before the first run: 1 (speak it) PASS by construction; 2 (fewer wrong) PASS; 3 (beats the program)
PASS; 4 (fewer tokens than prose) still NO, 231 against 168 and 326 against 218.

What it refused, and why that is the right call: on both models most refusals are the arithmetic task, where the
model cited the label as its source ("from": "cost:") instead of the figure's own words, so the consistency fact
(every number in the value occurs in its source) failed. The values were right; the citation was lazy. The gate
cannot tell a lazy citation from a fabricated one without reading the input itself, so it refuses, and that is the
honest behaviour: a value whose stated source does not contain it is not a sourced value. A model fine-tuned to
cite the figure's own words would close most of that gap, which is the Tinker track.

## The dense form (arm T, PLAN-ENCODING.md, run 2026-11-22), held-out

The question was Ken's: the AI does not have to write human-readable; it can write very efficiently and a program
can render it readable. So: the same relations, the same sources, the same checks, in a terse form (each field a
two-element array, value then source) against the readable form (each field an object with "value" and "from").
Both forced by the server. Output tokens are the model's own count.

| Model | Form | Right | Wrong | Refused | Tokens per correct | Output tokens per answer | Characters per answer |
|---|---|---|---|---|---|---|---|
| Llama 3.2, 3B | D readable | 50.0% | 0.0% | 50.0% | 326 | about 37 | 149 |
| Llama 3.2, 3B | T terse | 33.3% | 5.0% | 61.7% | 452 | 46 | 125 |
| Qwen 2.5 Coder, 7B | D readable | 79.2% | 0.0% | 20.8% | 231 | about 42 | 169 |
| Qwen 2.5 Coder, 7B | T terse | 76.7% | 3.3% | 20.0% | 202 | 44 | 98 |

(D's output tokens are estimated from characters at four per token, because the split count was added to the
runner after D ran; T's are the model's own count.)

Bars: 1 (fewer tokens per correct on both models): **NO**. The 7B saved 13 percent; the 3B spent 39 percent more.
2 (no more wrong): **NO**, 3.3 and 5.0 percent against none. 3 (the renderer round-trips exactly): **PASS**, 2,000
cases including quotes, backslashes, control characters and non-ASCII.

The reading: **the terse form cut characters by 42 percent and output tokens by nothing.** 98 characters against
169 on the 7B, and 44 output tokens against about 42. Short for a person is not short for the model: brackets,
commas and quotes are each a token whether or not a human finds them dense, and the words inside, the values and
the sources, cost the same in either form. The 3B also handled the array form worse, paraphrasing sources
instead of copying them, which the source fact refused. So "write dense" is true of characters and false of
tokens on today's tokenizers, and the renderer, which works, has nothing to save.

What this leaves for the token saving: not a denser spelling of the same facts, but fewer facts said. Two routes,
both still to run. One, the Kravitz form: the model states only what a software reading could not settle, so
most answers are a single token of agreement (the private answerer library already measures the shape of that at
107 tokens per correct answer). Two, relation tokens: a fine-tune that adds the field names, the source clause
and the operators as single tokens, so a relation costs a handful instead of fifteen; a prediction until it is run.

The chain of post-hoc arms, kept in order so the reader can see what each change did: L (free text) could not be
spoken; C (form forced) was spoken every time but copied dates as written; D (the date relation) reads them. Each
step is labelled; the first-run numbers stay in the tables above.

## What it means so far

On the small model the language is a far better checker than a native tongue: as a checker it cut wrong answers
from 68 to 4 percent; as the model's own output form it let nothing wrong through but could only be spoken a
quarter of the time. The honest sentence is: a model answering in relations with sources never guessed, and a 3B
model could rarely do it. Whether a 7B coding model can is the next table.
