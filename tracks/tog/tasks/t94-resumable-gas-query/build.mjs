import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Script} from 'node:vm';

const here=path.dirname(fileURLToPath(import.meta.url));
const sha=b=>createHash('sha256').update(b).digest('hex');
const demo=await fs.readFile(path.join(here,'../../../../demo/index.html'),'utf8');
const t93=await fs.readFile(path.join(here,'../t93-exact-terminal-gas/local/plugin.js'),'utf8');
assert.equal(sha(t93),'568ad31b48d449ea07eab9f6bcee93315ded72893fe47b4559ec8745f2a3e638');
assert.equal(sha(demo),'e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0');
function extract(text,start,end) {
  const i=text.indexOf(start),j=text.indexOf(end,i+start.length);
  assert(i>=0 && j>i); return text.slice(i,j);
}
function replace(text,a,b) {assert.equal(text.split(a).length,2,'Source changed: '+a);return text.replace(a,()=>b);}
let probe=extract(t93,'function t93TerminalQuery','function t93Terminal(');
probe=replace(probe,'function t93TerminalQuery(shellIds, dt, mode)', 'function t94Advance(shellIds, dt, mode, terminal, forceContinue)');
probe=replace(probe,"  if (!active) return {decision:'no', witness:null, counts};", `  if (!active && !forceContinue) return {decision:'no', witness:null, counts, empty:true};
  const probeHeat=sb.h.slice();`);
probe=replace(probe,'  counts.available = layers.reduce', `  const cache=layers.map(l=>new Uint8Array(l.ps.length));
  for(const l of layers) l.t+=dt;
  counts.available = layers.reduce`);
probe=replace(probe,'    layer.t += dt;','');
assert.equal(probe.split('t93Velocity(layer, pl, i);').length,4);
probe=probe.replaceAll('t93Velocity(layer, pl, i);','t93Velocity(layer, pl, i); cache[layer.idx][i]=1;');
probe=replace(probe,'if (eligible[id]) sb.h[id] +=','if (eligible[id]) probeHeat[id] +=');
const end=probe.indexOf('  for (const id of shellIds) {',probe.indexOf('counts.heat_queries++;'));
assert(end>0);
probe=probe.slice(0,end)+`  let witness=null;
  for (const id of shellIds) {
    if (eligible[id] && probeHeat[id]>0 && Math.fround(probeHeat[id]*(1-dt*.35))>=P.spreadIgnH) {
      witness=id; break;
    }
  }
  counts.reused_fields=0; counts.new_fields=0;
  if(forceContinue || (witness===null && !terminal)) {
    for(const layer of layers) {
      const pl=vpmPools[layer.idx], done=cache[layer.idx];
      for(let i=0;i<layer.ps.length;i++) {
        if(done[i]) counts.reused_fields++;
        else {t93Velocity(layer,pl,i);counts.new_fields++;}
      }
      t94Scatter(layer,dt);
    }
    stepEmbers(dt);
    const activeQuery=t90Query;
    t90Query=null; // Complete the entire native graph/heat/seed update exactly once.
    try {stepSpread(dt);} finally {t90Query=activeQuery;}
  }
  return {decision:witness===null?'no':'yes',witness,counts};
}
`;
const scatter=extract(demo.slice(demo.indexOf('function stepSimVPM(layer, dt){')),'  const out=[];','  layer.ps=out;')+'  layer.ps=out;';
const body='function t94Scatter(layer,dt){const pl=vpmPools[layer.idx],ps=layer.ps,n=ps.length;\n'+scatter+'\n}\n'+probe;
new Script(body);
await fs.mkdir(path.join(here,'local'),{recursive:true});
await fs.writeFile(path.join(here,'local/plugin.js'),body);
console.log(sha(body));
