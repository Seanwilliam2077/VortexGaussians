import assert from 'node:assert/strict';

// Browser-side diagnostics. Input RGB rows are native bottom-up; weights are top-down.
export function measureContrast(on, off, width, height, weights) {
  const blockWidth = width / 2, blockHeight = height / 2;
  if (!Number.isInteger(blockWidth) || !Number.isInteger(blockHeight) ||
      on.length !== width * height * 4 || off.length !== on.length ||
      weights.length !== blockWidth * blockHeight) throw Error('Mismatched full-frame diagnostic buffers');
  function histogram(last, unit) {
    return {unit, all: Array(last + 1).fill(0), target: Array(last + 1).fill(0),
      bounds: {changed: null, above: null, targetChanged: null, targetAbove: null}};
  }
  function include(bounds, key, x, y) {
    const b = bounds[key];
    if (!b) bounds[key] = [x, y, x, y];
    else {
      b[0] = Math.min(b[0], x); b[1] = Math.min(b[1], y);
      b[2] = Math.max(b[2], x); b[3] = Math.max(b[3], y);
    }
  }
  function tally(hist, v, x, y, inTarget, threshold) {
    hist.all[v]++;
    if (inTarget) hist.target[v]++;
    if (v > 0) {
      include(hist.bounds, 'changed', x, y);
      if (inTarget) include(hist.bounds, 'targetChanged', x, y);
    }
    if (v >= threshold) {
      include(hist.bounds, 'above', x, y);
      if (inTarget) include(hist.bounds, 'targetAbove', x, y);
    }
  }
  const pixel = histogram(255, 'native pixel, max-channel absolute RGB byte difference');
  const block = histogram(1020, '2x2 cell, four times max-channel absolute difference of channel means');
  const massByBlockBin = Array(1021).fill(0);
  for (let by = 0; by < blockHeight; by++) for (let bx = 0; bx < blockWidth; bx++) {
    const weight = weights[by * blockWidth + bx], inTarget = weight > 0;
    let dr = 0, dg = 0, db = 0;
    for (let dy = 0; dy < 2; dy++) for (let dx = 0; dx < 2; dx++) {
      const x = 2 * bx + dx, y = 2 * by + dy, j = 4 * ((height - 1 - y) * width + x);
      const r = on[j] - off[j], g = on[j+1] - off[j+1], b = on[j+2] - off[j+2];
      if (on[j+3] !== off[j+3]) throw Error('Native display alpha differs');
      dr += r; dg += g; db += b;
      tally(pixel, Math.max(Math.abs(r), Math.abs(g), Math.abs(b)), x, y, inTarget, 16);
    }
    const bin = Math.max(Math.abs(dr), Math.abs(dg), Math.abs(db));
    tally(block, bin, bx, by, inTarget, 64);
    massByBlockBin[bin] += weight;
  }
  return {width, height, blockWidth, blockHeight, coordinates:'top-left; inclusive bounds in histogram units',
    pixel, block, massByBlockBin};
}

export function instrumentAction(text) {
  function change(needle, value) {
    assert.equal(text.split(needle).length, 2, needle);
    text = text.replace(needle, () => value);
  }
  change('let t141Weights=null;', 'let t141Weights=null;\nlet t144Hist=false;\n' + measureContrast.toString());
  change('t141Weights={box,indices:', 't141Weights={box,fullWeights:eligible,indices:');
  change('const images=[], hashes=[];', 'const images=[], hashes=[], fullFrames=[];');
  change('hashes.push({full_display_rgba_sha256:', 'if(t144Hist)fullFrames.push(full);\n        hashes.push({full_display_rgba_sha256:');
  change('return {mass:changed,denominator:total,', 'const contrast=t144Hist?measureContrast(...fullFrames,cv.width,cv.height,t141Weights.fullWeights):undefined;\n  return {contrast,mass:changed,denominator:total,');
  change('state:state141,', 'state:state141, diagnostic(on){t144Hist=on;},');
  return text;
}
