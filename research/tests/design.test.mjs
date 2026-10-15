import test from 'node:test';
import assert from 'node:assert/strict';
import { parseArgs, buildCases, configureCases } from '../lib/design.mjs';

test('feedback matrix contains all four edges for every seed', () => {
  const cases = buildCases('feedback', [1, 2]); assert.equal(cases.length, 8);
  for (const seed of [1, 2]) {
    const arms = cases.filter(c => c.seed === seed);
    assert.equal(new Set(arms.map(c => `${c.params.spreadFlameHeat}/${c.params.spreadSceneFeed}`)).size, 4);
    assert.ok(arms.every(c => c.params.emitterOn === false && c.params.embers === false && c.params.sliceMode === 'world'));
  }
});

test('CLI validates arguments instead of silently converting invalid values', () => {
  assert.throws(() => parseArgs(['--frames', '2.5']));
  assert.throws(() => parseArgs(['--dt', 'NaN']));
  assert.throws(() => parseArgs(['--frames', '5', '--seconds', '2']));
  assert.throws(() => parseArgs(['--seeds', '-1']));
  assert.throws(() => parseArgs(['--unknown', 'x']));
  assert.equal(parseArgs(['--frames', '10']).frames, 10);
});

test('config refuses changes that silently invalidate matrix labels', () => {
  const args = parseArgs([]);
  for (const params of [{ spreadFlameHeat: false }, { emitterOn: true }, { embers: true }, { sliceMode: 'view' }, { spreadOn: false }]) {
    assert.throws(() => configureCases(args, { params }));
  }
  const cases = configureCases(parseArgs(['--seconds', '2', '--dt', '.1', '--seeds', '3']), { params: { cool: .9 } });
  assert.ok(cases.every(c => c.frames === 20 && c.dt === .1 && c.seed === 3 && c.params.cool === .9));
});

test('CLI duration overrides either form of duration in JSON config', () => {
  const seconds = configureCases(parseArgs(['--seconds', '2', '--dt', '.1']), { frames: 999 });
  assert.ok(seconds.every(c => c.frames === 20));
  const frames = configureCases(parseArgs(['--frames', '20']), { seconds: 99 });
  assert.ok(frames.every(c => c.frames === 20));
});

test('configured seeds must be nonempty distinct uint32 integers before matrix creation', () => {
  for (const seeds of [[], [11, 11], [-1], [0x100000000], [1.5], ['11'], null, '11']) {
    assert.throws(() => configureCases(parseArgs([]), { seeds }), /unique uint32/);
  }
  assert.throws(() => configureCases(parseArgs(['--seeds', '11,11'])), /unique uint32/);
  const cases = configureCases(parseArgs([]), { seeds: [0, 0xffffffff] });
  assert.equal(new Set(cases.map(c => c.id)).size, cases.length);
});
