import fs from 'node:fs/promises';
import path from 'node:path';
import { BASE_PARAMS } from './lib/design.mjs';
import { fixture } from './lib/fixtures.mjs';
import { startServer, launchBrowser, openResearchPage, hostMetadata, researchRoot } from './lib/runtime.mjs';

// Fixed illustrative views. Rendered differences are not perceptual-quality scores.
const out = path.resolve(process.argv[2] || path.join(researchRoot, 'runs', `p1-capture-${Date.now()}`));
await fs.mkdir(out, { recursive: true });
const manifestPath = path.join(out, 'captures.json');
try { await fs.access(manifestPath); throw new Error('Capture output already exists; use a new directory'); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
const metadata = { status: 'running', source: hostMetadata(), seed: 11, times: [1, 3, 6, 8],
  viewport: { width: 800, height: 600 }, camera: { yaw: 0, camDist: 2.8 },
  interpretation: 'Illustrative same-camera renders; neither image similarity nor appearance preference is measured.', captures: [] };
let server, launched;
try {
  server = await startServer(); launched = await launchBrowser();
  metadata.browser = { version: launched.browser.version(), launchOptions: launched.launchOptions };
  for (const policy of ['block', 'recycle-cold']) {
    const session = await openResearchPage(launched.browser, server.url);
    try {
      await session.page.setViewportSize(metadata.viewport);
      const f = fixture('raised-target');
      const params = { ...BASE_PARAMS, spreadClockMode: 'legacy', spreadParticlePolicy: policy,
        spreadRecycleMinAge: .5, camDist: metadata.camera.camDist };
      await session.page.evaluate(({ f, params }) => {
        const d = window.__demo; d.forceSize(800, 600);
        d.research.setScene(f.points); d.research.reset(11, params); d.research.camera(0);
        d.ignite(...f.ignition.position, f.ignition.radius);
      }, { f, params });
      let previous = 0;
      for (const time of metadata.times) {
        const snapshot = await session.page.evaluate(n => {
          const d = window.__demo; d.research.step(n, 1 / 60);
          d.render(); d.gl.finish();
          const glError = d.gl.getError();
          if (glError) throw new Error('WebGL error ' + glError);
          return d.research.snapshot({ detail: true });
        }, Math.round((time - previous) * 60));
        const filename = `${policy}-${time}s.png`;
        await session.page.locator('#cv').screenshot({ path: path.join(out, filename) });
        metadata.captures.push({ policy, requestedTime: time, filename, graphics: session.graphics, snapshot });
        console.log(filename);
        previous = time;
      }
      if (session.errors.length) throw new Error(session.errors.join('\n'));
    } finally { await session.page.close(); }
  }
  metadata.status = 'passed';
} catch (error) {
  metadata.status = 'failed'; metadata.error = error.stack || String(error); process.exitCode = 1;
} finally {
  await launched?.browser.close(); await server?.close();
  await fs.writeFile(manifestPath, JSON.stringify(metadata, null, 2));
}
