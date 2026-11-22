"""Runs the five problems and prints one line per gate verdict. Run: python problems/run_all.py
Exit code 0 only when every gate passed.
"""
import os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
failed = 0
for name in ('hanoi', 'tsp', 'philosophers', 'cube', 'enigma'):
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, '-B', os.path.join(HERE, name + '.py')], capture_output=True, text=True, timeout=900)
    out = r.stdout.strip().splitlines()
    verdicts = [l for l in out if 'PASS' in l or 'FAIL' in l]
    # the naive philosophers protocol is MEANT to fail its gate; every other FAIL is a failure of ours
    bad = [l for l in verdicts if 'FAIL' in l and 'naive' not in l]
    failed += bool(bad) or r.returncode != 0
    print(f'{name:13s} {"ok " if not bad and r.returncode == 0 else "BAD"}  {len(verdicts)} gate verdicts  ({time.perf_counter() - t0:.1f} s)')
    for l in verdicts: print('   ', l[:150])
    if r.returncode != 0: print('   ', (r.stderr.strip().splitlines() or ['no error text'])[-1])
sys.exit(1 if failed else 0)
