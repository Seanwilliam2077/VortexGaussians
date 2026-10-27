// CPU-only page-shell check. Never loads the WebGL demo or runs the simulator.
// From repository root: node tracks/evidence/checks/html-smoke.cjs
// Optional PLAYWRIGHT_MODULE and BROWSER_EXECUTABLE select installed tools.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '../../..');
const output = path.join(__dirname, 'html.json');
const files = ['tracks/art/index.html', 'tracks/art/art.js', 'tracks/art/art.css'];
const pins = () => Object.fromEntries(files.map(p => [p, crypto.createHash('sha256').update(fs.readFileSync(path.join(root, p))).digest('hex')]));
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' };
const server = http.createServer((req, res) => {
  let rel = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  if (rel.endsWith('/')) rel += 'index.html';
  const target = path.resolve(root, '.' + rel);
  if (!target.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
  try { const data = fs.readFileSync(target); res.setHeader('Content-Type', mime[path.extname(target)] || 'application/octet-stream'); res.end(data); }
  catch { res.writeHead(404).end(); }
});

(async () => {
  assert(!fs.existsSync(output), 'Refuse to overwrite prior smoke output');
  const result = { scope: 'Headless page shell, notes and export only. GPU disabled; no demo, solver, PLY or WebGL execution.', checks: [], sourcesBefore: pins() };
  let browser;
  try {
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    const origin = `http://127.0.0.1:${server.address().port}`;
    const options = { headless: true, args: ['--disable-gpu', '--disable-software-rasterizer'] };
    if (process.env.BROWSER_EXECUTABLE) options.executablePath = process.env.BROWSER_EXECUTABLE;
    else options.channel = 'msedge';
    browser = await chromium.launch(options);
    result.browserVersion = browser.version(); result.launchFlags = options.args;
    const context = await browser.newContext({ acceptDownloads: true });
    const requested = [], errors = [], failures = [];
    await context.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
    const page = await context.newPage();
    page.on('request', r => requested.push(new URL(r.url()).pathname));
    page.on('pageerror', e => errors.push(e.message));
    page.on('response', r => { if (r.status() >= 400) failures.push({ path: new URL(r.url()).pathname, status: r.status() }); });
    await page.goto(origin + '/tracks/art/', { waitUntil: 'networkidle' });
    const check = (name, passed) => { result.checks.push({ name, passed }); assert(passed, name); };
    check('initial_iframe_blank', await page.locator('#demo-frame').getAttribute('src') === 'about:blank');
    check('simulation_controls_disabled', await page.locator('#ignite').isDisabled() && await page.locator('#advance').isDisabled());
    await page.locator('#context').fill('Independent smoke check: synthetic author draft.');
    await page.locator('#choice').fill('No simulation loaded.');
    await page.locator('#observation').fill('<b>literal text, not participant evidence</b>');
    await page.locator('#note-form button[type=submit]').click();
    check('note_saved_as_text', (await page.locator('#notes').innerText()).includes('<b>literal text') && await page.locator('#notes b').count() === 0);
    await page.reload({ waitUntil: 'networkidle' });
    check('note_survives_reload', (await page.locator('#note-count').innerText()).includes('1'));
    await page.locator('[data-stage=intervene]').click();
    check('stage_changes_without_simulation', await page.locator('#panel-intervene').isVisible() && await page.locator('#advance').isDisabled());
    await page.locator('#note-kind').selectOption('audience-observation');
    await page.locator('#choice').fill('Missing real context and observation');
    await page.locator('#note-form button[type=submit]').click();
    check('incomplete_audience_note_rejected', (await page.locator('#note-count').innerText()).includes('1'));
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#export').click();
    const download = await downloadPromise, chunks = [];
    for await (const chunk of await download.createReadStream()) chunks.push(chunk);
    const exported = JSON.parse(Buffer.concat(chunks).toString('utf8'));
    check('export_has_actual_note', exported.notes.length === 1 && exported.notes[0].kind === 'author-draft' && exported.notes[0].audienceEvidenceVerified === false);
    check('export_is_not_checkpoint', exported.currentSnapshot === null && exported.limitations.some(t => t.includes('no asset bytes')));
    check('no_demo_or_asset_request', !requested.some(p => p.startsWith('/demo/') || p.endsWith('.ply')));
    check('no_page_errors_or_failed_assets', errors.length === 0 && failures.length === 0);
    result.export = { schema: exported.schema, notes: exported.notes.length, currentSnapshot: exported.currentSnapshot, hasLimitations: exported.limitations.length > 0 };
    result.requestedPaths = [...new Set(requested)]; result.pageErrors = errors; result.failedResponses = failures;
    result.passed = true;
  } catch (e) { result.passed = false; result.error = String(e.stack || e); }
  finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
    result.sourcesAfter = pins();
    result.sourcesUnchanged = JSON.stringify(result.sourcesBefore) === JSON.stringify(result.sourcesAfter);
    result.passed = result.passed && result.sourcesUnchanged;
    fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
  }
  console.log(JSON.stringify({ passed: result.passed, checks: result.checks.length, error: result.error || null, output: 'tracks/evidence/checks/html.json' }));
  process.exitCode = result.passed ? 0 : 1;
})();
