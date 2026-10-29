"""T53 staged runtime diagnostic, deliberately without T52 scientific formulas."""
import json
import sys
import time

START = time.perf_counter()


def mark(stage, **values):
    print(json.dumps(dict(stage=stage, elapsed_seconds=time.perf_counter()-START,
                          **values), allow_nan=False), flush=True)


mark('entry', executable=sys.executable, python=sys.version, mode=sys.argv[1])
import math
import os
from pathlib import Path
mark('stdlib_ok')

mode = sys.argv[1]
assert mode in ('plain', 'dll')
handles = []
if mode == 'dll':
    for relative in ('Library/bin', 'DLLs'):
        directory = Path(sys.executable).parent / relative
        assert directory.is_dir(), directory
        mark('dll_directory_begin', path=str(directory))
        handles.append(os.add_dll_directory(str(directory)))
        mark('dll_directory_ok', path=str(directory))

mark('numpy_import_begin')
import numpy as np
mark('numpy_import_ok', numpy=np.__version__, numpy_file=np.__file__)
mark('array_begin')
a = np.array([1, 2, 3], dtype=np.int64)
assert (a+a).tolist() == [2, 4, 6]
mark('array_ok')
mark('leggauss4_begin')
nodes, weights = np.polynomial.legendre.leggauss(4)
assert len(nodes) == len(weights) == 4
assert all(math.isfinite(float(x)) and -1.0 < float(x) < 1.0 for x in nodes)
assert all(float(x) < float(y) for x, y in zip(nodes[:-1], nodes[1:]))
assert all(math.isfinite(float(w)) and float(w) > 0.0 for w in weights)
assert abs(math.fsum(float(w) for w in weights)-2.0) <= 1e-12
mark('leggauss4_ok', order=4, constant_polynomial_integral_check=True)
mark('complete', scientific_integrand_evaluations=0)
