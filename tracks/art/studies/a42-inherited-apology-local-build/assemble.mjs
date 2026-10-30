// Static local assembly only. Running this file does not load or execute HTML/JS.
import { readFile, writeFile, access } from 'node:fs/promises';
import { createHash } from 'node:crypto';

const INPUT = new URL('../../../../demo/index.html', import.meta.url);
const BRIDGE = new URL('./bridge.js', import.meta.url);
const OUTPUT = new URL('./renderer.generated.html', import.meta.url);
const MANIFEST = new URL('./assembly.json', import.meta.url);
const INPUT_BYTES = 314044;
const INPUT_SHA256 = 'e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0';
const ANCHOR = Buffer.from('window.__demo = {', 'utf8');
const BEGIN = Buffer.from('\n/* A42 LOCAL BRIDGE BEGIN — source: bridge.js */\n', 'utf8');
const END = Buffer.from('\n/* A42 LOCAL BRIDGE END */\n', 'utf8');
const hash = buffer => createHash('sha256').update(buffer).digest('hex');
const assert = (ok, message) => { if (!ok) throw new Error('A42 assembly: ' + message); };
async function absent(url) {
  try { await access(url); }
  catch (error) { if (error.code === 'ENOENT') return; throw error; }
  throw new Error('A42 assembly: refuses to overwrite ' + url.pathname.split('/').at(-1));
}

await absent(OUTPUT);
await absent(MANIFEST);
const input = await readFile(INPUT), bridge = await readFile(BRIDGE);
assert(input.length === INPUT_BYTES, 'original demo byte count differs');
assert(hash(input) === INPUT_SHA256, 'original demo SHA256 differs');
const at = input.indexOf(ANCHOR);
assert(at >= 0 && input.indexOf(ANCHOR, at + ANCHOR.length) === -1, 'anchor must occur exactly once');
assert(bridge.length > 0, 'bridge is empty');
const bridgeText = bridge.toString('utf8');
assert(Buffer.from(bridgeText, 'utf8').equals(bridge), 'bridge is not canonical UTF-8');
assert(!bridgeText.startsWith('\uFEFF'), 'bridge must not have a BOM');
assert(!/<\/script/i.test(bridgeText), 'bridge cannot contain an HTML script terminator');
assert(input.indexOf(BEGIN) === -1 && input.indexOf(END) === -1, 'source already contains assembly markers');
const inserted = Buffer.concat([BEGIN, bridge, END]);
const output = Buffer.concat([input.subarray(0, at), inserted, input.subarray(at)]);
assert(output.subarray(0, at).equals(input.subarray(0, at))
  && output.subarray(at + inserted.length).equals(input.subarray(at)), 'non-insertion source change');
assert(Buffer.concat([output.subarray(0, at), output.subarray(at + inserted.length)]).equals(input),
  'removing the insertion must restore original bytes exactly');
const manifest = {
  version: 1,
  source: { path: '../../../../demo/index.html', bytes: input.length, sha256: hash(input) },
  bridge: { path: './bridge.js', bytes: bridge.length, sha256: hash(bridge) },
  output: { path: './renderer.generated.html', bytes: output.length, sha256: hash(output) },
  insertion: { anchor: ANCHOR.toString('utf8'), anchorOccurrences: 1, byteOffset: at,
    bytes: inserted.length, sha256: hash(inserted),
    beginMarker: BEGIN.toString('utf8'), endMarker: END.toString('utf8'),
    insertionOnly: true, originalBytesReconstructExactly: true },
  semantics: 'Bridge declarations inserted inside the existing IIFE. Normal embed URL and initialization order retained.'
};
// Exclusive writes are deliberate. A partial I/O failure is recorded, never repaired by an automatic rerun.
await writeFile(OUTPUT, output, { flag: 'wx' });
await writeFile(MANIFEST, JSON.stringify(manifest, null, 2) + '\n', { encoding: 'utf8', flag: 'wx' });
console.log(JSON.stringify(manifest, null, 2));
