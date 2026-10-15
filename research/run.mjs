import fs from 'node:fs/promises';
import path from 'node:path';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';
import { parseArgs, configureCases } from './lib/design.mjs';
import { fixture, graphDescription } from './lib/fixtures.mjs';
import { assertSnapshot, measure, classify, timeseriesCsv } from './lib/metrics.mjs';
import { startServer, launchBrowser, openResearchPage, hostMetadata, researchRoot } from './lib/runtime.mjs';

const HELP = `Synthetic P0 research diagnostics (not publication evidence)\nUsage: node run.mjs [--suite quick|feedback|sensitivity|all] [--seeds 11,23,47]\n  [--frames N | --seconds N] [--dt 0.016666666666666666] [--sample-every N]\n  [--config config.json] [--out DIRECTORY] [--browser-executable PATH] [--timeout MS]\nJSON config: {params:{...},seeds:[11],dt:...,frames:...,sampleEvery:...}. Matrix factors cannot be globally overridden.\nBrowser: npm install; npx playwright install chromium; or set PLAYWRIGHT_MODULE and BROWSER_EXECUTABLE.\n`;

export async function runCase(browser, baseUrl, definition, timeout, onSample) {
  const f = fixture(definition.fixture, definition.fixtureOptions);
  f.graph = graphDescription(f.points, definition.params.spreadR);
  if (f.name === 'raised-target') {
    const sources = f.points.filter(p => p.group === 'source'), targets = f.points.filter(p => p.group === 'target');
    f.minimumSourceTargetDistance = Math.min(...sources.flatMap(a => targets.map(b => Math.hypot(...a.position.map((v, k) => v - b.position[k])))));
    f.causalGeometryValid = f.minimumSourceTargetDistance > definition.params.spreadR && f.minimumSourceTargetDistance > definition.params.spreadIgnR;
    if (!f.causalGeometryValid) throw new Error('Raised-target geometry is bridged by the configured graph/initial heat radius; choose a valid diagnostic configuration');
  }
  const { page, errors, graphics } = await openResearchPage(browser, baseUrl, timeout);
  const raw = [], samples = [], firstIgnition = new Map();
  const start = performance.now();
  try {
    const initial = await page.evaluate(({ f, d }) => {
      const r = window.__demo.research;
      r.setScene(f.points); r.reset(d.seed, d.params); r.camera(d.yaw);
      const lit = window.__demo.ignite(...f.ignition.position, f.ignition.radius);
      return { lit, snapshot: r.snapshot({ detail: true }) };
    }, { f, d: definition });
    if (!initial.lit) throw new Error('Fixture initial ignition ignited zero splats');
    const capture = s => { assertSnapshot(s); raw.push(s); samples.push(measure(s, f, firstIgnition)); };
    capture(initial.snapshot);
    for (let frame = 0; frame < definition.frames;) {
      const n = Math.min(definition.sampleEvery, definition.frames - frame);
      const s = await page.evaluate(({ n, dt }) => {
        window.__demo.research.step(n, dt);
        return window.__demo.research.snapshot({ detail: true });
      }, { n, dt: definition.dt });
      frame += n; capture(s);
      onSample?.(frame, definition.frames);
    }
    if (errors.length) throw new Error(`Browser page errors: ${errors.join('\n')}`);
    return { status: 'passed', definition, fixture: f, graphics, initialIgnited: initial.lit,
      effectiveParams: raw[0].params, elapsedWallMilliseconds: performance.now() - start,
      firstIgnition: Object.fromEntries(firstIgnition), firstIgnitionResolution: definition.sampleEvery * definition.dt,
      outcome: classify(samples, f.name), samples, raw, browserErrors: errors };
  } catch (e) {
    return { status: 'failed', definition, fixture: f, graphics, error: e.stack || String(e),
      elapsedWallMilliseconds: performance.now() - start, samples, raw, browserErrors: errors };
  } finally { await page.close(); }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) { console.log(HELP); return; }
  const fileConfig = args.config ? JSON.parse(await fs.readFile(args.config, 'utf8')) : {};
  const cases = configureCases(args, fileConfig);
  for (const c of cases) if (!(c.dt > 0 && Number.isFinite(c.dt) && Number.isInteger(c.frames) && c.frames > 0 && Number.isInteger(c.sampleEvery) && c.sampleEvery > 0)) throw new Error('Invalid configured dt/frames/sampleEvery');
  const out = path.resolve(args.out || path.join(researchRoot, 'runs', new Date().toISOString().replaceAll(':', '-')));
  await fs.mkdir(out, { recursive: true });
  const manifestPath = path.join(out, 'manifest.json');
  try { await fs.access(manifestPath); throw new Error(`Output already contains manifest: ${out}; choose a new --out`); }
  catch (e) { if (e.code !== 'ENOENT') throw e; }
  const manifest = { version: 1, status: 'running', metadata: hostMetadata(), args, fileConfig,
    protocol: args.config || args.frames || args.seconds || args.dt || args.sampleEvery ? 'custom-overrides-recorded' : 'fixed-synthetic-diagnostic',
    plannedCases: cases, results: [] };
  const save = () => fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2));
  await save();
  let server, launched;
  try {
    server = await startServer(); launched = await launchBrowser(args.browserExecutable);
    manifest.browser = { version: launched.browser.version(), module: launched.module, launchOptions: launched.launchOptions };
    for (let index = 0; index < cases.length; index++) {
      const c = cases[index]; console.log(`[${index + 1}/${cases.length}] ${c.id}: ${c.frames} frames @ dt=${c.dt}`);
      let result;
      try { result = await runCase(launched.browser, server.url, c, args.timeout); }
      catch (e) { result = { status: 'failed', definition: c, error: e.stack || String(e), samples: [], raw: [] }; }
      const filename = `${c.id}.json`;
      await fs.writeFile(path.join(out, filename), JSON.stringify(result));
      if (result.samples.length) await fs.writeFile(path.join(out, `${c.id}.csv`), timeseriesCsv(result.samples));
      manifest.results.push({ id: c.id, status: result.status, rawFile: filename,
        csvFile: result.samples.length ? `${c.id}.csv` : null,
        outcome: result.outcome || null, error: result.error || null });
      console.log(`  ${result.status}: ${result.error || JSON.stringify(result.outcome)}`);
      await save();
    }
    manifest.status = manifest.results.some(r => r.status !== 'passed') ? 'failed' : 'passed';
  } catch (e) { manifest.status = 'failed'; manifest.error = e.stack || String(e); console.error(manifest.error); }
  finally {
    await launched?.browser.close(); await server?.close();
    manifest.completed = new Date().toISOString(); await save();
  }
  console.log(`Results: ${out}`);
  if (manifest.status !== 'passed') process.exitCode = 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
}
