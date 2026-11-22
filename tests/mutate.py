"""Test the tests: plant one bug at a time in relation.py and see whether tests/test_relation.py notices.

This is what TestThisPuppy does for Java with PIT, written small for Python because the harness has no Python
engine yet and mutmut does not run natively on Windows. Run: python tests/mutate.py
Deterministic: the same mutations in the same order every time. A surviving mutant is a bug the tests would miss.
"""
import ast, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, 'relation.py')
TESTS = os.path.join(ROOT, 'tests', 'test_relation.py')

SWAP_BIN = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult}
SWAP_CMP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
            ast.Is: ast.IsNot, ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In}


def mutants(tree):
    """Yield (description, mutated tree) for every single-point change we know how to make."""
    for i, node in enumerate(ast.walk(tree)):
        kind = None
        if isinstance(node, ast.BinOp) and type(node.op) in SWAP_BIN:
            kind = ('binop', SWAP_BIN[type(node.op)]())
        elif isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in SWAP_CMP:
            kind = ('compare', SWAP_CMP[type(node.ops[0])]())
        elif isinstance(node, ast.Constant) and isinstance(node.value, bool):
            kind = ('bool', not node.value)
        elif isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
            kind = ('int', node.value + 1)
        elif isinstance(node, ast.Return) and node.value is not None:
            kind = ('return', None)
        elif isinstance(node, ast.BoolOp):
            kind = ('boolop', ast.Or() if isinstance(node.op, ast.And) else ast.And())
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            kind = ('not', None)
        if kind is None: continue
        yield i, node.lineno, kind


def apply(source_text, index, kind):
    tree = ast.parse(source_text)
    node = list(ast.walk(tree))[index]
    what, value = kind
    if what == 'binop': node.op = value
    elif what == 'compare': node.ops = [value]
    elif what in ('bool', 'int'): node.value = value
    elif what == 'return': node.value = ast.Constant(None)
    elif what == 'boolop': node.op = value
    elif what == 'not':
        node.op = ast.UAdd()          # `not x` becomes `+x`: the test is gone
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def tests_pass(workdir):
    # the same run every time: fixed hash seed, and no bytecode cache (a mutant written in the same second with the
    # same file size as the last one would otherwise run the LAST mutant's compiled code)
    env = dict(os.environ, PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1')
    try:
        r = subprocess.run([sys.executable, '-B', os.path.join(workdir, 'tests', 'test_relation.py')], capture_output=True,
                           text=True, timeout=120, cwd=workdir, env=env)
    except subprocess.TimeoutExpired:
        return False          # a mutant that hangs the tests (a loop that no longer ends) is caught by the clock, not by an assert
    return r.returncode == 0


def main():
    text = open(SOURCE, encoding='utf-8').read()
    tree = ast.parse(text)
    plan = list(mutants(tree))
    work = tempfile.mkdtemp(prefix='relation-mutants-')
    os.makedirs(os.path.join(work, 'tests'))
    shutil.copy(TESTS, os.path.join(work, 'tests', 'test_relation.py'))
    shutil.copy(SOURCE, os.path.join(work, 'relation.py'))
    assert tests_pass(work), 'the tests must pass on the unmutated code first'
    killed, survived = 0, []
    for n, (index, line, kind) in enumerate(plan, 1):
        try:
            mutated = apply(text, index, kind)
        except Exception:
            continue
        open(os.path.join(work, 'relation.py'), 'w', encoding='utf-8').write(mutated)
        if tests_pass(work):
            survived.append((line, kind[0], kind[1]))
            print(f'  SURVIVED  line {line:4d}  {kind[0]} -> {kind[1]}')
        else:
            killed += 1
        print(f'\r  {n}/{len(plan)} mutants, {killed} killed, {len(survived)} survived', end='', flush=True)
    shutil.rmtree(work, ignore_errors=True)
    total = killed + len(survived)
    print(f'\n\n{total} bugs planted, {killed} caught by the tests ({100 * killed // max(total, 1)} percent), {len(survived)} survived')
    return 0 if not survived else 1


if __name__ == '__main__':
    sys.exit(main())
