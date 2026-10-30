import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { startServer, launchBrowser, repoRoot } from '../../../../research/lib/runtime.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const mode = process.argv.includes('--preview') ? 'preview' : process.argv.includes('--film') ? 'film' : null;
const outName = process.argv[process.argv.indexOf('--out') + 1];
if (!mode || !process.argv.includes('--execute')) {
  console.log('A52: --preview|--film --out UNIQUE-NAME --execute. Preview <=180s/12 native frames; film <=900s/2880 streamed frames. No automatic retry.');
  process.exit(0);
}
if (!process.argv.includes('--out') || !/^[a-z0-9][a-z0-9-]{0,40}$/.test(outName || '')) throw Error('Explicit safe unique output name required');
const out = path.join(here, outName);
await fs.mkdir(out, { recursive: false });
const started = performance.now(), wall = () => (performance.now() - started) / 1000;
const limit = mode === 'preview' ? 180 : 900;
const targets = [0, 12, 24, 34, 44, 50, 60, 72, 84, 94, 104, 120];
const FPS = 24, COUNT = 2880;
const ffmpeg = process.env.FFMPEG_EXECUTABLE || 'C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/Library/bin/ffmpeg.exe';
const ffprobe = path.join(path.dirname(ffmpeg), 'ffprobe.exe');
const sha = b => createHash('sha256').update(b).digest('hex');
const result = { schema: 'a52-production-v1', createdUTC: new Date().toISOString(), mode, status: 'started',
  intended: { width: 1280, height: 720, durationSeconds: 120, fps: FPS, frames: COUNT },
  limitSeconds: limit, framesRendered: 0, PNGBytesTransferred: 0, images: [], checkpoints: [],
  sourceIdentities: {}, pageErrors: [], console: [], externalRequests: [], childRuns: [], cleanup: {},
  observation: 'Offline frame rendering and media validity only. No human or continuous agent viewing, audience effect, contribution or score is inferred.' };
let server, browser, context, page, expired = false, timer;
const children = new Set(), pendingChildren = new Set();
const failIfExpired = () => { if (expired || wall() > limit) throw Error('Finite production deadline exceeded'); };
const sources = ['BRIEF.md', 'scene.mjs', 'work.mjs', 'work.css', 'index.html', 'fire-source.mjs', 'fire-bridge.js',
  'assemble-source.mjs', 'source.generated.html', 'produce.mjs'].map(x => path.join(here, x))
  .concat([path.join(repoRoot, 'demo/index.html'), path.join(repoRoot, 'research/lib/runtime.mjs')]);
function child(executable, args) {
  const at = wall(), p = spawn(executable, args, { windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
  children.add(p);
  let stdout = '', stderr = '';
  p.stdout.on('data', b => { stdout = (stdout + b.toString()).slice(-65536); });
  p.stderr.on('data', b => { stderr = (stderr + b.toString()).slice(-16384); });
  const done = new Promise((resolve, reject) => {
    p.once('error', e => { children.delete(p); reject(e); });
    p.once('close', (code, signal) => {
      children.delete(p);
      const record = { executable, args, code, signal, wallSeconds: wall() - at, stdout, stderr };
      result.childRuns.push(record);
      code === 0 ? resolve(record) : reject(Object.assign(Error('Child process failed: ' + code + ' ' + stderr), { record }));
    });
  });
  pendingChildren.add(done);
  done.then(() => pendingChildren.delete(done), () => pendingChildren.delete(done));
  done.catch(() => {});
  p.stdin.on('error', () => {});
  return { p, done };
}
async function bounded(action, milliseconds) {
  let timeout;
  try {
    return await Promise.race([Promise.resolve().then(action), new Promise((_, reject) => {
      timeout = setTimeout(() => reject(Error('Cleanup deadline exceeded')), milliseconds);
    })]);
  } finally { clearTimeout(timeout); }
}
async function runChild(executable, args) {
  failIfExpired(); const c = child(executable, args); c.p.stdin.end(); return c.done;
}
async function writeFrame(p, data) {
  await new Promise((resolve, reject) => p.stdin.write(data, e => e ? reject(e) : resolve()));
}
async function frame(seconds) {
  failIfExpired();
  const item = await page.evaluate(t => {
    const before = performance.now();
    const state = window.__a52.renderAt(t);
    const renderingMs = performance.now() - before;
    const encodeStart = performance.now();
    const data = document.querySelector('#view').toDataURL('image/png');
    return { state, renderingMs, pngMs: performance.now() - encodeStart, data };
  }, seconds);
  if (!item.data.startsWith('data:image/png;base64,')) throw Error('Unexpected canvas export');
  const data = Buffer.from(item.data.slice(22), 'base64');
  if (!data.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))
    || data.readUInt32BE(16) !== 1280 || data.readUInt32BE(20) !== 720) throw Error('Native frame dimensions mismatch');
  result.framesRendered++; result.PNGBytesTransferred += data.length;
  result.renderingMs = (result.renderingMs || 0) + item.renderingMs;
  result.pngEncodingMs = (result.pngEncodingMs || 0) + item.pngMs;
  return { data, state: item.state };
}
try {
  timer = setTimeout(() => {
    expired = true;
    for (const p of children) p.kill();
    if (context) void context.close().catch(() => {});
    if (browser) void browser.close().catch(() => {});
  }, limit * 1000);
  for (const f of sources) {
    const b = await fs.readFile(f);
    result.sourceIdentities[path.relative(repoRoot, f).replaceAll('\\','/')] = { bytes: b.length, sha256: sha(b) };
  }
  const original = result.sourceIdentities['demo/index.html'];
  if (original.sha256 !== 'e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0') throw Error('Original demo identity changed');
  server = await startServer();
  failIfExpired();
  const launch = await launchBrowser(); browser = launch.browser;
  if (expired) throw Error('Deadline during launch');
  context = await browser.newContext({ viewport: { width: 1320, height: 860 }, deviceScaleFactor: 1 });
  if (expired) throw Error('Deadline during context setup');
  await context.route('**/*', async route => {
    const u = new URL(route.request().url());
    if (!['127.0.0.1', 'localhost'].includes(u.hostname)) {
      result.externalRequests.push(u.href); return route.abort();
    }
    return route.continue();
  });
  page = await context.newPage();
  page.on('pageerror', e => result.pageErrors.push(e.message));
  page.on('console', m => { if (['warning','error'].includes(m.type())) result.console.push({ type: m.type(), text: m.text() }); });
  await page.goto(server.url + '/tracks/art/studies/a52-room-facing-away/', { waitUntil: 'load', timeout: 30000 });
  await page.waitForFunction(() => !!window.__a52, null, { timeout: 30000 });
  await page.evaluate(async () => await window.__a52.ready);
  result.initial = await page.evaluate(() => window.__a52.inspect());
  result.preparationWallSeconds = wall();
  if (mode === 'preview') {
    for (let i = 0; i < targets.length; i++) {
      const t = targets[i], item = await frame(t);
      const file = String(i + 1).padStart(2, '0') + '-' + t + 's.png';
      await fs.writeFile(path.join(out, file), item.data, { flag: 'wx' });
      result.images.push({ file, seconds: t, bytes: item.data.length, sha256: sha(item.data), state: item.state });
      console.log(JSON.stringify({ phase: 'preview', seconds: t, elapsedSeconds: wall() }));
    }
  } else {
    const movie = path.join(out, 'room-facing-away.mp4');
    const encoding = child(ffmpeg, ['-hide_banner', '-loglevel', 'error', '-nostdin', '-n',
      '-f', 'image2pipe', '-vcodec', 'png', '-framerate', String(FPS), '-i', 'pipe:0',
      '-an', '-frames:v', String(COUNT), '-c:v', 'libx264', '-preset', 'veryfast',
      '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', movie]);
    for (let i = 0; i < COUNT; i++) {
      const item = await frame(i / FPS);
      await writeFrame(encoding.p, item.data);
      if (i % 120 === 0 || i === COUNT - 1) {
        result.checkpoints.push({ frame: i, seconds: i / FPS, state: item.state, wallSeconds: wall() });
        console.log(JSON.stringify({ phase: 'film', rendered: i + 1, total: COUNT, elapsedSeconds: wall() }));
      }
    }
    encoding.p.stdin.end();
    await encoding.done;
    const probe = await runChild(ffprobe, ['-v', 'error', '-select_streams', 'v:0', '-show_entries',
      'format=duration,size:stream=codec_name,width,height,nb_frames,duration,r_frame_rate', '-of', 'json', movie]);
    const metadata = JSON.parse(probe.stdout), s = metadata.streams[0];
    if (s.width !== 1280 || s.height !== 720 || Number(s.nb_frames) !== COUNT
      || Math.abs(Number(metadata.format.duration) - 120) > 1 / FPS) throw Error('Encoded duration/frame identity mismatch');
    const decoded = await runChild(ffmpeg, ['-hide_banner', '-v', 'error', '-nostdin', '-i', movie,
      '-map', '0:v:0', '-f', 'null', '-', '-progress', 'pipe:1', '-nostats']);
    const frameCounts = [...decoded.stdout.matchAll(/^frame=(\d+)$/gm)].map(m => Number(m[1]));
    if (frameCounts.at(-1) !== COUNT || decoded.stderr.trim()) throw Error('Full decode did not verify all frames without error');
    const b = await fs.readFile(movie);
    result.movie = { file: path.basename(movie), bytes: b.length, sha256: sha(b), metadata,
      allFramesDecoded: true, decodedFrames: frameCounts.at(-1), continuouslyViewed: false };
    const selected = [0, 576, 1056, 1440, 2016, 2496, 2879];
    await fs.mkdir(path.join(out, 'keyframes'));
    await runChild(ffmpeg, ['-hide_banner', '-v', 'error', '-nostdin', '-n', '-i', movie,
      '-vf', 'select=' + selected.map(n => 'eq(n\\,' + n + ')').join('+'), '-fps_mode', 'vfr',
      path.join(out, 'keyframes', '%02d.png')]);
    for (let i = 0; i < selected.length; i++) {
      const file = 'keyframes/' + String(i + 1).padStart(2, '0') + '.png', b = await fs.readFile(path.join(out, file));
      result.images.push({ file, encodedFrame: selected[i], seconds: selected[i] / FPS, bytes: b.length, sha256: sha(b) });
    }
  }
  result.final = await page.evaluate(() => window.__a52.inspect());
  failIfExpired();
  if (result.pageErrors.length || result.externalRequests.length) throw Error('Page error or external request during production');
  result.sourceUnchanged = true;
  for (const f of sources) {
    const name = path.relative(repoRoot, f).replaceAll('\\','/');
    if (sha(await fs.readFile(f)) !== result.sourceIdentities[name].sha256) result.sourceUnchanged = false;
  }
  if (!result.sourceUnchanged) throw Error('Source changed during production');
  result.status = mode === 'preview' ? 'completed_preview' : 'completed_encoded_and_decoded_film';
} catch (e) {
  result.status = 'failed'; result.error = { message: e.message, stack: e.stack }; process.exitCode = 1;
} finally {
  if (page && !page.isClosed()) {
    try { await bounded(() => page.evaluate(() => window.__a52?.dispose()), 2000); result.cleanup.work = true; }
    catch (e) { result.cleanup.workError = e.message; }
  }
  for (const p of children) p.kill();
  await bounded(() => Promise.allSettled([...pendingChildren]), 3000)
    .then(() => result.cleanup.children = children.size === 0, e => result.cleanup.children = e.message);
  result.cleanup.remainingChildPIDs = [...children].map(p => p.pid);
  if (context) await bounded(() => context.close(), 3000).then(() => result.cleanup.context = true, e => result.cleanup.context = e.message);
  if (browser) await bounded(() => browser.close(), 5000).then(() => result.cleanup.browser = true, e => result.cleanup.browser = e.message);
  if (server) await bounded(() => server.close(), 3000).then(() => result.cleanup.server = true, e => result.cleanup.server = e.message);
  clearTimeout(timer);
  result.expired = expired; result.wallSeconds = wall();
  const resourceFailure = ['children', 'context', 'browser', 'server'].some(k => result.cleanup[k] !== undefined && result.cleanup[k] !== true);
  if (expired || result.wallSeconds > limit || resourceFailure || result.cleanup.workError) {
    result.status = 'failed';
    result.error ??= { message: 'Production or cleanup deadline/resource closure failed' };
    process.exitCode = 1;
  }
  result.costScope = 'Wall clock includes initialization, source stepping, rendering, PNG transfer, file writes and, in film mode, encoding/probe/full decode/keyframe extraction/cleanup; final result write itself is not separately timed. JS rendering times are not GPU timings.';
  await fs.writeFile(path.join(out, 'result.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({ status: result.status, wallSeconds: result.wallSeconds, frames: result.framesRendered, images: result.images.length, movieBytes: result.movie?.bytes, cleanup: result.cleanup, error: result.error?.message }));
}
