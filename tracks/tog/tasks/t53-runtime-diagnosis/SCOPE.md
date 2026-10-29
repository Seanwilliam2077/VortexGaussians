# T53 — bounded runtime diagnosis

Parent: `bf82b773af15ceb74d952ddd7c4ef477f3677260`. The previous goal turn made progress: T52 derived a stronger ordinary tangent baseline and preserved one failed scalar-verification attempt. It did not validate numerical values. The complete SIGGRAPH/TOG goal remains active and unachieved.

## Question and decision

Can a staged diagnostic reproduce and localize the current runtime failure, and can an existing runtime execute the small numerical prerequisites without installing or persistently changing anything? This is preparation for a later separately specified scientific check. T52's failure, lack of output and unknown original phase remain unchanged. A new stage-localized failure is evidence about this diagnostic, not a retroactive trace of T52.

## Frozen budget and branches

At most three diagnostic child launches, each with a 20-second subprocess timeout. Root launches each separately and inspects its saved terminal evidence before selecting an eligible branch. All use `-I -B -u -X utf8`, the repository working directory and the same frozen `probe.py`. A single-use receipt per slot prevents accidental duplicate execution. No detached workers.

1. A: existing research Python `C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/python.exe`, mode `plain`, inherited environment.
2. B: only if A reaches `numpy_import_begin` but not `numpy_import_ok`, using the same Python in `dll` mode. Register only its existing `Library/bin` and `DLLs` directories using `os.add_dll_directory`, retaining handles until process end. No PATH mutation, package edits or persistent environment settings. If A passes or fails elsewhere, skip B.
3. C: only if no completed diagnostic so far passes all stages, use the existing bundled Python `C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`, mode `plain`. A pass in another runtime is an available preparation route, not attribution of the original cause. Stop on its result.

Each child emits flushed JSON stages for entry/stdlib, optional DLL registration, NumPy import, exact small integer array arithmetic and `leggauss(4)`. The last operation checks four finite interior ordered nodes, positive finite weights and the integral of the constant polynomial within absolute 1e-12. It does not evaluate T52's ell, J, beta, E or kappa expressions. No orders 128/256/512, workload integrands, fluid simulation, GPU, rendering, tuning, package installation, source-code acquisition or additional runtime search. A four-node pass does not qualify the larger T52 node generator or its scientific measurement.

Save commands, interpreter and probe identities, whitelisted Python/NumPy version and module metadata when reached, stage logs, exit codes, timeout/launch errors and actual supervised wall time. Record diagnostic arithmetic separately from scientific invocations (zero). Time is diagnostic cost, not an algorithm benchmark. Input-identity mismatch invalidates a pass and stops all later slots. Missing end markers stay unknown: no entry cannot distinguish startup from the initial json/sys/time imports, and a B registration failure is not a completed NumPy import test. Stop this task after the allowed branches and review, even if all fail; do not infer a DLL name or root cause from an exit code alone.

## Limited API evidence and provenance

One official Python documentation page was opened and searched once during preparation: [os.add_dll_directory](https://docs.python.org/3/library/os.html#os.add_dll_directory), section displayed as lines 3195–3210 on 30 October 2026. It documents extension-dependency search and removable handles. This justifies the temporary diagnostic API, not the hypothesis that missing search directories caused T52. No research-paper/source batch was opened. The public page was labelled Python 3.15.2; local runtime versions are recorded by the probe rather than inferred from that label.

After execution, one independent readback checks branch eligibility, stage evidence, frozen identities and limits. New scientific execution, any runtime repair and an application-quality requirement need a subsequent explicit finite protocol. Historical outcomes, art inactivity, main and the deleted automation are preserved.
