"""Bloom and fold between the terse form a model writes and the readable form a person reads.

Terse (what the model emits, forced by the server):   {"date": ["2026-03-03", "March 3, 2026"], "amount": ["240", "$240.00"]}
Readable (what a person is shown):                    date = 2026-03-03 from "March 3, 2026"
                                                      amount = 240 from "$240.00"

The round trip is exact: fold(bloom(t)) == t for every terse answer, including odd characters in values and
sources, because the readable form escapes quotes and newlines the way JSON does and the fold reads them back.
Nothing is lost on the way out and nothing is invented on the way back.

    python render.py bloom '<terse json>'     prints the readable lines
    python render.py fold  < readable lines   prints the terse json
"""
import json
import re
import sys

LINE = re.compile(r'^(\w+) = (.*) from (".*")$')


def bloom(terse):
    """Terse JSON text -> readable relation lines. The value is shown bare; the source is a JSON string literal,
    so quotes and newlines inside it survive."""
    obj = json.loads(terse)
    lines = []
    for name, pair in obj.items():
        value, source = pair
        lines.append(f'{name} = {json.dumps(value)[1:-1] if needs_escape(value) else value} from {json.dumps(source)}')
    return '\n'.join(lines)


def needs_escape(value):
    """Escape when JSON would write the value differently (control characters, quotes, backslashes, anything
    non-ASCII) or when it has leading or trailing space; a plain value is shown as it is."""
    return json.dumps(value)[1:-1] != value or value != value.strip()


def fold(readable):
    """Readable relation lines -> terse JSON text, with the keys in the order the lines came."""
    obj = {}
    for line in readable.splitlines():
        if not line.strip(): continue
        m = LINE.match(line)
        if not m: raise ValueError(f'not a relation line: {line}')
        name, value, source = m.groups()
        obj[name] = [json.loads('"' + value + '"') if needs_unescape(value) else value, json.loads(source)]
    return json.dumps(obj)


def needs_unescape(value):
    return '\\' in value


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'bloom': print(bloom(sys.argv[2]))
    elif len(sys.argv) > 1 and sys.argv[1] == 'fold': print(fold(sys.stdin.read()))
    else: print(__doc__)
