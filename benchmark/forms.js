// The forms: the same instruction, written six ways, for each kind of task.
//
// Every form of one kind asks for exactly the same thing and the same shape of
// answer, so one grader can mark them all. Only the way of saying it changes.
//
//   prose    polite, padded, the way people often write to a chatbot
//   terse    short imperative lines, plain words
//   schema   a labelled outline with the shape of the answer written out
//   code     a function signature and a docstring
//   mixed    plain direction where judgment is needed, structure where the
//            content is structured. The form this project argues for.
//   abbrev   terse, with the words abbreviated. Included as a check: it looks
//            shortest to a person, and the question is whether a model agrees.
'use strict';

const FORMS = ['prose', 'terse', 'schema', 'code', 'mixed', 'abbrev'];

const INSTRUCTIONS = {
  classify: {
    label: 'Review',
    prose: 'Hello! I hope you are doing well. I would really appreciate it if you could please read the customer review below and tell me whether its overall sentiment is positive, negative or neutral. Please reply with just that one word and nothing else, with no punctuation and no explanation. Thank you so much for your help!',
    terse: "Classify the review's sentiment.\nReply with one word: positive, negative or neutral.\nNo other text.",
    schema: 'Task: sentiment of a review\nOutput: positive | negative | neutral\nFormat: one word, nothing else',
    code: 'def sentiment(review: str) -> Literal["positive", "negative", "neutral"]:\n    """Overall sentiment of the review. Output the return value only: one word."""',
    mixed: 'Judge the overall sentiment of the review, as a careful reader would.\nOutput: positive | negative | neutral (one word, nothing else)',
    abbrev: 'Clsfy rvw sntmnt.\nRply 1 wrd: positive, negative or neutral.\nNo othr txt.',
  },
  extract: {
    label: 'Line',
    prose: 'Hi there! Below you will find a single line taken from an invoice or a receipt. Could you please find the date and the amount of money in it for me? I need the date written as year, month and day in the form YYYY-MM-DD, and I need the amount as a plain number without a dollar sign or any commas. Please give me your answer as a JSON object that has the two keys date and amount, and please do not add any other words or explanation. Thanks a lot!',
    terse: 'Find the date and the amount in the line.\nReturn JSON with keys date and amount.\nDate as YYYY-MM-DD. Amount as a plain number, no $ or commas.\nJSON only.',
    schema: 'Task: extract from an invoice line\nOutput: {"date": "YYYY-MM-DD", "amount": number}\nFormat: JSON only',
    code: 'def extract(line: str) -> dict:\n    """Return {"date": "YYYY-MM-DD", "amount": float} found in the line.\n    Output the return value only, as JSON."""',
    mixed: 'Read the line and find when it happened and how much it was for.\nOutput: {"date": "YYYY-MM-DD", "amount": number}\nJSON only.',
    abbrev: 'Fnd date & amt in line.\nRtrn JSON w/ keys date & amount.\nDate as YYYY-MM-DD. Amt as plain nmbr, no $ or commas.\nJSON only.',
  },
  calculate: {
    label: 'Figures',
    prose: 'Hello! I am trying to work out whether something is worth buying. Below I have listed the price of the item, how much money it saves me each time I use it, and the number of times I expect to use it. Could you please work out my net saving for me? That is the saving per use multiplied by the number of uses, with the price then taken away. Please reply with only the final number, without a dollar sign and without any explanation. Thank you very much!',
    terse: 'Work out the net saving: saving per use times uses, minus price.\nReply with the number only. No $ and no explanation.',
    schema: 'Task: net saving\nFormula: saving_per_use * uses - price\nOutput: number\nFormat: number only',
    code: 'def net_saving(price: float, saving_per_use: float, uses: int) -> float:\n    return saving_per_use * uses - price\n# Output the return value only: a number.',
    mixed: 'Work out whether the purchase pays for itself.\nnet = saving_per_use * uses - price\nOutput: net (number only)',
    abbrev: 'Wrk out net svng: svng per use x uses, mns price.\nRply w/ nmbr only. No $ & no explntn.',
  },
  format: {
    label: 'Note',
    prose: 'Hi! Below is a short note describing something I need to do. I would be grateful if you could please turn it into a JSON object for my to-do list. The object should have a key called title containing the task itself as text without the full stop at the end, a key called priority containing the priority as a whole number, and a key called tags containing a list of the tags as lower case strings. Please reply with the JSON object only and do not add anything else. Many thanks!',
    terse: 'Turn the note into a JSON object.\nKeys: title (the task, no final full stop), priority (whole number), tags (list of lower case strings).\nJSON only.',
    schema: 'Task: note to record\nOutput: {"title": string, "priority": integer, "tags": [string]}\nRules: title has no final full stop; tags lower case\nFormat: JSON only',
    code: 'def to_record(note: str) -> dict:\n    """Return {"title": str, "priority": int, "tags": list[str]}.\n    Title has no final full stop. Tags are lower case.\n    Output the return value only, as JSON."""',
    mixed: 'Turn the note into a to-do record. The title is the task itself, without its final full stop.\nOutput: {"title": string, "priority": integer, "tags": [lower case strings]}\nJSON only.',
    abbrev: 'Trn note into JSON obj.\nKeys: title (task, no fnl full stop), priority (whole nmbr), tags (list of lwr case strs).\nJSON only.',
  },
};

// The whole prompt for one task in one form: the instruction, a blank line, then the labelled input.
function prompt(task, form) {
  const kind = INSTRUCTIONS[task.kind];
  return `${kind[form]}\n\n${kind.label}: ${task.input}`;
}
// The input alone, laid out the same way. Its token count is taken off the whole prompt's, to leave the instruction's.
function inputOnly(task) { return `\n\n${INSTRUCTIONS[task.kind].label}: ${task.input}`; }

module.exports = { FORMS, INSTRUCTIONS, prompt, inputOnly };
