# Independent cloth-and-gas evolution reached frame 145; flame edit remains undecided

The unmodified Blackbody solver ran the smaller lighter through the full six seconds of the released cotton-curtain shot on the NVIDIA/D3D12 device. At the deadline 336 of 5,832 simulated vertices were burning. The native emission and composite readbacks did not complete within the registered worker limit. Consequently the fixed screen-space test has no answer, and the second lighter was not run. This establishes a working outside physical simulation on an authored procedural shot. Visual transfer of a VortexGaussians acceleration method remains untested. [Frozen brief](../t124-external-curtain-observation/PROTOCOL.md) · [Native progress](evidence/pair/L.json) · [Parent timeout](evidence/pair/SUMMARY.json)

| Native frame | Seconds from frame 1 | Burning cotton vertices |
| ---: | ---: | ---: |
| 1 | 0 | 0 |
| 25 | 1 | 0 |
| 73 | 3 | 6 |
| 97 | 4 | 39 |
| 145 | 6 | 336 |

These are sampled occupancies. No first-ignition frame is inferred between snapshots. At frame 145 the recorded native vertex temperatures spanned 300.0953–1154.0801 K. The worker retained full-array SHA-256 for the regular gas scalars, velocities and per-vertex material state at frames 1 through 11, 25, 73, 97 and 145. For every sampled array, selected raw float values can be checked directly from the compact lossless archive. They represent one treatment on one GPU. They do not identify where either treatment's final flame would appear or the first divergence between treatments. [45 numerical array subsets](evidence/pair/L-sampled-values.npz) · [Offline verifier](verify.py)

### What the clocks cover

Seven official binary wheels, including MuJoCo 3.3.7 within Blackbody's declared version range, totaled 9,673,356 bytes (9.23 MiB). Each archived file record gives its official URL, byte size and SHA-256; no wheel or external asset is committed. An isolated zero-render, zero-timestep preparation of the unchanged full brush passed at final quality, using a native 136×160×80 grid and 5,832 cloth vertices. It took 74.10 s including worker startup. Earlier T124 and T125 initialization failures remain in their original records. [Environment and hashes](evidence/WHEELS.json) · [Full native preparation](evidence/preparation/PREPARE.json) · [Preparation wall clock](evidence/preparation/EXIT.json) · [T125 failure](../t125-nvidia-dx12-admission/README.md)

On the fresh L worker, the timed observer had finished physical simulation and readback at 88.55 s and entered the native rendering sequence. The outer host stopped the process at 240.22 s including setup, named device admission, simulation, sampled-field I/O and the uncompleted renders. The receipt marks the start of the rendering sequence; it cannot distinguish shader/pipeline creation, element rendering, GPU transfer or compositing as the limiting operation. Missing projection output cannot be scored as darkness or failure of the lighter. The archive contains zero paired photometric measurements and zero end-to-end performance comparisons. [Last completed phase](evidence/pair/L.json) · [Fixed retry contract](RETRY.md)

An independent follow-up would first qualify native render/readback on a known saved frame, with separate instrumentation around the native fire-element renderer, emission buffer read, composite renderer and composite read. Such a diagnostic could establish the actual resource requirement before another decision experiment. Saving native renderable state at the deadline would separate an offline visualization issue from repeating the physical calculation. The retained plane/vertex subsets are diagnostic and cannot restore the full scene. No further rendering was attempted in T126.

Run `python verify.py` from this directory using Python and NumPy to check the retained data. To reconstruct dependencies, use a fresh temporary runtime, resolve the official CPython 3.12 Windows wheels for `mujoco==3.3.7` and compare them to the archived hashes. The two small GPU bindings, upstream checkout and device are pinned in [T124](../t124-external-curtain-observation/README.md) and [T125](../t125-nvidia-dx12-admission/README.md). [Wheel staging](wheels.py) · [Preparation](prepare.py) · [Unchanged query and diagnostic archive wrapper](pair.py)
