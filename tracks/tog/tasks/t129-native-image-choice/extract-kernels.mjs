// Rebuild the compact vendored implementation from the historical local T119 build products.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const pieces=[];
async function source(file,hash){
  const bytes=await fs.readFile(path.resolve(here,'..',file));
  assert.equal(createHash('sha256').update(bytes).digest('hex'),hash,file);
  return bytes.toString().replaceAll('\r\n','\n');
}
function pull(text,first,next){
  const a=text.indexOf(first),b=text.indexOf(next,a);
  assert(a>=0 && b>a,first+' / '+next);
  return text.slice(a,b);
}
const q=await source('t90-callable-regional-query/query.js','0e0cd4cecba197fb109e61cdd522f591bfc4d22722f3ff43a0923d35b3f27036');
pieces.push(pull(q,'let t90Query', 'function t90Run('));
const gas=await source('t95-multistep-material-slice/local/plugin.js','5782263e00c896e983614799332480c0abff925c83b1faaf6920b8c827af74c2');
pieces.push(pull(gas,'function t95FullGas(', 'function t95Feed('));
const graph=await source('t97-ordinary-cached-graph/.generated-plugin.js','36a19010dfda87a3c27e2f458a529e14537eda16a5f6055e681c025fdbca3e59');
pieces.push(pull(graph,'const t97AssetGraph', 'function t97Neighbours('),pull(graph,'function t97Use(', 'const t97NativeStepSpread'));
const tail=await source('t102-active-recipients/local/plugin.js','3311852d29e7c1ee2b6f9b615235174ece6550c79b0c889e6e7b3b7f4c1e8474');
pieces.push(pull(tail,'function t102MaterialTail(', 'function t102Spread('));
const active=await source('t102-active-recipients/active.js','355cb566eb3328094232395564b24d82b9f05e3d0e2b505502f9048ccd1fa49c');
pieces.push(pull(active,'let t102Anchor', 'function t102ResetBranch('));
const fork=await source('t98-edit-to-answer/click.js','62e138b45fb747aa45d3981e17c2ad16b52ff2885c1bde1277387ce26078e49f');
pieces.push(fork);
const sibling=await source('t119-cross-sibling-actions/local/firewoods-1/plugin.js','1505050a662c4d4d2561346eeff98d9a0d099485d78614a706cfb7a10a3ac0f1');
const kernel=pull(sibling,'let t116Geometry','function t116Slice(');
const tap='      if(p.mask[i]) t111Add(p,i);';
assert.equal(kernel.split(tap).length,2);
// The new observable is measured from final display bytes. Both methods omit the earlier material query callback.
pieces.push(kernel.replace(tap,''),pull(sibling,'function t119Materialize(', '// Runs inside the pinned T111'),pull(sibling,'function t119Guard(', 'function t119Run('));
const phys=await source('t100-material-repair/repair.js','941b4158868850ab59ffea796e8d9a15a2ee5fb609dbb4b6ae6df4d71b9e544f');
const mark=await source('t108-visible-progression/progress.js','a83dd58ba02700210d202db95cf9920ce21c4abb7c5907c0ec02d1732c3beab3');
pieces.push(pull(phys,'function t100Physical()', 'function t100Equal('),pull(mark,'function t108Fingerprint()', 'function t108Answer('));
await fs.writeFile(path.join(here,'native-kernels.js'),'// Source snapshots for portable reproduction. Regenerate with extract-kernels.mjs.\n'+pieces.map(x=>x.trim()).join('\n\n')+'\n');

