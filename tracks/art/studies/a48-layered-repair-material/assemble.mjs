// This program only assembles bytes. It never loads or executes the page.
import { readFile, writeFile, access } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const inputURL = new URL('../../../../demo/index.html', import.meta.url);
const outputURL = new URL('./renderer.generated.html', import.meta.url);
const manifestURL = new URL('./assembly.json', import.meta.url);
const sourceHash = 'e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0';
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const require = (ok, message) => { if (!ok) throw Error('A48 assembly: ' + message); };
for (const url of [outputURL, manifestURL]) {
  try { await access(url); throw Error('A48 assembly refuses to overwrite ' + url.pathname); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
}
const input = await readFile(inputURL), bridge = await readFile(new URL('./bridge.js', import.meta.url));
require(input.length === 314044 && hash(input) === sourceHash, 'original source identity differs');
const anchor = Buffer.from('window.__demo = {'), at = input.indexOf(anchor);
require(at >= 0 && input.indexOf(anchor, at + anchor.length) === -1, 'anchor is not unique');
const bridgeText = bridge.toString('utf8');
require(bridge.length > 0 && Buffer.from(bridgeText).equals(bridge), 'bridge must be UTF-8');
require(!bridgeText.startsWith('\uFEFF') && !/<\/script/i.test(bridgeText), 'unsafe bridge wrapper');
const begin = '\n/* A48 LOCAL BRIDGE BEGIN — source: bridge.js */\n';
const end = '\n/* A48 LOCAL BRIDGE END */\n';
require(!input.includes(Buffer.from(begin)) && !input.includes(Buffer.from(end)), 'source already has markers');
const insertion = Buffer.concat([Buffer.from(begin), bridge, Buffer.from(end)]);
const output = Buffer.concat([input.subarray(0, at), insertion, input.subarray(at)]);
require(Buffer.concat([output.subarray(0, at), output.subarray(at + insertion.length)]).equals(input), 'not a pure insertion');
const manifest = {
  version: 1,
  source: { path: '../../../../demo/index.html', bytes: input.length, sha256: hash(input) },
  bridge: { path: './bridge.js', bytes: bridge.length, sha256: hash(bridge) },
  output: { path: './renderer.generated.html', bytes: output.length, sha256: hash(output) },
  insertion: { anchor: anchor.toString(), anchorOccurrences: 1, byteOffset: at, bytes: insertion.length,
    sha256: hash(insertion), beginMarker: begin, endMarker: end,
    insertionOnly: true, originalBytesReconstructExactly: true },
  semantics: 'Only a closure bridge is inserted; original initialization and embed early-return RAF remain intact.'
};
await writeFile(outputURL, output, { flag: 'wx' });
await writeFile(manifestURL, JSON.stringify(manifest, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(manifest, null, 2));
