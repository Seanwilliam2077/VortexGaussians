#!/usr/bin/env python3
"""Pre-registered analysis of the flame 2AFC study. Standard library only.

    python study/analyze.py results/*.csv

Written before any data exists, and frozen by this commit. It does what the paper
says it does and nothing else:

  * pooled two-sided exact binomial test against chance, per condition tag
  * Wilson 95% interval on the proportion
  * a per-participant direction count, so a pooled effect driven by a minority is visible
  * no outlier rejection and no response-time filtering

"chose A" means the paper's method, or the condition switched on. The target is N >= 12
participants; below that the script still prints its table, and says it is under target.
"""
import csv, glob, math, sys
from collections import defaultdict

TAGS = ['solver', 'source', 'interz', 'couple', 'bloom']
TARGET_N = 12
TRIALS_PER_PERSON = 18


def binom_two_sided(k, n, p=0.5):
    """Exact two-sided p: the mass of every outcome no more likely than the observed one."""
    pmf = [math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(n + 1)]
    return min(1.0, sum(q for q in pmf if q <= pmf[k] * (1 + 1e-9)))


def wilson(k, n, z=1.959964):
    if n == 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def load(paths):
    people = {}
    for path in paths:
        with open(path, newline='', encoding='utf-8') as f:
            people[path] = list(csv.DictReader(f))
    return people


def analyze(people):
    pooled = defaultdict(lambda: [0, 0])
    per_person = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for person, rows in people.items():
        for r in rows:
            tag, a = r['tag'], int(r['choseA'])
            pooled[tag][0] += a
            pooled[tag][1] += 1
            per_person[tag][person][0] += a
            per_person[tag][person][1] += 1
    out = []
    for tag in TAGS:
        k, n = pooled[tag]
        if n == 0:
            continue
        lo, hi = wilson(k, n)
        people_for = sum(1 for a, m in per_person[tag].values() if 2 * a > m)
        people_against = sum(1 for a, m in per_person[tag].values() if 2 * a < m)
        people_tied = len(per_person[tag]) - people_for - people_against
        out.append(dict(tag=tag, k=k, n=n, rate=k / n, lo=lo, hi=hi, p=binom_two_sided(k, n),
                        people_for=people_for, people_against=people_against, people_tied=people_tied))
    return out


def main(argv):
    paths = sorted(p for a in argv for p in glob.glob(a))
    if not paths:
        sys.exit(__doc__)
    people = load(paths)
    short = [p for p, r in people.items() if len(r) != TRIALS_PER_PERSON]
    print(f'participants: {len(people)} (target >= {TARGET_N})')
    if len(people) < TARGET_N:
        print('UNDER TARGET: this table is not the pre-registered result.')
    if short:
        print(f'incomplete sessions kept, as registered: {len(short)}')
    print(f'{"tag":<8}{"A/n":>9}{"rate":>7}{"95% Wilson":>17}{"p":>9}   {"for/against/tied":>16}')
    for r in analyze(people):
        print(f'{r["tag"]:<8}{r["k"]:>5}/{r["n"]:<3}{r["rate"]:>7.3f}   [{r["lo"]:.3f}, {r["hi"]:.3f}]'
              f'{r["p"]:>9.4f}   {r["people_for"]:>6}/{r["people_against"]}/{r["people_tied"]}')


if __name__ == '__main__':
    main(sys.argv[1:])
