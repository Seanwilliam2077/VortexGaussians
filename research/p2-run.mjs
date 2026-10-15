import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';
import { parseArgs } from './lib/design.mjs';
import { assertSnapshot, measure, timeseriesCsv } from './lib/metrics.mjs';
import { startServer, launchBrowser, openResearchPage, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { p2Fixture } from './p2-fixtures.mjs';
import { configureP2, compareP2, refinementCurveError } from './p2-design.mjs';

export function checkP2Snapshot(snapshot, f) {
  assertSnapshot(snapshot);
  if (typeof snapshot.particleStateHash !== 'string' || !snapshot.particleStateHash) throw new Error('Missing real particleStateHash from P2 runtime');
  if (!snapshot.areaFeed || !Number.isFinite(snapshot.scene.representedArea)) throw new Error('Missing P2 area ledger/scene measure');
  if (Math.abs(snapshot.scene.representedArea - f.representedArea) > 1e-10) throw new Error('Runtime represented area disagrees with authored fixture');
  if (snapshot.points.some(p => !Number.isFinite(p.areaWeight) || p.areaWeight <= 0)) throw new Error('Runtime lost authored positive areaWeight');
  if (snapshot.particles.layerCounts.some(n => n > snapshot.params.ppl)) throw new Error('Particle layer capacity exceeded');
  if (snapshot.params.spreadMeasureMode === 'area') {
    const c = snapshot.counters, credit = snapshot.areaFeed.creditBalance;
    const residual = c.areaFeedCreditsGenerated - c.areaFeedAttempts - c.areaFeedServiceCapDropped - c.areaFeedCancelledCredits - credit;
    if (Math.abs(residual) > 1e-8 * Math.max(1, c.areaFeedCreditsGenerated)) throw new Error(`Area credit ledger mismatch: ${residual}`);
    if (c.areaFeedAttempts !== c.areaFeedAdmitted + c.areaFeedBlocked) throw new Error('Area admission ledger mismatch');
    if (credit < 0 || credit >= 1 || snapshot.areaFeed.wholeEventsPending !== 0) throw new Error('Area feed retained integer event debt');
  }
  return snapshot;
}

export async function runP2Case(browser, baseUrl, definition, timeout = 120000, onSample) {
  const f = p2Fixture(definition.kind, definition.variant, definition.order);
  const { page, errors, graphics } = await openResearchPage(browser, baseUrl, timeout);
  const raw = [], samples = [], firstIgnition = new Map();
  const started = performance.now();
  try {
    const initial = await page.evaluate(({ f, d }) => {
      const r = window.__demo.research; r.setScene(f.points); r.reset(d.seed, d.params); r.camera(d.yaw);
      let lit = 0;
      for (const position of f.sourcePositions) lit += window.__demo.ignite(...position, f.ignitionRadius);
      return { lit, snapshot: r.snapshot({ detail: true }) };
    }, { f, d: definition });
    const expectedSourceCount = f.points.filter(p => p.group === 'source').length;
    if (initial.lit !== expectedSourceCount || initial.snapshot.points.some(p => (p.group === 'source') !== (p.state === 1))) throw new Error('Initial ignition differs from exact authored source patch');
    const capture = s => {
      checkP2Snapshot(s, f); raw.push(s);
      const metrics = measure(s, f, firstIgnition);
      Object.assign(metrics, { particleStateHash: s.particleStateHash, randomDraws: s.randomDraws,
        areaFeed: s.areaFeed, countersByGroup: s.countersByGroup });
      samples.push(metrics);
    };
    capture(initial.snapshot);
    for (let frame = 0; frame < definition.frames;) {
      const n = Math.min(definition.sampleEvery, definition.frames - frame);
      const s = await page.evaluate(({ n, dt }) => {
        window.__demo.research.step(n, dt); return window.__demo.research.snapshot({ detail: true });
      }, { n, dt: definition.dt });
      frame += n; capture(s); onSample?.(frame, definition.frames);
    }
    if (errors.length) throw new Error(`Browser page errors: ${errors.join('\n')}`);
    return { status: 'passed', definition, fixture: f, graphics, effectiveParams: raw[0].params,
      initialIgnited: initial.lit, elapsedWallMilliseconds: performance.now() - started,
      firstIgnition: Object.fromEntries(firstIgnition), firstIgnitionResolution: definition.dt * definition.sampleEvery,
      raw, samples, browserErrors: errors };
  } catch (e) {
    return { status: 'failed', definition, fixture: f, graphics, error: e.stack || String(e),
      elapsedWallMilliseconds: performance.now() - started, raw, samples, browserErrors: errors };
  } finally { await page.close(); }
}

function caseSummary(result) {
  const last = result.samples.at(-1); if (!last) return null;
  const window = result.samples.filter(s => s.time >= 3 - 1e-8 && s.time <= 6 + 1e-8 && s.scene.burning > 0);
  return { finalScene: last.scene, finalParticles: last.particles, counters: last.counters, areaFeed: last.areaFeed,
    targetIgnitedAreaFraction: last.groups.target.ignitedFraction,
    sourceArea: result.fixture.groupAreas.source, targetArea: result.fixture.groupAreas.target,
    hotCoverage3to6ConditionalBurning: window.length ? window.filter(s => s.particles.hotCount > 0).length / window.length : null,
    hotCheckpoints3to6: window.map(s => ({ time: s.time, hotCount: s.particles.hotCount, burning: s.scene.burning })),
    interpretation: 'Authored-area implementation diagnostics; weighted heat/fuel and particle counts are not calibrated physical energy or visual quality.' };
}

export async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) { console.log('node research/p2-run.mjs --suite all|quick|graph-duplicates|refinement|feedback [--seeds 11,23,47] [--out DIR] [--browser-executable PATH]\nAlso --frames/--seconds, --dt, --sample-every, --config; time overrides are labelled custom, policy parameters frozen.'); return; }
  const config = args.config ? JSON.parse(await fs.readFile(args.config, 'utf8')) : {};
  const cases = configureP2(args, config), out = path.resolve(args.out || path.join(researchRoot, 'runs', `p2-${Date.now()}`));
  await fs.mkdir(out, { recursive: true });
  const manifestPath = path.join(out, 'manifest.json');
  try { await fs.access(manifestPath); throw new Error(`Output manifest exists: ${out}`); }
  catch (e) { if (e.code !== 'ENOENT') throw e; }
  const manifest = { version: 1, phase: 'P2', status: 'running', metadata: hostMetadata(), args, config,
    protocol: args.config || args.frames || args.seconds || args.dt || args.sampleEvery ? 'custom-overrides-recorded' : 'fixed-P2-synthetic-diagnostic',
    plannedCases: cases, results: [], comparisons: [], refinementComparisons: [],
    warning: 'Execution success does not imply the duplicate or convergence hypothesis passed. No visual-quality, physical-energy or GPU-benchmark claim.' };
  const save = () => fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2));
  let server, launched;
  await save();
  try {
    server = await startServer(); launched = await launchBrowser(args.browserExecutable);
    manifest.browser = { version: launched.browser.version(), module: launched.module, launchOptions: launched.launchOptions };
    for (let i = 0; i < cases.length; i++) {
      const c = cases[i]; console.log(`[${i + 1}/${cases.length}] ${c.id}: ${c.frames} frames`);
      let result, lastProgress = Date.now();
      try { result = await runP2Case(launched.browser, server.url, c, args.timeout, (frame, total) => {
        if (Date.now() - lastProgress > 15000) { console.log(`  ${frame}/${total} frames`); lastProgress = Date.now(); }
      }); }
      catch (e) { result = { status: 'failed', definition: c, error: e.stack || String(e), raw: [], samples: [] }; }
      await fs.writeFile(path.join(out, `${c.id}.json`), JSON.stringify(result));
      if (result.samples.length) await fs.writeFile(path.join(out, `${c.id}.csv`), timeseriesCsv(result.samples));
      manifest.results.push({ id: c.id, family: c.family, status: result.status, rawFile: `${c.id}.json`,
        csvFile: result.samples.length ? `${c.id}.csv` : null, summary: result.status === 'passed' ? caseSummary(result) : null,
        error: result.error || null });
      console.log(`  ${result.status}${result.error ? `: ${result.error}` : `; target area ignited=${result.samples.at(-1).groups.target.ignitedFraction}`}`);
      await save();
    }
    // Read only one candidate/reference at a time to keep fine-grid raw trajectories off the live heap.
    for (const row of manifest.results.filter(r => r.status === 'passed')) {
      const d = cases.find(c => c.id === row.id);
      const referenceDef = cases.find(c => c.family === d.family && c.variant === 'base' && c.order === 'forward'
        && c.params.spreadMeasureMode === d.params.spreadMeasureMode && c.seed === d.seed);
      const referenceRow = manifest.results.find(r => r.id === referenceDef?.id && r.status === 'passed');
      if (!referenceRow) { row.comparisonUnavailable = 'Baseline case missing or failed'; continue; }
      const result = JSON.parse(await fs.readFile(path.join(out, row.rawFile), 'utf8'));
      const reference = row.id === referenceRow.id ? result : JSON.parse(await fs.readFile(path.join(out, referenceRow.rawFile), 'utf8'));
      manifest.comparisons.push(compareP2(result, reference));
      if (d.family === 'refinement') {
        const finestDef = cases.find(c => c.family === 'refinement' && c.variant === 'refine5' && c.params.spreadMeasureMode === d.params.spreadMeasureMode && c.seed === d.seed);
        const finestRow = manifest.results.find(r => r.id === finestDef?.id && r.status === 'passed');
        if (finestRow) {
          const finest = row.id === finestRow.id ? result : JSON.parse(await fs.readFile(path.join(out, finestRow.rawFile), 'utf8'));
          manifest.refinementComparisons.push({ candidate: row.id, ...refinementCurveError(result, finest) });
        } else row.refinementComparisonUnavailable = 'Finest grid omitted or failed';
      }
    }
    manifest.status = manifest.results.some(r => r.status !== 'passed') ? 'failed' : 'passed';
  } catch (e) { manifest.status = 'failed'; manifest.error = e.stack || String(e); console.error(manifest.error); }
  finally {
    await launched?.browser.close(); await server?.close();
    manifest.completed = new Date().toISOString(); await save();
  }
  console.log(`P2 results: ${out}`); if (manifest.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
