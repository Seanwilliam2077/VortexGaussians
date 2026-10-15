// Authored physical measures are explicit. analysisWeight affects reporting only.
const A0 = .0016;
const mod = (n, d) => ((n % d) + d) % d;
function point(id, group, position, areaWeight, anchor, cell) {
  return { id, group, position, areaWeight, analysisWeight: areaWeight,
    anchor, cell, fuel: 1, opacity: .5, scale: .025, color: [.35, .23, .1] };
}

export function p2Fixture(kind = 'surface', variant = 'base', order = 'forward') {
  let points = [];
  if (kind === 'raised-target') {
    for (let x = -1; x <= 1; x++) for (let z = -1; z <= 1; z++) {
      points.push(point(`source:${x}:${z}`, 'source', [x * .04, .2, z * .04], A0, true, [x + 1, z + 1]));
      for (let y = 0; y < 3; y++) points.push(point(`target:${x}:${y}:${z}`, 'target', [x * .04, .45 + y * .04, z * .04], A0, true, [x + 1 + 3 * y, z + 1]));
    }
  } else if (kind === 'surface') {
    const uniform = variant === 'refine3' ? 3 : variant === 'refine5' ? 5 : 1;
    for (let x = 0; x <= 20; x++) for (let z = -2; z <= 2; z++) {
      const factor = variant === 'adaptive' && x >= 10 ? 3 : uniform;
      const center = (factor - 1) / 2;
      for (let sx = 0; sx < factor; sx++) for (let sz = 0; sz < factor; sz++) {
        const anchor = sx === center && sz === center;
        const id = `site:${x}:${z}${anchor ? '' : `:f${factor}:${sx}:${sz}`}`;
        points.push(point(id, x < 2 ? 'source' : 'target',
          [x * .04 + (sx - center) * .04 / factor, .2, z * .04 + (sz - center) * .04 / factor],
          A0 / (factor * factor), anchor, [x, z + 2]));
      }
    }
  } else throw new Error(`Unknown fixture ${kind}`);

  const duplicateVariants = ['base', 'uniform2', 'uniform4', 'variable-both', 'variable-source', 'variable-target'];
  if (duplicateVariants.includes(variant)) {
    points = points.flatMap(p => {
      const applies = variant === 'variable-both' || variant === `variable-${p.group}`;
      const copies = variant === 'uniform2' ? 2 : variant === 'uniform4' ? 4
        : applies ? 1 + mod(p.cell[0] + 2 * p.cell[1], 4) : 1;
      return Array.from({ length: copies }, (_, copy) => ({ ...p,
        id: copy ? `${p.id}:copy${copy}` : p.id, position: [...p.position], color: [...p.color],
        anchor: p.anchor && copy === 0, areaWeight: p.areaWeight / copies, analysisWeight: p.analysisWeight / copies }));
    });
  } else if (!['refine3', 'refine5', 'adaptive'].includes(variant) || kind !== 'surface') throw new Error(`Unknown variant ${kind}/${variant}`);
  if (order === 'shuffle') {
    let state = 73013;
    for (let i = points.length - 1; i > 0; i--) {
      state = (Math.imul(1664525, state) + 1013904223) >>> 0;
      const j = Math.floor(state / 4294967296 * (i + 1));
      [points[i], points[j]] = [points[j], points[i]];
    }
  } else if (order !== 'forward') throw new Error(`Unknown order ${order}`);
  const sourcePositions = [...new Map(points.filter(p => p.group === 'source').map(p => [p.position.join(','), p.position])).values()];
  const groupAreas = {};
  for (const p of points) groupAreas[p.group] = (groupAreas[p.group] || 0) + p.areaWeight;
  return { name: `p2-${kind}`, kind, variant, order, points, sourcePositions,
    ignitionRadius: 1e-6, groupAreas, representedArea: Object.values(groupAreas).reduce((a, b) => a + b, 0),
    referenceArea: A0, commonAnchorIds: points.filter(p => p.anchor).map(p => p.id).sort(),
    densityMap: points.map(({ id, position, areaWeight, analysisWeight, anchor, cell }) => ({ id, position, areaWeight, analysisWeight, anchor, cell })),
    domain: kind === 'surface' ? { x: [-.02, .82], z: [-.10, .10], y: .2, sourcePatch: 'x < .06', adaptiveCells: 'coarse cell center x >= .4 subdivided 3x3' } : null,
    interpretation: kind === 'surface' ? 'Cell-centred authored area partitions; nested odd refinements retain every coarse centre.' : 'Raised-target geometry with explicit .0016 area per original site, split among duplicates.' };
}
