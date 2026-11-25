# Native answers at the terminal ignition scan

In this implementation the native scan marks newly ignited sites before processing graph donors, advancing fuel clocks and emitting more gas. An exact query can read those ignition decisions at the terminal scan. Every earlier queried frame still runs to completion so its graph and gas evolution can affect the next frame.

Two continuous 360-step trajectories reproduced every T86 frame's ignition IDs, active and gas counts, retirements and RNG draw count. Both fork and endpoint markers matched. The endpoint hashes were `491894ec` for AB and `115a0126` for BA. Every first regional event and its IDs matched T87. This control profiles the time at which an exact decision becomes available inside the solver.

| Query | Horizon | Windows | Complete terminal step, median ms | Through terminal scan, median ms | Median paired time ratio |
| --- | --- | ---: | ---: | ---: | ---: |
| All site labels | 1 | 6 | 16.95 | 9.30 | 0.564 |
| All site labels | 4 | 6 | 71.80 | 64.90 | 0.896 |
| All site labels | 8 | 6 | 139.90 | 133.10 | 0.950 |
| All site labels | All | 18 | 71.80 | 64.90 | 0.896 |
| First shell ignition or end | 1 | 6 | 16.95 | 9.30 | 0.564 |
| First shell ignition or end | 4 | 6 | 36.85 | 30.70 | 0.750 |
| First shell ignition or end | 8 | 6 | 51.10 | 44.85 | 0.799 |
| First shell ignition or end | All | 18 | 18.60 | 11.85 | 0.637 |

Each time includes all preceding native steps in that query. A shell query stops at the same first event or horizon end under both columns. Shorter regional windows benefit proportionally more from omitting the last tail. Rows reuse frames in two takes of the same asset. The all-site median paired saving was 6.80 ms and the shell median paired saving was 6.90 ms.

## Timing scope

The start precedes the camera update, clock advance and native step. A single browser-clock read immediately after the ignition scan sets the intermediate time. The last read follows the complete step. The recorder obtains material labels outside this interval. No frames are rendered. Within this 15.47 s capture, native stepping took 4.67 s (AB) and 5.42 s (BA), and per-frame state copying and event observation took 37.6 and 41.2 ms, respectively. The capture receipt contains source checks, browser launch, setup, boundary state reads, browser communication, compression and teardown times.

The paired values include the instrumented clock read and use a single sample per native frame. Returning an answer from a separately dispatched partial step would also need result extraction and, for an interactive query, a policy for resuming the partially completed frame. The profile excludes those costs along with checkpoint loading and shell construction. Its timings compare alternatives **within the same take and execution**. Cross-run wall times from different tasks do not form a paired measurement.

## Reproduction

Run `python score.py` from this task or pass the full script path from another directory. It uses only the published per-frame timing ledgers, T86 public evidence and T87 regional decisions. `SCORE.json` includes every window and horizon. `evidence/CAPTURE.json` pins the data and executable identities.

The optional `node capture.mjs --check` preflight checks the original T86 staged HTML digest, identities and instrumented JavaScript without launching a browser. To reproduce the two takes, run `node capture.mjs <fresh-output-directory>` with the same Node, Playwright and browser build and the external T42 foreground PLY. `PLAYWRIGHT_MODULE`, `BROWSER_EXECUTABLE` and `T86_PLY` locate those dependencies on another host. The original observation receipt is protected by exclusive creation of the run marker.
