// UI-only check for the reset receipt. No __demo calls, no fabricated audience record.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { startServer, launchBrowser, repoRoot } from '../../research/lib/runtime.mjs';

const out = path.resolve(process.argv[2] || 'tracks/art/checks/reset-receipt-20261027');
await fs.mkdir(path.dirname(out), { recursive: true });
await fs.mkdir(out, { recursive: false });
const names = ['tracks/art/index.html', 'tracks/art/art.js', 'tracks/art/art.css', 'tracks/art/receipt-ui.mjs', 'demo/index.html', 'static/test_scene.ply'];
const hashes = async () => Object.fromEntries(await Promise.all(names.map(async name => [name,
  createHash('sha256').update(await fs.readFile(path.join(repoRoot, name))).digest('hex')])));
const result = { createdAt: new Date().toISOString(), scope: 'UI-only synthetic prototype validation; no audience, art-quality, physical or performance conclusion', checks: [], errors: [], sourceBefore: await hashes() };
const server = await startServer();
let browser, page;
const check = (name, details = {}) => result.checks.push({ name, passed: true, ...details });
const read = async () => ({ time: await page.locator('#time-label').innerText(), burning: await page.locator('#burning-count').innerText(),
  charred: await page.locator('#char-count').innerText(), run: await page.locator('#run-count').innerText() });
const waitText = async (selector, text) => {
  const end = Date.now() + 30000;
  while (Date.now() < end) {
    if ((await page.locator(selector).innerText()).includes(text)) return;
    await page.waitForTimeout(100);
  }
  throw new Error(`Timeout waiting for ${selector}: ${text}`);
};
try {
  ({ browser } = await launchBrowser());
  result.browser = browser.version();
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
  page = await context.newPage(); page.setDefaultTimeout(30000);
  page.on('pageerror', error => result.errors.push(error.message));
  await page.goto(`${server.url}/tracks/art/`);
  assert.equal(await page.locator('#receipt-empty').isVisible(), true);
  assert.equal(await page.locator('#receipt-toggle').isVisible(), false);
  check('no fabricated receipt before scene or reset');
  await page.locator('#start-example').click(); await waitText('#status', '45,808 / 45,808');
  assert.equal(await page.locator('#receipt-toggle').isVisible(), false);
  check('scene load does not count as author reset');
  await page.locator('[data-stage=intervene]').click(); await page.locator('#ignite').click();
  await page.locator('#advance').click(); await waitText('#status', '本段推进完成');
  const before = await read(); assert.equal(before.time, '模拟时间 1.00 s');
  assert.ok(Number(before.burning.replaceAll(',', '')) > 0);
  await page.locator('[data-stage=revisit]').click(); await page.locator('#reset').click();
  const after = await read(); assert.equal(after.time, '模拟时间 0.00 s');
  assert.equal(after.burning, '0'); assert.equal(after.charred, '0');
  assert.equal(await page.locator('#receipt-time').innerText(), '1.00 s');
  assert.equal(await page.locator('#receipt-burning').innerText(), before.burning);
  assert.equal(await page.locator('#receipt-charred').innerText(), before.charred);
  check('reset receipt matches prior visible state while current counters reset', { before, after });
  await page.locator('#receipt-toggle').click(); assert.equal(await page.locator('#receipt-content').isVisible(), false);
  assert.equal(await page.locator('#receipt-toggle').getAttribute('aria-expanded'), 'false');
  assert.deepEqual(await read(), after);
  await page.locator('#receipt-toggle').click(); assert.equal(await page.locator('#receipt-content').isVisible(), true);
  assert.deepEqual(await read(), after);
  assert.equal(await page.locator('#receipt-burning').innerText(), before.burning);
  await page.locator('.reset-receipt').screenshot({ path: path.join(out, 'receipt-wide.png') });
  check('hide and reopen only changes presentation');
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await page.locator('.reset-receipt').screenshot({ path: path.join(out, 'receipt-narrow.png') });
  check('390px receipt has no horizontal page overflow');
  await page.locator('#receipt-toggle').click();
  const pendingDownload = page.waitForEvent('download'); await page.locator('#export').click();
  const download = await pendingDownload; const exported = path.join(out, 'journal.json'); await download.saveAs(exported);
  const journal = JSON.parse(await fs.readFile(exported, 'utf8'));
  const resets = journal.events.filter(e => e.type === 'reinitialize' && e.reason === '作者选择重新开始');
  assert.equal(resets.length, 1); assert.equal(resets[0].previous.simulatedSeconds, 1);
  assert.equal(resets[0].previous.counts.burning, Number(before.burning.replaceAll(',', '')));
  assert.equal(journal.resetReceiptVisible, false); assert.equal(journal.notes.length, 0);
  assert.equal(journal.events.filter(e => e.type === 'receipt-visibility').length, 3);
  check('actual JSON download retains reset snapshot and presentation choices, no invented notes');
  await page.reload();
  assert.equal(await page.locator('#demo-frame').getAttribute('src'), 'about:blank');
  assert.equal(await page.locator('#receipt-toggle').isVisible(), true);
  assert.equal(await page.locator('#receipt-content').isVisible(), false);
  await page.locator('#receipt-toggle').click();
  assert.equal(await page.locator('#receipt-time').innerText(), '1.00 s');
  assert.equal(await page.locator('#receipt-burning').innerText(), before.burning);
  assert.equal(await page.locator('#scene-count').innerText(), '—');
  check('refresh retains receipt and hidden choice but never restores simulation');
  assert.deepEqual(result.errors, []); check('no page errors');
  result.status = 'completed';
} catch (error) {
  result.status = 'failed'; result.failure = { message: error.message, stack: error.stack }; process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  await server.close();
  result.sourceAfter = await hashes(); result.sourcesUnchanged = JSON.stringify(result.sourceBefore) === JSON.stringify(result.sourceAfter);
  if (!result.sourcesUnchanged) { result.status = 'failed'; process.exitCode = 1; }
  await fs.writeFile(path.join(out, 'result.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify({ status: result.status, checks: result.checks.length, errors: result.errors, sourcesUnchanged: result.sourcesUnchanged, out }));
}
