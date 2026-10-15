import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from './lib/design.mjs';
import { timeseriesCsv } from './lib/metrics.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { runCase } from './run.mjs';
import { configureP1, p1Metrics } from './p1-design.mjs';

export async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log('P1 implementation diagnostics. node research/p1-run.mjs --suite all|quick|clock|lifetime|combined [--seeds 11,23,47] [--out DIR] [--browser-executable PATH]\nDuration flags --frames/--seconds, --dt, --sample-every and JSON --config are recorded as custom; parameters are frozen.');
    return;
  }
  const config = args.config ? JSON.parse(await fs.readFile(args.config, 'utf8')) : {};
  const cases = configureP1(args, config);
  const out = path.resolve(args.out || path.join(researchRoot, 'runs', `p1-${Date.now()}`));
  await fs.mkdir(out, { recursive: true });
  const manifestPath = path.join(out, 'manifest.json');
  try { await fs.access(manifestPath); throw new Error(`Output manifest exists: ${out}`); }
  catch (e) { if (e.code !== 'ENOENT') throw e; }
  const manifest = { version: 1, phase: 'P1', status: 'running', metadata: hostMetadata(), args, config,
    protocol: args.config || args.frames || args.seconds || args.dt || args.sampleEvery ? 'custom-overrides-recorded' : 'fixed-P1-synthetic-diagnostic',
    plannedCases: cases, results: [],
    warning: 'These are controlled implementation comparisons, insufficient alone for physical validity or visual quality. Recycling changes later shared RNG consumption.' };
  const save = () => fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2));
  let server, launched;
  await save();
  try {
    server = await startServer(); launched = await launchBrowser(args.browserExecutable);
    manifest.browser = { version: launched.browser.version(), module: launched.module, launchOptions: launched.launchOptions };
    for (let i = 0; i < cases.length; i++) {
      const c = cases[i]; console.log(`[${i + 1}/${cases.length}] ${c.id}: ${c.frames} frames`);
      let result, lastProgress = Date.now();
      try {
        result = await runCase(launched.browser, server.url, c, args.timeout, (frame, total) => {
          if (Date.now() - lastProgress > 15000) { console.log(`  ${frame}/${total} frames`); lastProgress = Date.now(); }
        });
      } catch (e) { result = { status: 'failed', definition: c, error: e.stack || String(e), samples: [], raw: [] }; }
      if (result.status === 'passed') result.p1Metrics = p1Metrics(result);
      await fs.writeFile(path.join(out, `${c.id}.json`), JSON.stringify(result));
      if (result.samples.length) await fs.writeFile(path.join(out, `${c.id}.csv`), timeseriesCsv(result.samples));
      manifest.results.push({ id: c.id, family: c.family, status: result.status,
        rawFile: `${c.id}.json`, csvFile: result.samples.length ? `${c.id}.csv` : null,
        metrics: result.p1Metrics || null, error: result.error || null });
      console.log(`  ${result.status}${result.error ? `: ${result.error}` : `; target=${result.p1Metrics.targetIgnited}/${result.p1Metrics.targetCount}; recycled=${result.p1Metrics.sceneSeedsRecycled}`}`);
      await save();
    }
    manifest.status = manifest.results.some(r => r.status !== 'passed') ? 'failed' : 'passed';
  } catch (e) { manifest.status = 'failed'; manifest.error = e.stack || String(e); console.error(manifest.error); }
  finally {
    await launched?.browser.close(); await server?.close();
    manifest.completed = new Date().toISOString(); await save();
  }
  console.log(`P1 results: ${out}`);
  if (manifest.status !== 'passed') process.exitCode = 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
}
