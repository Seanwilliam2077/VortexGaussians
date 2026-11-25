// Extract the prepared native field query verbatim so formulas and float stores stay in sync.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Script} from 'node:vm';

const here = path.dirname(fileURLToPath(import.meta.url));
const demo = await readFile(path.resolve(here, '../../../../demo/index.html'), 'utf8');
assert.equal(createHash('sha256').update(demo).digest('hex'), 'e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0');
const native = demo.slice(demo.indexOf('function stepSimVPM(layer, dt){'), demo.indexOf('//  M6: 3D Gaussian VPM'));
function between(text, start, end) {
  const a = text.indexOf(start), b = text.indexOf(end, a);
  assert(a >= 0 && b > a && text.indexOf(start, a + 1) < 0, 'Native source boundaries changed');
  return text.slice(a, b);
}
const constants = between(native, '  const C=P.gam', '  for(let i=0;i<n;i++){');
const query = between(native, '    const px=pl.X[i]', '\n  }\n  const out=[];');
const sourceAdvance = between(demo.slice(demo.indexOf('function stepAll(dt){')), '  if(pointer.active){\n    source.x=pointer.x;', "  if(P.dimMode==='vol')");
const body = await readFile(path.join(here,'terminal.js'),'utf8');
const compiled = body.replace('/* NATIVE_FIELD */', constants + query).replace('/* NATIVE_SOURCE_ADVANCE */', sourceAdvance);
new Script(compiled);
const out = path.resolve(process.argv[2] || path.join(here, 'local', 'plugin.js'));
await mkdir(path.dirname(out), {recursive:true});
await writeFile(out, compiled);
console.log(createHash('sha256').update(compiled).digest('hex') + '  ' + path.basename(out));
