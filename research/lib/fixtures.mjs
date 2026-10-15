// Coordinates are world coordinates under the research API's identity transform.
// Analysis weights never modify the authored per-splat fuel or the simulator.
function point(id, group, x, y, z, weight = 1, anchor = true) {
  return { id, group, position: [x, y, z], fuel: 1, opacity: 0.5, scale: 0.025,
    color: [0.35, 0.23, 0.1], analysisWeight: weight, anchor };
}

export function fixture(name, { density = 1, order = 'forward', orderSeed = 123 } = {}) {
  if (![1, 2, 4].includes(density)) throw new Error('density must be 1, 2 or 4');
  let points = [], ignition, purpose;
  if (name === 'raised-target') {
    for (let x = -1; x <= 1; x++) for (let z = -1; z <= 1; z++) {
      points.push(point(`source:${x}:${z}`, 'source', x * .04, .20, z * .04));
      for (let y = 0; y < 3; y++) points.push(point(`target:${x}:${y}:${z}`, 'target', x * .04, .45 + y * .04, z * .04));
    }
    ignition = { position: [0, .20, 0], radius: .075 };
    purpose = 'Buoyant source-to-target feedback: .25 gap exceeds both .11 graph radius and .14 initial flame heating radius.';
  } else if (name === 'surface-strip') {
    for (let x = 0; x <= 20; x++) for (let z = -2; z <= 2; z++) {
      points.push(point(`strip:${x}:${z}`, x <= 1 ? 'source' : 'target', x * .04, .20, z * .04, .04 * .04));
    }
    ignition = { position: [0, .20, 0], radius: .06 };
    purpose = 'Connected surface graph; duplication preserves geometry, anchor IDs, and area-weighted analysis.';
  } else if (name === 'cap-stress') {
    for (let x = -20; x <= 20; x++) for (let z = -20; z <= 20; z++) {
      points.push(point(`scheduler:${x}:${z}`, x < 0 ? 'left' : x > 0 ? 'right' : 'center', x * .12, .20, z * .12));
    }
    ignition = { position: [0, .20, 0], radius: 3.5 };
    purpose = '1681 disconnected preignited sites: scheduler/fuel-service diagnostic only; no physical scene or propagation claim.';
  } else throw new Error(`Unknown fixture: ${name}`);
  const base = points;
  points = base.flatMap(p => Array.from({ length: density }, (_, copy) => ({ ...p,
    id: copy ? `${p.id}:duplicate:${copy}` : p.id, position: [...p.position], color: [...p.color],
    analysisWeight: p.analysisWeight / density, anchor: copy === 0 })));
  if (order === 'reverse') points.reverse();
  else if (order === 'shuffle') {
    let state = orderSeed >>> 0;
    for (let i = points.length - 1; i > 0; i--) {
      state = (Math.imul(1664525, state) + 1013904223) >>> 0;
      const j = Math.floor((state / 4294967296) * (i + 1));
      [points[i], points[j]] = [points[j], points[i]];
    }
  } else if (order !== 'forward') throw new Error(`Unknown order: ${order}`);
  return { name, density, order, orderSeed, purpose, ignition, points,
    densityMap: points.map(({ id, position, analysisWeight, anchor }) => ({ id, position, analysisWeight, anchor })),
    graph: graphDescription(points, .11) };
}

export function graphDescription(points, radius) {
  // Exact diagnostic graph, independent of the simulator's spatial hash.
  const parent = points.map((_, i) => i), degrees = points.map(() => 0);
  const find = x => { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; };
  for (let i = 0; i < points.length; i++) for (let j = i + 1; j < points.length; j++) {
    const a = points[i].position, b = points[j].position;
    if (a.reduce((v, x, k) => v + (x - b[k]) ** 2, 0) <= radius ** 2) {
      degrees[i]++; degrees[j]++; parent[find(i)] = find(j);
    }
  }
  return { radius, components: new Set(points.map((_, i) => find(i))).size,
    minDegree: Math.min(...degrees), maxDegree: Math.max(...degrees),
    meanDegree: degrees.reduce((a, b) => a + b, 0) / points.length };
}
