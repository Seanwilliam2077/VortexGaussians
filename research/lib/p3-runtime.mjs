import fs from 'node:fs/promises';
import path from 'node:path';
import { P3 } from '../p3-design.mjs';
import { encodeFloat32, imageSummary } from './p3-metrics.mjs';

export async function openP3Page(browser, baseUrl) {
  const page = await browser.newPage({ viewport: { width: P3.width, height: P3.height }, deviceScaleFactor: 1 });
  page.setDefaultTimeout(120000); const errors = [];
  page.on('pageerror', e => errors.push(e.stack || e.message));
  try {
    await page.goto(`${baseUrl}/demo/?embed=1&orbit=0`, { waitUntil: 'load' });
    await page.waitForFunction(() => typeof window.__demo?.researchP3?.reset === 'function');
    const graphics = await page.evaluate(({ width, height }) => {
      const d = window.__demo; d.P.paused = true; d.forceSize(width, height);
      const gl = d.gl, ext = gl.getExtension('WEBGL_debug_renderer_info');
      return { userAgent: navigator.userAgent, webglVersion: gl.getParameter(gl.VERSION),
        renderer: gl.getParameter(ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER),
        vendor: gl.getParameter(ext ? ext.UNMASKED_VENDOR_WEBGL : gl.VENDOR),
        extensions: gl.getSupportedExtensions(), canvas: { width: gl.drawingBufferWidth, height: gl.drawingBufferHeight },
        timingMethod: 'gl.finish synchronized wall-clock latency; not pure GPU time' };
    }, P3);
    return { page, errors, graphics };
  } catch (e) { await page.close(); throw e; }
}

export function assertFiniteTree(value, location = 'snapshot') {
  if (typeof value === 'number' && !Number.isFinite(value)) throw new Error(`Nonfinite ${location}`);
  if (value && typeof value === 'object') for (const [key, v] of Object.entries(value)) assertFiniteTree(v, `${location}.${key}`);
}

export function requireSamePhysics(reference, candidate, label) {
  if (reference.length !== candidate.length) throw new Error(`Physics trajectory length mismatch: ${label}`);
  for (let i = 0; i < reference.length; i++) if (reference[i] !== candidate[i]) throw new Error(`Physics hash changed at step ${i}: ${label}`);
}

export function checkSourceHashes(before, after) {
  const keys = [...new Set([...Object.keys(before), ...Object.keys(after)])];
  const changed = keys.filter(k => before[k] !== after[k]);
  if (changed.length) throw new Error(`Source files changed during measurement: ${changed.join(', ')}`);
  return { matched: true, fileCount: keys.length };
}

export async function saveImage(out, stem, image) {
  const encoded = encodeFloat32(image), { bytes, ...metadata } = encoded;
  await fs.mkdir(path.join(out, 'images'), { recursive: true });
  const filename = `images/${stem}.rgba.f32`;
  await fs.writeFile(path.join(out, filename), bytes);
  const record = { ...metadata, file: filename, summary: imageSummary(image),
    framebufferPrecision: image.precision ?? image.framebufferPrecision ?? null };
  await fs.writeFile(path.join(out, `images/${stem}.json`), JSON.stringify(record, null, 2));
  return record;
}

export function timingCsv(rows) {
  const columns = ['frame', 'time', 'simulationMs', 'tracerMs', 'gatherSortUploadMs', 'drawSubmitMs', 'finishWaitMs', 'totalMs'];
  return `${columns.join(',')}\n${rows.map(r => columns.map(k => r[k] ?? '').join(',')).join('\n')}\n`;
}
