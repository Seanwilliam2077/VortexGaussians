// Byte assembly only: this script never loads a browser or runs a simulation.
import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const originalURL = new URL('../../../../demo/index.html', import.meta.url);
const bridgeURL = new URL('./fire-bridge.js', import.meta.url);
const outputURL = new URL('./source.generated.html', import.meta.url);
const expectedSha256 = 'e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0';
const require = (condition, message) => { if (!condition) throw new Error('A52 assembly: ' + message); };
const input = await readFile(originalURL);
const sourceSha256 = createHash('sha256').update(input).digest('hex');
require(sourceSha256 === expectedSha256, 'original demo source identity differs');
const bridge = await readFile(bridgeURL), bridgeText = bridge.toString('utf8');
require(bridge.length && Buffer.from(bridgeText).equals(bridge), 'bridge is not valid UTF-8');
require(!bridgeText.startsWith('\uFEFF') && !/<\/script/i.test(bridgeText), 'unsafe bridge text');
const anchor = Buffer.from('window.__demo = {'), position = input.indexOf(anchor);
require(position >= 0 && input.indexOf(anchor, position + anchor.length) < 0, 'anchor is not unique');
const begin = Buffer.from('\n/* A52 FIRE BRIDGE BEGIN: fire-bridge.js */\n');
const end = Buffer.from('\n/* A52 FIRE BRIDGE END */\n');
require(!input.includes(begin) && !input.includes(end), 'original contains insertion markers');
const insertion = Buffer.concat([begin, bridge, end]);
const output = Buffer.concat([input.subarray(0, position), insertion, input.subarray(position)]);
require(Buffer.concat([output.subarray(0, position), output.subarray(position + insertion.length)]).equals(input),
  'source does not reconstruct exactly after removing inserted bridge');
// A derived build artifact can be replaced; the only source write is this URL.
await writeFile(outputURL, output);
console.log(JSON.stringify({ source: 'demo/index.html', sourceSha256, sourceBytes: input.length,
  output: 'source.generated.html', outputBytes: output.length, pureInsertion: true,
  originalBytesReconstructExactly: true, simulationExecuted: false }, null, 2));
