import http from 'node:http';
import fs from 'node:fs/promises';
import { readFileSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
import os from 'node:os';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

export const repoRoot = fileURLToPath(new URL('../../', import.meta.url));
export const researchRoot = fileURLToPath(new URL('../', import.meta.url));
const require = createRequire(import.meta.url);

export async function startServer(root = repoRoot) {
  const mime = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png' };
  const server = http.createServer(async (req, res) => {
    try {
      const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
      let target = path.resolve(root, `.${pathname}`);
      const relative = path.relative(root, target);
      if (relative.startsWith('..') || path.isAbsolute(relative)) { res.writeHead(403); res.end(); return; }
      const stat = await fs.stat(target);
      if (stat.isDirectory()) target = path.join(target, 'index.html');
      const body = await fs.readFile(target);
      res.writeHead(200, { 'Content-Type': mime[path.extname(target)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
      res.end(body);
    } catch (error) { res.writeHead(error.code === 'ENOENT' ? 404 : 500); res.end('Unavailable'); }
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  return { url: `http://127.0.0.1:${server.address().port}`, close: () => new Promise((resolve, reject) => server.close(e => e ? reject(e) : resolve())) };
}

export async function launchBrowser(executable) {
  const candidates = [process.env.PLAYWRIGHT_MODULE,
    process.env.PLAYWRIGHT_MODULE_ROOT && path.join(process.env.PLAYWRIGHT_MODULE_ROOT, 'playwright'),
    'playwright', 'playwright-core'].filter(Boolean);
  let playwright, source; const failures = [];
  for (const candidate of candidates) {
    try { playwright = require(candidate); source = candidate; break; }
    catch (e) { failures.push(`${candidate}: ${e.code || e.message}`); }
  }
  if (!playwright) throw new Error(`Playwright not found. Run npm install in research/, or set PLAYWRIGHT_MODULE to the installed module. ${failures.join('; ')}`);
  const executablePath = executable || process.env.BROWSER_EXECUTABLE;
  const attempts = executablePath ? [{ executablePath }] : [{}, { channel: 'msedge' }, { channel: 'chrome' }];
  for (const options of attempts) {
    try {
      const browser = await playwright.chromium.launch({ headless: true, ...options });
      return { browser, module: source, launchOptions: { headless: true, ...options } };
    } catch (e) { failures.push(`${JSON.stringify(options)}: ${e.message}`); }
  }
  throw new Error(`Browser launch failed. Set --browser-executable / BROWSER_EXECUTABLE, or run npx playwright install chromium in research/. ${failures.join('; ')}`);
}

export async function openResearchPage(browser, baseUrl, timeout = 120000) {
  const page = await browser.newPage({ viewport: { width: 480, height: 360 } });
  page.setDefaultTimeout(timeout);
  const errors = [];
  page.on('pageerror', e => errors.push(e.stack || e.message));
  try {
    await page.goto(`${baseUrl}/demo/?embed=1&orbit=0`, { waitUntil: 'load' });
    await page.waitForFunction(() => window.__demo?.research?.snapshot);
    await page.evaluate(() => { window.__demo.P.paused = true; window.__demo.forceSize(480, 360); });
    const graphics = await page.evaluate(() => {
      const gl = window.__demo.gl, ext = gl.getExtension('WEBGL_debug_renderer_info');
      return { userAgent: navigator.userAgent, webglVersion: gl.getParameter(gl.VERSION),
        renderer: gl.getParameter(ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER),
        vendor: gl.getParameter(ext ? ext.UNMASKED_VENDOR_WEBGL : gl.VENDOR) };
    });
    return { page, errors, graphics };
  } catch (e) { await page.close(); throw e; }
}

export function hostMetadata() {
  let gitSha = null, gitStatus = null, gitError = null;
  try {
    gitSha = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repoRoot, encoding: 'utf8' }).trim();
    gitStatus = execFileSync('git', ['status', '--porcelain'], { cwd: repoRoot, encoding: 'utf8' }).trim();
  } catch (e) { gitError = e.message; }
  const sourceHashes = {};
  const visit = directory => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      if (['runs', 'node_modules', '.git'].includes(entry.name)) continue;
      const name = path.join(directory, entry.name);
      if (entry.isDirectory()) visit(name);
      else if (/\.(mjs|json|md)$/.test(entry.name)) sourceHashes[path.relative(repoRoot, name).replaceAll('\\', '/')] = createHash('sha256').update(readFileSync(name)).digest('hex');
    }
  };
  visit(researchRoot);
  sourceHashes['demo/index.html'] = createHash('sha256').update(readFileSync(path.join(repoRoot, 'demo/index.html'))).digest('hex');
  return { timestamp: new Date().toISOString(), gitSha, gitStatus, gitError, sourceHashes,
    node: process.version, platform: process.platform, architecture: process.arch, release: os.release(),
    cpuModel: os.cpus()[0]?.model || null, logicalCpuCount: os.cpus().length,
    interpretation: 'Synthetic evidence of implementation behavior; insufficient alone for physical validity or SIGGRAPH readiness. Wall-clock durations are harness observations, not GPU benchmarks.' };
}
