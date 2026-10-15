export function assertSnapshot(s) {
  if (!s || !Array.isArray(s.points) || !s.hash || !s.scene?.burnHash) throw new Error('Missing detailed research snapshot/hash/burnHash');
  const finite = (x, where) => {
    if (typeof x === 'number' && !Number.isFinite(x)) throw new Error(`Non-finite snapshot number at ${where}`);
    if (x && typeof x === 'object') for (const [k, v] of Object.entries(x)) finite(v, `${where}.${k}`);
  };
  finite(s, 'snapshot');
  if (new Set(s.points.map(p => p.id)).size !== s.points.length) throw new Error('Duplicate stable point IDs');
  return s;
}

export function measure(snapshot, fixture, firstIgnition) {
  assertSnapshot(snapshot);
  const authored = new Map(fixture.points.map(p => [p.id, p]));
  if (snapshot.points.length !== authored.size) throw new Error('Snapshot fixture point count mismatch');
  const groups = {};
  for (const p of snapshot.points) {
    const source = authored.get(p.id);
    if (!source) throw new Error(`Unrecognized point ${p.id}`);
    if (p.state !== 0 && !firstIgnition.has(p.id)) firstIgnition.set(p.id, snapshot.time);
    const g = groups[p.group] ||= { count: 0, burning: 0, charred: 0, everIgnited: 0,
      heatSum: 0, heatMax: 0, fuelRemaining: 0, fuelConsumed: 0, weightSum: 0,
      weightedChar: 0, weightedFuelConsumed: 0, weightedEverIgnited: 0, anchors: [] };
    g.count++; g.burning += +(p.state === 1); g.charred += +(p.state === 2);
    g.everIgnited += +firstIgnition.has(p.id); g.heatSum += p.heat; g.heatMax = Math.max(g.heatMax, p.heat);
    g.fuelRemaining += p.fuel; g.fuelConsumed += p.fuelInitial - p.fuel;
    g.weightSum += source.analysisWeight;
    g.weightedChar += p.char * source.analysisWeight;
    g.weightedFuelConsumed += (p.fuelInitial - p.fuel) * source.analysisWeight;
    g.weightedEverIgnited += +firstIgnition.has(p.id) * source.analysisWeight;
    if (source.anchor) g.anchors.push({ id: p.id, heat: p.heat, state: p.state, char: p.char, fuel: p.fuel });
  }
  for (const g of Object.values(groups)) {
    g.meanChar = g.weightedChar / g.weightSum;
    g.meanFuelConsumed = g.weightedFuelConsumed / g.weightSum;
    g.ignitedFraction = g.weightedEverIgnited / g.weightSum;
  }
  return { time: snapshot.time, frame: snapshot.frame, hash: snapshot.hash, burnHash: snapshot.scene.burnHash,
    scene: snapshot.scene, particles: snapshot.particles, counters: snapshot.counters, groups };
}

export function classify(samples, fixtureName) {
  const last = samples.at(-1), peakTargetHeat = Math.max(0, ...samples.map(s => s.groups.target?.heatMax || 0));
  const targetIgnited = last.groups.target?.everIgnited || 0;
  return { targetIgnited, peakTargetHeat, sceneSeedsEmitted: last.counters.sceneSeedsEmitted,
    targetExposureObserved: peakTargetHeat > 0,
    outcome: fixtureName !== 'raised-target' ? 'diagnostic' : targetIgnited > 0 ? 'target_ignited'
      : peakTargetHeat === 0 ? 'no_target_exposure_observed' : 'exposed_without_ignition',
    warning: 'Exposure is measured only at sample times; zero endpoint or zero sampled exposure does not prove feedback ineffective.' };
}

const csvCell = value => /[",\r\n]/.test(String(value ?? '')) ? `"${String(value).replaceAll('"', '""')}"` : String(value ?? '');
export function timeseriesCsv(samples) {
  const rows = [];
  for (const s of samples) for (const [group, g] of Object.entries(s.groups)) {
    const row = { frame: s.frame, time: s.time, group, hash: s.hash, burnHash: s.burnHash };
    for (const [key, value] of Object.entries(g)) if (typeof value === 'number') row[key] = value;
    for (const [key, value] of Object.entries(s.particles)) if (typeof value === 'number') row[`particles.${key}`] = value;
    for (const [key, value] of Object.entries(s.counters)) if (typeof value === 'number') row[`counters.${key}`] = value;
    rows.push(row);
  }
  const keys = [...new Set(rows.flatMap(r => Object.keys(r)))];
  return [keys.join(','), ...rows.map(r => keys.map(k => csvCell(r[k])).join(','))].join('\n') + '\n';
}
