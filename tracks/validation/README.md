# Dual-track integration checks

The subsequent numerical screens have their own [T03 independent audit](t03-review.md) and [plots](t03-20261027-v2/README.md), followed by [T04's joint feasible result](t04-review.md) and [plots](t04-20261027/README.md), [T05's ordinary cold start](t05-review.md), and [T07's ordinary timing revision](t07-review.md) with [saved plots](t07-20261027/README.md). The interface checks below do not validate those research results.

27 October 2026. These checks establish software behavior, not artistic merit, physical realism, or a TOG contribution.

The independent CPU/HTML audit is [recorded separately](../evidence/INTEGRATION_REVIEW.md). The root agent additionally ran [art-ui.mjs](art-ui.mjs) through the visible browser controls in headless Edge 149.0.4022.52, using the existing WebGL demo. It never injected simulator state or called `__demo` from the harness. Thirteen interaction checks passed with no page exceptions; [machine-readable result](art-ui-20261027/result.json) pins the tested sources.

The real scene loaded 45,808 points. The visible default ignition count was 2,483; 60 steps advanced one simulated second and stopped. Explicit pause and stage changes stopped time; reinitialization cleared visible burn counters and preserved a note. Export/reload, correct camera units in the exported metadata, local-file loading and incomplete-audience-record rejection passed. The 390 px layout had no horizontal overflow and was visually inspected. Hidden-tab behavior and cross-browser consistency were not exercised in this run. No performance or physical-correctness benchmark was attempted.

The [exported journal](art-ui-20261027/journal.json) contains one explicitly labeled automated interface-test draft, **not a participant response or artist observation**. Browser context and test server were closed after the run.

| View | Saved frame |
|---|---|
| Loaded and paused | [Initial scene](art-ui-20261027/loaded.png) |
| One simulated second after ignition | [Flame frame](art-ui-20261027/after-one-second.png) |
| Reinitialized scene | [Reset](art-ui-20261027/reset.png) |
| 60 degree slider | [Changed view](art-ui-20261027/yaw60.png) |
| 390 px layout | [Narrow page](art-ui-20261027/narrow.png) |

The images show a synthetic low-detail campfire fixture, not a captured personal place. Usable controls do not establish the proposed memory theme.

## Repeat locally

Use the existing Playwright dependency in `research/`, or set `PLAYWRIGHT_MODULE` to an installed module and `BROWSER_EXECUTABLE` to Edge/Chromium. No installation is performed. Run from the repository root; use a fresh output directory whose parent exists:

```sh
node tracks/validation/art-ui.mjs tracks/validation/runs/art-ui-next
```

The harness starts a temporary loopback server, creates a fresh browser context, saves results and closes both. Outputs under `runs/` are ignored. The UI performs only bounded simulation segments, and the harness waits up to 90 seconds per observed transition; failure is saved rather than silently retried.
