# P6: exact compact-support exchange cost screen

This is a standard spatial-hash baseline and a bounded CPU cost/sparsity measurement. It is not a new approximation, a full-system benchmark, or a realism experiment. No measured outcome is available when this design is written. All fine thermal states remain explicit. No coarsening, caps, source, loss, motion, combustion, or rendering occurs.

## Frozen inputs and nine cases

IDs are `s500-smooth`, `s500-hotpatch`, `s500-checkerboard`, then the same three suffixes for `s5000` and `s50000`, in that order. Each executes one outer step of 1/60 s.

Two surface rectangles lie at x=-0.2 and +0.2 m; each covers y=[0.1,0.9], z=[-0.4,0.4] and has area 0.64 m². Midpoint tensor grids per plane are (ny,nz)=(10,25), (50,50), (100,250), respectively. This gives total surface counts 500, 5000, 50000; anisotropic discretizations are intentional. Each surface node has area 1.28/N and area heat capacity 2 J/(m² K).

Gas is a 10×10×6 midpoint grid over x=[-0.2,0.2], y=[0.1,0.9], z=[-0.4,0.4]. Every parcel has volume 0.256/600 m³ and volume heat capacity 3 J/(m³ K). Surface order is side, y, z; gas order is x, y, z, each ascending. Node IDs encode these indices. All surface nodes precede gas nodes.

Temperatures are physical-coordinate functions, unchanged across resolutions:

- Smooth: surface 320+40(y-0.1)/0.8+20(z+0.4)/0.8 K; gas 600+80(x+0.2)/0.4+60(y-0.1)/0.8-40(z+0.4)/0.8 K.
- Hotpatch: surfaces 300 K. Gas 900 K iff x²+(y-0.5)²+z²<0.12², otherwise 300 K.
- Checkerboard, both kinds: 300+500 mod2(floor((x+0.017)/0.125)+floor((y+0.031)/0.125)+floor((z+0.047)/0.125)) K. mod2 returns 0 or 1 even for negative arguments. The fixed shifts avoid coincident cell boundaries; this is not a node-index pattern.

## Identical physical operator and schedule

h=0.30 m, beta=4 W/(m² K). For surface i and gas j, r=sqrt((dx*dx+dy*dy)+dz*dz). Strict support is r<h. G=beta*A_i*V_j*[3/(pi*h*h*h)]*(1-r/h), with the written JS evaluation order. This is the same mathematical kernel as P4a; the explicitly declared scalar distance differs from P4a's Math.hypot only by floating-point evaluation. A tiny P4a comparison uses tolerance, not bitwise equivalence.

C_i is authored measure times capacity density. Degrees sumG are accumulated in canonical surface-i/gas-j order. Every method uses n=max(1,ceil(dt*max_i(sumG_i/C_i)/0.9)), capped only by an error at 100000 (never truncated). Each substep synchronously reads old T, accumulates Q=dt_sub*G*(T_j-T_i) with opposite signs using per-node Kahan summation, then updates T. No clipping occurs. Energy and flux ledgers use Kahan sums. Full final temperatures and every node's degree and neighbor count are retained.

An independent auditor reconstructs all pairs. Complete CSR topology must match its independently reconstructed topologySHA256 exactly: SHA256 of rowOffsets:uint32LE[ns+1] followed by local gasIndex:uint32LE[E], excluding G. This hash is computed outside timing and is also checked across methods and fresh-state trials. The auditor reports a support-boundary band |r-h|<=8*eps*max(h,r) for diagnosis only; band membership does not exempt any topology-hash, temperature, or degree mismatch. Implementation checks: finite temperatures, initial min/max within 1e-9 K, relative energy drift and opposite debit/credit <=1e-12 using max(1 J,|E_initial|), independent final temperature error <=1e-9 K, relative degree error <=1e-12 with denominator max(1 W/K,|reference|). All producer methods must have identical canonical graph and final-temperature binary hashes. No empirical cost threshold decides scientific success.

## Exact builders and memory

`allpairs-rebuild` enumerates all N_surface×600 pairs and is a correctness/cost diagnostic, not a competitor used to claim a new method. `hash-rebuild` hashes the 600 gas nodes into cells of side h using Math.floor, including negative coordinates. For each surface point it gathers the 27 neighboring cells, sorts local gas IDs ascending, and performs the same exact distance test. No candidate cap or support shrink is allowed.

Both builders make two enumeration passes: count exact edges, allocate exact-sized CSR, then fill G and degrees. This avoids a hidden oversized allocation advantage. Candidate counts are per pass; reported distance evaluations count both passes. The hash index is built once per graph. A surface cell's sorted candidate list is cached within that build and reused by all its surface nodes and by the second pass. Bucket lookups therefore equal 27 times distinct encountered surface cells; sorting/index/cache allocation cost remains inside graph build. Cache entries, hits and typed-array payload are recorded. CSR uses uint32 rowOffsets, uint32 local gas indices, float64 G; sumG is float64 and neighborCount uint32. Exact owned typed-array payload is reported, not process peak memory; unknown Map/string/object overhead is null rather than invented. There is only one live graph at a time. Large-case raw files omit edge triples but retain every node's sumG and neighbor count, edge count, canonical CSR SHA256 and full output temperatures. N=500 retains canonical [surfaceGlobalIndex,gasGlobalIndex,G] triples. Three temperature patterns on the same positions do not constitute geometry generalization.

## Measurement contract

Each case has one full untimed warmup per method, then five fresh-state trials per method. Method orders are [allpairs,hash-rebuild,hash-cached], [hash-rebuild,hash-cached,allpairs], [hash-cached,allpairs,hash-rebuild], [hash-cached,hash-rebuild,allpairs], [allpairs,hash-cached,hash-rebuild]. Five repeats are not perfectly order balanced.

Every trial constructs a fresh graph. `hash-cached` explicitly records preprocessing `buildSetupMs`, then reports the cost of one application after preprocessing; it does not hide setup, assume a reuse count, or represent changing geometry. `applicationMs` includes build+exchange for the rebuild methods, only exchange for the cached application. `totalWithSetupMs` includes both for all methods. Build includes index construction, candidate enumeration, sorting, graph allocation, G, degrees and CFL rate. Exchange includes scratch allocation, finite checks, energy/flux ledgers and all substeps. Input packing and initial-temperature clone are outside all intervals identically; SHA, JSON serialization and independent validation are also outside. Node --expose-gc is required; forced GC occurs outside each trial, with the previous graph released. Incidental GC inside a measured interval is naturally included.

CPU performance.now wall times are not GPU-completed render times or frame FPS. Report all five raw timings and median/min/max; the stored floor-index 95th percentile over five samples is labeled explicitly and is descriptive only. There is no 10% frame-cost criterion and no full-system speedup inference.

## Evidence and freeze

Producer files are design.mjs, core.mjs, run.mjs, test.mjs, PROTOCOL.md; independent audit.py and the unchanged, locally copied p4-thermal-reference.mjs are also SHA256-pinned. The latter has SHA256 73b367b9009c5fd36c92100eb8e40ac82ac2ab66e10e2b61acb395949f58aefe and is used only by tiny correctness tests, never as a timed competitor. Formal execution requires an externally frozen source-hash mapping and a new/empty output directory. The source mapping is checked before and after, including failure; authored input is hashed before/after each case. Manifest contains planned IDs, host/runtime, complete timing semantics, per-case byte size and file SHA. Each case includes authored nodes and parameters, per-method output graph summaries, full final T, ledgers and all trial records. inputSHA256 hashes UTF-8 JSON.stringify(input); graph and temperature binary hashes use little-endian buffers with explicit ordering. Final producer status remains pending-independent-audit; successful execution is distinct from independent correctness.

Only tiny synthetic wiring/unit fixtures may run before source freeze. Formal command:

```
node --expose-gc run.mjs --formal --freeze freeze.json --out NEW_DIRECTORY
```

Unit command: `node --test test.mjs`. Neither command modifies the VortexGaussians repository or older evidence.
