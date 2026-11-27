# A 12-minute cold preparation did not deliver the neutral composite

The original Blackbody stage on the RTX 5070 Laptop GPU reached D3D12 compute-pipeline creation for its classic main entry. That call had no recorded return before the supervisor stopped the one registered worker. The worker had yet to construct the caustics entry, prepare the scene, draw a frame or read pixels. Warm draw time and the neutral composite therefore remain unmeasured. [Registered input and budget](PROTOCOL.md) · [Worker receipt](evidence/RESULT.json)

| Observed host call | Worker start (s) | Worker return (s) |
| --- | ---: | ---: |
| Device admission | 0.001 | 4.152 |
| Engine construction | 4.154 | 20.704 |
| Create main shader module | 20.720 | 20.742 |
| Create bind-group layout | 20.744 | 20.745 |
| Create pipeline layout | 20.746 | 20.747 |
| Create main compute pipeline | 20.747 | Censored |

The expanded main source and computed kernel key matched the registered values. Module construction took 22.36 ms. After both layouts returned, the trace recorded the main compute-pipeline call. The supervisor clock covered 720.434 s through child termination and cleanup, including 720.427 s on the Windows awake clock. Its longest gap between polls was 0.256 s. The last trace append on the original machine had filesystem time 07:14:25.702 UTC. The registered deadline was 07:26:04.635 UTC, about 699 s later. This interval measures elapsed host time with an outstanding native call. The trace cannot distinguish driver compilation, synchronization or other work inside that call. [Native call ledger](evidence/PHASES.ndjson) · [Supervisor clocks](evidence/EXIT.json)

A separate source check of the unchanged fixture found the stage backdrop enabled, one fabric, no CG rows or footage, and Lume disabled. Its native classic draw dispatches the same main pipeline. Image dimensions affect dispatch size, while the pipeline key depends on source, entry, bindings and workgroup. Preparing a smaller image would still require this key. Caustics is constructed after main, so omitting it would leave the observed call in place. These observations concern setup on one adapter and driver. They provide no image-quality comparison or evidence about an artist's choice. [Fixed constructor](https://github.com/gjnail/blackbody/blob/e2ac951dbfabc6060073943e4c344439ac5f4555/blackbody/engine/stage.py#L229-L245) · [Classic stage draw](https://github.com/gjnail/blackbody/blob/e2ac951dbfabc6060073943e4c344439ac5f4555/blackbody/engine/stage.py#L795-L805) · [Pipeline key](https://github.com/gjnail/blackbody/blob/e2ac951dbfabc6060073943e4c344439ac5f4555/blackbody/engine/gpu.py#L368-L373)

Run `python verify.py evidence` from this directory to check the receipts without a device. The single attempt is consumed. [Measurement code](observe.py) · [Portable verifier](verify.py)
