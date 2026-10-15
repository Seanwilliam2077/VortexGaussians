# Standard physical reference (P5c)

This isolated Python reference uses explicit `Gamma = volume * vorticity`,
source-only Gaussian Biot–Savart kernels, the full velocity Jacobian,
volume-weighted Shepard temperature and its own quotient-rule gradient.
It is standard numerical infrastructure, not a new fluid algorithm.
It does not change or replace the browser demo's runtime.

Validated environment: Python 3.12.14 and NumPy 2.3.5. No SciPy, CUDA or
third-party fluid solver is used. Run these commands from this directory:

```sh
python test_core.py
python run.py --out fresh-exploratory-run
```

The evidence archive contains a source freeze and the original formal run.
From its `source` directory, reproduce or independently audit with:

```sh
python run.py --formal --freeze ../source-freeze.json --out ../new-formal-run
python audit.py ../formal --freeze ../source-freeze.json --out ../new-audit.json --fault-injections
```

Output directories/files must be new; saved evidence is never overwritten.
`PROTOCOL.md` records the design before the joint source freeze. Its opening
draft-status sentence is historical; `source-freeze.json` and the completed
formal manifest establish the actual frozen run.

The 21 cases cover measure/split consistency, analytic kernel derivatives,
fixed-width filtered-field quadrature convergence, temperature reconstruction,
buoyancy source units, and two prescribed ODEs. They do not validate coupled
Navier–Stokes evolution, periodic Biot–Savart, viscosity, walls, combustion,
long-time stability, rendering quality, speed or research novelty.
