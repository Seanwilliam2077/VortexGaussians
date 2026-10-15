import test from 'node:test';
import assert from 'node:assert/strict';
import { P3, qualityCases, timingCases, p3Config, parseP3Args } from '../p3-design.mjs';
import { imageError, poolErrors, referenceGate, encodeFloat32, decodeFloat32, distribution } from '../lib/p3-metrics.mjs';
import { compareP3Quality, validateP3Snapshot } from '../p3-run.mjs';
import { checkSourceHashes, requireSamePhysics } from '../lib/p3-runtime.mjs';
const img = (data, width = data.length / 4) => ({ width, height: 1, data, orientation: 'bottom-left' });

test('P3 main matrix separates physical and independent render/reference RNGs', () => {
  const cases = qualityCases(); assert.equal(cases.length, 48);
  assert.equal(cases.filter(c => c.family === 'shared').length, 3);
  assert.equal(new Set(cases.map(c => c.id)).size, cases.length);
  for (const c of cases) { assert.equal(p3Config(c).nSim, 600); assert.equal(p3Config(c).params.rate, 180); }
  const streams = [...P3.renderSeeds, ...P3.referenceSeeds, ...P3.doubleReferenceSeeds];
  assert.equal(new Set(streams).size, 9); assert.equal(qualityCases('quick').length, 6);
  assert.throws(() => parseP3Args(['--n-sim', '1200']), /Unknown/);
  assert.throws(() => qualityCases('invalid'), /Unknown/);
});

test('timing uses independent resets and balanced positions with GPU completion configured', () => {
  const cases = timingCases(); assert.equal(cases.length, 25); assert.equal(P3.timing.sync, 'finish');
  for (let position = 0; position < 5; position++) assert.equal(new Set([0, 1, 2, 3, 4].map(r => `${cases[r * 5 + position].mode}:${cases[r * 5 + position].nRender}`)).size, 5);
});

test('pixel errors retain dark-background dilution and fixed-reference foreground separately', () => {
  const a = img([0, 0, 0, 0, 0, 0, 0, 0]);
  const b = img([1, 2, 3, .5, 0, 0, 0, 0]);
  const e = imageError(a, b);
  assert.equal(e.full.pixels, 2); assert.equal(e.foreground.pixels, 1);
  assert.equal(e.full.rgbSquaredError, 14); assert.equal(e.foreground.alphaRmse, .5);
  assert.equal(e.holes.fraction, 1); assert.equal(e.holes.denominator, 1);
  const pooled = poolErrors([e, e]); assert.equal(pooled.full.pixels, 4); assert.equal(pooled.full.rgbRmse, e.full.rgbRmse);
});

test('empty ROI and zero signal cannot pass a convergence gate', () => {
  const zero = imageError(img([0, 0, 0, 0]), img([0, 0, 0, 0]));
  assert.equal(zero.foreground.rgbRmse, null); assert.equal(referenceGate(zero, zero).passed, false);
  const low = imageError(img([0, 0, 0, 0]), img([1, 1, 1, 1]));
  const good = imageError(img([.9, .9, .9, .9]), img([1, 1, 1, 1]));
  assert.equal(referenceGate(low, good).passed, true);
  const badAlpha = imageError(img([.9, .9, .9, .5]), img([1, 1, 1, 1]));
  assert.equal(referenceGate(low, badAlpha).passed, false);
});

test('raw floating RGBA round-trips with dimensions, orientation and checksum checks', () => {
  const image = img([.125, 2, -1, .5]); const encoded = encodeFloat32(image);
  assert.deepEqual([...decodeFloat32(encoded.bytes, encoded).data], image.data);
  const corrupt = Buffer.from(encoded.bytes); corrupt[0] ^= 1;
  assert.throws(() => decodeFloat32(corrupt, encoded), /checksum/);
  assert.throws(() => decodeFloat32(encoded.bytes.subarray(1), encoded), /length/);
  assert.throws(() => imageError(image, { ...image, orientation: 'top-left' }), /orientations/);
  assert.throws(() => imageError(img([NaN, 0, 0, 0]), image), /Nonfinite/);
});

test('timing distributions reject nonfinite or missing values rather than fabricate zero', () => {
  assert.throws(() => distribution([]), /Invalid/); assert.throws(() => distribution([NaN]), /Invalid/);
  assert.deepEqual(distribution([3, 1, 2]), { count: 3, minimum: 1, median: 2, p90: 2, p95: 2, maximum: 3, mean: 2 });
});

test('missing reference cases remain explicit failures, never partial reference acceptance', async () => {
  const results = qualityCases('pilot').map(definition => ({ definition, status: 'failed' }));
  const result = await compareP3Quality('.', results);
  assert.equal(result.referenceAccepted, false); assert.equal(result.referenceGates.length, 1);
  assert.equal(result.referenceGates[0].passed, false); assert.match(result.referenceGates[0].reason, /incomplete/);
});

test('physics/hash provenance mismatches are visible failures', () => {
  assert.throws(() => requireSamePhysics(['a', 'b'], ['a', 'c'], 'candidate'), /step 1/);
  assert.throws(() => checkSourceHashes({ a: 'old' }, { a: 'new' }), /changed/);
  assert.throws(() => validateP3Snapshot({ physicalHash: 'x', tracerHash: 'y', precision: 'rgba16f' }), /RGBA32F/);
});
