import { createHash } from 'node:crypto';

export function validateImage(image) {
  if (!Number.isInteger(image.width) || image.width < 1 || !Number.isInteger(image.height) || image.height < 1 ||
      image.data.length !== image.width * image.height * 4) throw new Error('Invalid RGBA dimensions/length');
  for (const x of image.data) if (!Number.isFinite(x)) throw new Error('Nonfinite linear image value');
  return image;
}

export function imageError(candidate, reference, thresholds = {}) {
  validateImage(candidate); validateImage(reference);
  if (candidate.width !== reference.width || candidate.height !== reference.height) throw new Error('Image dimensions differ');
  if (candidate.orientation && reference.orientation && candidate.orientation !== reference.orientation) throw new Error('Image orientations differ');
  const foregroundAlpha = thresholds.foregroundAlpha ?? .01;
  const holeReferenceAlpha = thresholds.holeReferenceAlpha ?? .2;
  const holeCandidateAlpha = thresholds.holeCandidateAlpha ?? .05;
  const foregroundMask = thresholds.foregroundMask;
  const holeMask = thresholds.holeMask;
  for (const mask of [foregroundMask, holeMask]) if (mask && mask.length !== candidate.width * candidate.height) throw new Error('Mask dimensions differ');
  const regions = { full: accum(), foreground: accum() };
  let holeDenominator = 0, holePixels = 0;
  for (let i = 0; i < candidate.data.length; i += 4) {
    const a = candidate.data, b = reference.data;
    for (const region of [regions.full, ...((foregroundMask ? foregroundMask[i / 4] : b[i + 3] > foregroundAlpha) ? [regions.foreground] : [])]) {
      region.pixels++;
      for (let c = 0; c < 3; c++) { const d = a[i + c] - b[i + c]; region.rgbSquaredError += d * d; region.rgbAbsoluteError += Math.abs(d); }
      const d = a[i + 3] - b[i + 3]; region.alphaSquaredError += d * d; region.alphaAbsoluteError += Math.abs(d);
    }
    if (holeMask ? holeMask[i / 4] : b[i + 3] >= holeReferenceAlpha) { holeDenominator++; if (a[i + 3] < holeCandidateAlpha) holePixels++; }
  }
  return { ...Object.fromEntries(Object.entries(regions).map(([key, r]) => [key, finish(r)])),
    holes: { pixels: holePixels, denominator: holeDenominator, fraction: holeDenominator ? holePixels / holeDenominator : null },
    thresholds: { foregroundAlpha, holeReferenceAlpha, holeCandidateAlpha, fixedReferenceMask: !!foregroundMask } };
}

export function referenceMasks(images, thresholds = {}) {
  if (!images.length) throw new Error('No reference images for ROI');
  images.forEach(validateImage); const first = images[0];
  if (images.some(im => im.width !== first.width || im.height !== first.height || im.orientation !== first.orientation)) throw new Error('Reference image formats differ');
  const alpha = new Float64Array(first.width * first.height);
  for (const im of images) for (let i = 0; i < alpha.length; i++) alpha[i] += im.data[4 * i + 3] / images.length;
  return { foregroundMask: Uint8Array.from(alpha, a => +(a > (thresholds.foregroundAlpha ?? .01))),
    holeMask: Uint8Array.from(alpha, a => +(a >= (thresholds.holeReferenceAlpha ?? .2))),
    referenceCount: images.length, width: first.width, height: first.height, orientation: first.orientation };
}
function accum() { return { pixels: 0, rgbSquaredError: 0, rgbAbsoluteError: 0, alphaSquaredError: 0, alphaAbsoluteError: 0 }; }
function finish(r) { return { ...r, rgbRmse: r.pixels ? Math.sqrt(r.rgbSquaredError / (3 * r.pixels)) : null,
  alphaRmse: r.pixels ? Math.sqrt(r.alphaSquaredError / r.pixels) : null,
  rgbMae: r.pixels ? r.rgbAbsoluteError / (3 * r.pixels) : null, alphaMae: r.pixels ? r.alphaAbsoluteError / r.pixels : null }; }

export function poolErrors(errors) {
  if (!errors.length) throw new Error('No image errors to pool');
  return Object.fromEntries(['full', 'foreground'].map(region => {
    const sum = accum();
    for (const e of errors) for (const key of Object.keys(sum)) sum[key] += e[region][key];
    return [region, finish(sum)];
  }));
}

export function referenceGate(low, reference, ratio = .25) {
  const checks = [];
  for (const region of ['full', 'foreground']) for (const channel of ['rgb', 'alpha']) {
    const denominator = low[region][`${channel}Rmse`], numerator = reference[region][`${channel}Rmse`];
    const meaningful = Number.isFinite(denominator) && denominator > 0 && Number.isFinite(numerator);
    checks.push({ region, channel, numerator, denominator, ratio: meaningful ? numerator / denominator : null,
      passed: meaningful && numerator <= ratio * denominator,
      reason: meaningful ? null : 'Empty ROI or zero/nonfinite low-reference signal; cannot validate reference' });
  }
  return { passed: checks.every(c => c.passed), threshold: ratio, checks };
}

export function imageSummary(image) {
  validateImage(image); const n = image.width * image.height;
  let alphaSum = 0, alphaMax = -Infinity, rgbSum = 0, foreground = 0, saturatedAlpha = 0;
  for (let i = 0; i < image.data.length; i += 4) {
    const a = image.data[i + 3]; alphaSum += a; alphaMax = Math.max(alphaMax, a);
    rgbSum += image.data[i] + image.data[i + 1] + image.data[i + 2];
    if (a > .01) foreground++; if (a > .99) saturatedAlpha++;
  }
  return { meanAlpha: alphaSum / n, maxAlpha: alphaMax, meanRgb: rgbSum / (3 * n),
    foregroundFraction: foreground / n, saturatedAlphaFraction: saturatedAlpha / n };
}

export function encodeFloat32(image) {
  validateImage(image); const bytes = Buffer.alloc(image.data.length * 4);
  for (let i = 0; i < image.data.length; i++) bytes.writeFloatLE(image.data[i], i * 4);
  return { bytes, sha256: createHash('sha256').update(bytes).digest('hex'),
    width: image.width, height: image.height, channels: 4, type: 'float32', endianness: 'little',
    orientation: image.orientation || 'bottom-left', colorSpace: 'linear', layout: 'interleaved RGBA' };
}
export function decodeFloat32(bytes, metadata) {
  if (bytes.length !== metadata.width * metadata.height * 16) throw new Error('Float32 file length disagrees with dimensions');
  if (metadata.sha256 && createHash('sha256').update(bytes).digest('hex') !== metadata.sha256) throw new Error('Float32 file checksum mismatch');
  const data = new Float32Array(bytes.length / 4);
  for (let i = 0; i < data.length; i++) data[i] = bytes.readFloatLE(i * 4);
  return validateImage({ ...metadata, data });
}
export function distribution(values) {
  if (!values.length || values.some(x => !Number.isFinite(x) || x < 0)) throw new Error('Invalid timing samples');
  const sorted = [...values].sort((a, b) => a - b), q = p => sorted[Math.floor((sorted.length - 1) * p)];
  return { count: sorted.length, minimum: sorted[0], median: q(.5), p90: q(.9), p95: q(.95), maximum: sorted.at(-1), mean: sorted.reduce((a, b) => a + b, 0) / sorted.length };
}
