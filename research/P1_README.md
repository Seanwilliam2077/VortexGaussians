# P1 combustion clocks and particle reuse

P1 compares two opt-in changes with the P0 implementation. `spreadClockMode: 'elapsed'` advances every burning site's fuel, glow, and char each step while retaining the graph-work cap. `spreadParticlePolicy: 'recycle-cold'` lets scene feedback reuse an occupied slot when both temperature channels are below 0.55 and the particle is at least 0.5 simulated seconds old. The default policies remain `legacy` and `block`.

Run from the repository root, after installing the dependencies described in [README.md](README.md):

```sh
node --test research/tests/*.test.mjs
node research/p1-smoke.mjs --out research/runs/p1-smoke
node research/p1-run.mjs --suite all --out research/runs/p1-full
node research/p1-capture.mjs research/runs/p1-images
```

Set `BROWSER_EXECUTABLE` to an installed Chromium or Edge executable if needed. `PLAYWRIGHT_MODULE` can select an existing Playwright installation. The capture runner uses the same environment variables and takes its output directory as its sole positional argument. Every output directory must be new.

The [P1 protocol](P1_PROTOCOL.md) defines the hypotheses and limits. The full matrix separates clock behavior, connected-graph tradeoffs, particle capacity, and feedback-edge controls. Raw per-site states, grouped CSV, method metrics, metadata and source fingerprints are retained. Quick runs validate the pipeline and do not replace the full observation window. The fixed late-burning window is 3–6 seconds; hot particles must be counted alongside burning sites and lost-state proxies.

Elapsed clocks make local fuel evolution independent of graph processing quotas for a fixed ignition history. They do not make graph heat transfer budget independent: a source may burn out before its deferred graph work runs. The candidate reuse policy restores capacity by discarding cold particle state. It is not conservative resampling and may change smoke, circulation and appearance. Reuse scans a full layer to find the coldest eligible particle; candidate examination counts expose that added work. Neither policy normalizes reconstruction density.

The visual runner saves paired 800×600 renders at 1, 3, 6 and 8 seconds, seed 11, 600 particles per layer, a world-fixed simulation and the same camera. Its camera distance is 2.8 for framing, while the numerical matrix uses the original camera distance. It records full snapshots so the world-fixed trajectories can be checked. These are illustrative views, not a perceptual study or a frame-time benchmark.
