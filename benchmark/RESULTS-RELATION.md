# Design R, the relation gate: results (2026-11-21)

Run fresh the same evening the bars were written (PLAN.md, "Added 2026-11-21"): llama3.2:3b, three seeds, both
task sets, designs A, B, R and G in one file (results/raw-llama3.2-3b.jsonl, 960 answers, 12 minutes).
Report: `python report.py llama3.2:3b`. Token counts are the model's own, every call added up.

## Held-out tasks (the ones that count)

| Design | Right | Wrong | No answer | Tokens per correct | Calls per task |
|---|---|---|---|---|---|
| A one call | 50.8% | 49.2% | 0.0% | 218 | 1.00 |
| B agent pipeline (model checks model) | 31.7% | 68.3% | 0.0% | 2,749 | 6.00 |
| **R relation gate (same worker, gate program checks)** | **49.2%** | **4.2%** | **46.7%** | **607** | 2.01 |
| G library standard (structured output + seed) | 97.5% | 0.0% | 2.5% | 107 | 1.05 |

Original tasks: B 37.5% right, 62.5% wrong, 2,332 tokens per correct; R 47.5% right, 4.2% wrong, 48.3% no answer, 664.

## The bars

- **R against B:** PASS. Wrong answers let through 4.2% against 68.3%; right 49.2% against 31.7%; 4.5 times fewer
  tokens per correct answer (the bar was 2). Replacing the model checker with the gate program made the pipeline
  both more accurate and cheaper on the same model, the same prompts and the same retry wording.
- **R against C (the plain shape gate, run 2026-10-26):** PASS. Wrong 4.2% against 25.0%. The source facts
  ("every number in the answer occurs in the input", "every string occurs in the input") are what C did not have.
- **R against G:** G is far ahead, 97.5% right at 107 tokens, as expected and as said in advance. G has the seed
  (software does the exact work at zero tokens) and structured output; R has neither, by design, so that the only
  thing R changes against B is the checker. The gate is not the whole library.

## What R did, read from the rows

- 114 of 240 answers abstained. Nearly all are the 3B model wrapping a correct JSON object in prose ("Here's the
  corrected output:"), which the gate's shape fact refuses and which the grader would also have failed. Those are
  refusals of answers that were going to be wrong, so they appear as "no answer" rather than "wrong". B handed the
  same kind of answer over as if it were checked.
- 10 of 240 were let through and wrong, and every one is outside what a shape-and-source gate can see:
  - 5 classify: the sentiment was misjudged. The gate only knows the answer is one of the three words.
  - 3 format: "Call the Plumber" for "Call the plumber". The strings fact compares without case; the grader does
    not. A case-sensitive fact for the title would have refused all three (not run, so not claimed).
  - 2 calculate: wrong arithmetic in the right shape. A relation `net = saving * uses - price` would catch it, and
    that is the seed, which is design C and G territory, kept out of R on purpose.
- On classify, R equals A exactly (the gate changes nothing on a judgment task), and B's checker is the one thing
  that bought a little accuracy there (97% against 90%) at eight times the tokens.

## The second model: qwen2.5-coder:7b (run the same evening, same bars)

| Design | Right | Wrong | No answer | Tokens per correct | Calls per task |
|---|---|---|---|---|---|
| A one call | 69.2% | 30.8% | 0.0% | 168 | 1.00 |
| B agent pipeline | 68.3% | 31.7% | 0.0% | 520 | 2.37 |
| R relation gate | 55.8% | 11.7% | 32.5% | 468 | 1.68 |
| G library standard | 95.8% | 2.5% | 1.7% | 117 | 1.03 |

**R against B: NO on this model.** Fewer wrong answers (11.7 against 31.7 percent) but fewer right (55.8 against
68.3) and only 1.1 times fewer tokens against a bar of 2. Two reasons, both read from the rows:

1. The 7B model's self-check says YES almost every time (2.37 calls per task against the 3B's 6.00), so the model
   checker is cheap here and catches little; the gate's token advantage shrinks to a tenth. Its wrong-answer
   advantage stays, which is the reliability half of the claim.
2. **A gate bug, found by this run:** 21 of R's 60 refusals were correct extract answers refused because the input
   wrote the month as a word ("7 January 2026") and the numbers fact wanted the month number to appear in the
   input. That is a false refusal, and it cost R most of its extract accuracy (40 against A's 90 percent). A
   `dates(text) in input` fact fixes it; R3, below, is the rerun. The 3B run had three of the same refusals.

The other refusals were right: 30 calculate answers that were explanations instead of a number (A and B were 0
percent right on calculate too; B handed those over as checked), and 9 format answers with a tag or title not in
the note.

**R against C:** PASS (11.7 against 25.0 percent wrong). **R against G:** G far ahead again, as before.

## R2 and R3 (post hoc, labelled; reported beside the first result, never instead of it)

- R2, llama3.2:3b, strings fact exact with case: original wrong 4.2 to 1.7 percent (the three capitalised titles
  caught), held-out 4.2 to 3.3 percent.
- R3, both models, with the dates fact (held-out, three seeds, same B rows as the comparison):

| Model | Design | Right | Wrong | No answer | Tokens per correct | R vs B bar |
|---|---|---|---|---|---|---|
| llama3.2:3b | B | 31.7% | 68.3% | 0% | 2,749 | |
| llama3.2:3b | R (first run) | 49.2% | 4.2% | 46.7% | 607 | PASS, 4.5x |
| llama3.2:3b | R3 (dates fact) | 60.0% | 3.3% | 36.7% | 464 | PASS, 5.9x |
| qwen2.5-coder:7b | B | 68.3% | 31.7% | 0% | 520 | |
| qwen2.5-coder:7b | R (first run) | 55.8% | 11.7% | 32.5% | 468 | NO (right below B, 1.1x) |
| qwen2.5-coder:7b | R3 (dates fact) | 69.2% | 8.3% | 22.5% | 325 | NO on tokens only: right 69.2 vs 68.3, wrong 8.3 vs 31.7, 1.6x against a bar of 2 |

  With the false refusals gone, the gate beats the model checker on right and wrong answers on both models. The
  token bar still fails on the 7B, for the reason given above: that model's self-check is cheap. The 7B's
  remaining wrong answers are all calculate: a bare number in the right shape with the wrong arithmetic (10 of 30),
  which a shape gate cannot see and a relation that computes the sum would.

## What it means, and what it does not

- The claim that stands: on this model and these tasks, a deterministic gate written in the relation language beats
  a model checking a model on every measure at once, wrong answers, right answers and tokens per correct answer.
  The pipeline's checker was the part that cost the most and caught the least.
- The gate's honest edge is exactly where the language said it would be: it cannot judge sentiment and it cannot
  check arithmetic without the relation that computes it. Those are the fork and the seed, respectively.
- One model, one machine, tasks written by the same person who wrote the gate program; the held-out set is the
  guard against that, and it is where the numbers above come from. A first result, not proof for every model.
- Nothing here is a speed claim: R's answers took longer than A's (two calls on average) and less than B's.
