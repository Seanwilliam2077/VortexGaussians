#!/usr/bin/env python3
"""Rebuild the bibliography from the published PDF, keeping only what a .tex cites.

    python paper/tools/extract_refs.py paper/source/vortex_gaussians_paper_2026-08-31.pdf paper/main.tex -o paper/refs.bbl

The LaTeX source of the 31-page version is not in this repository, so the reference list
is recovered from the PDF. Entries are split on the hanging indent, which is exact, and each
is emitted as a natbib \\bibitem whose label reproduces the author-year citation.
"""
import argparse, re, sys, unicodedata
import pymupdf


def entries(pdf):
    doc = pymupdf.open(pdf)
    out, cur, active, done = [], [], False, False
    for page in doc:
        if done:
            break
        w = page.rect.width
        d = page.get_text('dict')
        lines = []
        for b in d['blocks']:
            for l in b.get('lines', []):
                t = ''.join(s['text'] for s in l['spans']).strip()
                if t:
                    lines.append((0 if l['bbox'][0] < w / 2 else 1, l['bbox'][1], l['bbox'][0], t))
        lines.sort(key=lambda v: (v[0], round(v[1], 0), v[2]))
        for col, y, x, t in lines:
            if not active:
                if t == 'References':
                    active = True
                continue
            if t == 'A' or 'Per-Slice Solver Pseudocode' in t:
                done = True
                break
            if t.startswith("SIGGRAPH ’27") or 'Zijun Xiao' in t and len(t) < 40 or 'Native Gaussian-Splatting Content' in t:
                continue
            if y < 72 or y > 745:                 # running head and foot
                continue
            left = 52 if col == 0 else 318
            if x < left + 3:                      # flush left: a new entry
                if cur:
                    out.append(cur)
                cur = [t]
            else:
                cur.append(t)
    if cur:
        out.append(cur)
    return out


def join(lines):
    s = ''
    for t in lines:
        if s.endswith('-') and t[:1].islower():
            s = s[:-1] + t
        elif s.endswith(('/', ':')) or re.search(r'doi:\S*$', s) and not s.endswith('.'):
            s += t
        else:
            s += (' ' if s else '') + t
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'(?<=[a-z,])(?=In[A-Z])', ' ', s)
    return re.sub(r'O\(N\s*log\s*N\)', r'$O(N\\log N)$', unicodedata.normalize('NFKC', s)).strip()


def tex(s):
    keep = s.replace('$O(N\\log N)$', '\0')
    for a, b in (('\\', ''), ('&', '\\&'), ('%', '\\%'), ('#', '\\#'), ('_', '\\_')):
        keep = keep.replace(a, b)
    keep = re.sub(r'(https?://\S+?)\.?(?=\s|$)', lambda m: '\\url{' + m.group(1).replace('\\_', '_') + '}', keep)
    return keep.replace('\0', '$O(N\\log N)$')


def surname(name):
    name = re.sub(r'\b(?:Jr\.|III)\b', '', name).strip()
    return name.split()[-1]


def parse(text):
    m = re.match(r'^(.*?)\.? (\d{4})\. ', text) or re.match(r'^(.*?)\. (\d{4})\.', text)
    if not m:
        raise SystemExit('no year in: ' + text[:80])
    authors, year = m.group(1), m.group(2)
    names = re.split(r',\s*and\s+|\s+and\s+|,\s*', authors)
    names = [n for n in names if n and not re.fullmatch(r'(Ed\.|Jr\.)', n)]
    last = [surname(n) for n in names]
    if len(last) == 1:
        label = last[0]
    elif len(last) == 2:
        label = f'{last[0]} and {last[1]}'
    else:
        label = f'{last[0]} et~al\\mbox{{.}}'
    key = re.sub(r'[^a-z]', '', last[0].lower().translate(str.maketrans('äöüéèßłąñ', 'aouee lan')).replace(' ', '')) + year
    return key, label, year


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('tex', nargs='+')
    ap.add_argument('-o', required=True)
    ap.add_argument('--keys', action='store_true', help='list every available key and stop')
    a = ap.parse_args()
    refs = {}
    for raw in entries(a.pdf):
        text = join(raw)
        key, label, year = parse(text)
        while key in refs:                        # same surname and year: greengard1985, ...b
            key += 'b'
        refs[key] = (label, year, tex(text))
    if a.keys:
        print('\n'.join(f'{k}\t{v[0]}\t{v[1]}' for k, v in sorted(refs.items())))
        return
    cited = set()
    for path in a.tex:
        src = open(path, encoding='utf-8').read()
        for m in re.finditer(r'\\(?:cite|citet|citep)\{([^}]*)\}', src):
            cited |= {k.strip() for k in m.group(1).split(',')}
    missing = cited - set(refs)
    if missing:
        sys.exit(f'cited but not in the published list: {sorted(missing)}')
    with open(a.o, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\\begin{thebibliography}{%d}\n' % len(cited))
        for k, (label, year, text) in refs.items():
            if k in cited:
                f.write(f'\\bibitem[{label}({year})]{{{k}}}\n{text}\n\n')
        f.write('\\end{thebibliography}\n')
    print(f'{len(cited)} of {len(refs)} references written to {a.o}')


if __name__ == '__main__':
    main()
