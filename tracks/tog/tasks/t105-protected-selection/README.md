# Protecting a selected patch after the second stroke

Changing the query from brush spill to a fixed selection produced a strong order effect on the already fitted Playground geometry at seed 43. Of 1,822 selected material sites, 1,631 were still cold just after the A→B edit. The first selected ignitions followed after 22 steps. With the opposite order only 30 sites remained eligible and four ignited after three steps. Full replay and both frozen prefix methods returned a valid first-frame witness in every trial. Both responses arrived within a single certified prefix. [Pre-registered task](PROTOCOL.md) · [Reference including all tied site IDs](REFERENCE.json)

The protected site, original index 3271, is the nearest available material point to the arithmetic midpoint of the two brush centers. Snapping moved the center 0.3384 world units. Its radius-0.12 ball intersects 191 static B contacts and zero A contacts. The choice uses the original ordered sites and remains fixed for both shots. Directly ignited or already burning members are removed at the click. The sphere's partial overlap with B and the near depletion in B→A limit a literal interpretation as a patch untouched by the strokes. This is a prospective transfer of task and seed on known geometry. The earlier Playground shell experiments use a different seed and region. [Frozen static selection](selection.json) · [Exact registered material IDs](selection-ids.json.gz)

## Time from second brush to answer

Numbers give median host-delivered milliseconds and the measured minimum–maximum in parentheses. Each method had one warmup and four balanced repeats per edit. Simulated step time is 1/60 s. Both registered requests have a three-second deadline.

| Order | Eligible | First frame (ties) | Full, retained active index | Prefix then restart | Prefix then repair | Full, fresh active index |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A→B | 1,631 | 202 (12) | 274.3 (259.2–298.2) | 194.9 (190.8–204.4) | 206.8 (185.0–215.6) | 318.5 (287.3–351.2) |
| B→A | 30 | 183 (4) | 43.9 (39.0–45.4) | 37.1 (32.9–41.3) | 41.2 (38.2–44.3) | 69.0 (68.2–75.4) |

The initial certificates allowed 59 and 41 steps respectively. None of the measured branches needed recovery. The repair operator nevertheless allocated 112,640 and 15,360 log bytes. Its delivery ratios to ordinary retained replay were 0.754 and 0.938. In the three-step case its observed range overlaps full replay. The restart variant had the smallest median in both edits. The four methods received the same static input, applied the same stroke and rebuilt the protected selection inside the timer. First-use retained indexes cost 27.0 and 39.3 ms, with typed payloads of 405,715 and 407,047 bytes. Rotation charged these builds to different warmup calls. Each fresh full query indexed 73,256 and 73,892 recipients respectively. The pre-click replay from frame 0 to 180 took 4.17 and 7.75 s. The independent native worker took 39.18 s and the complete timed worker with all capture and validation phases took 46.59 s. [Per-edit medians, ranges and memory](SCORE.json) · [Raw query reports including setup, guards and graph work](evidence/timing/CAPTURE.json)

The standalone scorer checked the two full 360-frame continuations, independent registered site IDs, stroke contacts, both eligible counts, all 40 issued calls including warmups, and eight-frame ordinary full-state audits and the slice audit to its first regional event. These two positive trajectories expand the tested author-defined tasks. They add no right-censored click, natural repair boundary, or evidence of an animator's actual preference. The choice of patch and seed was committed before the new native labels. One source-staging substitution initially matched two strings in the parent runner. Making it match the declaration alone fixed the prelaunch assertion after reference capture. Timing and numeric plugins then ran with the original methods, selection, seed and rotation; the raw receipt includes the final runner digest. [Frozen algorithm and region](run.mjs) · [Independent reference capture](evidence/native/capture-report.json)

## Reproduce

Check the archived answer and timings from this folder with Python 3.9 or later. The offline checks use the standard library.

```shell
python reference.py
python score.py
```

For new simulations, stage the identical third-party PLY using T101's asset recipe. Build the T93, T94, T95, T97, T100 and T102 native plugins from their respective build or prepare scripts. Run `python prepare.py` with NumPy. The script verifies the frozen recipe, site membership and geometry pins. `node capture.mjs <fresh-reference-dir>` runs the two independent takes. For a full repeat in a fresh checkout, use `node capture.mjs evidence/native` with the published evidence directory sequestered; the worker requires a fresh destination. The native runner accepts `node run.mjs --out <fresh-timing-dir>` and reads the archived native ledger from `evidence/native`. Score the separate timing capture using `python score.py --timing-dir <fresh-timing-dir>`. [Upstream asset preparation](../t101-playground-holdout/prepare.py) · [Benchmark adapter](run.mjs) · [Offline verification](score.py)
