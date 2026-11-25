import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Script} from 'node:vm';

const here=path.dirname(fileURLToPath(import.meta.url));
const sha=s=>createHash('sha256').update(s).digest('hex');
const ordinary=await fs.readFile(path.join(here,'../t97-ordinary-cached-graph/ordinary.js'),'utf8');
const slice=await fs.readFile(path.join(here,'../t95-multistep-material-slice/slice.js'),'utf8');
assert.equal(sha(ordinary),'e9842f4b3c3fd09c8f018fb675fd40f7c08836077db3d7e4e978b126f860f388');
assert.equal(sha(slice),'f36395b687f63db3c66f1786022a01ec11eebe64c4e513c7a97cb88d9e87a214');
const anchor='  const decay=1-dt*.35;';
const end='  /* NATIVE_EMISSION */';
const tail=ordinary.slice(ordinary.indexOf(anchor),ordinary.indexOf(end));
assert(tail.includes('sb.burning=sb.burning.filter') && tail.includes('t97Neighbours'));
const repair=`function t100Replay(frame,dt) {
  const sb=sceneBurnState,q=null,r=P.spreadIgnR;
  const data=frame.values;
  for(let j=0;j<frame.count*4;j+=4) {
    const s=[data[j],data[j+1],data[j+2]], T=data[j+3];
    hashQuery(s,r,(id,d)=>{if(sb.state[id]===0) sb.h[id]+=dt*P.spreadHeat*T*(1-d/r);});
  }
  ${tail}
  // Under the prefix proof the sliced feed and native feed visit the same ordered IDs.
  // Gas and the RNG are already at the end of this frame.
  sb.emitCursor=frame.cursor;
}`;
let advance=slice.slice(slice.indexOf('function t95Advance('));
assert.equal(advance.split('const s=worldToSrc(p.x,p.y,z);').length,2);
advance=advance.replace('function t95Advance(plan,dt)','function t100Advance(plan,dt,log)')
  .replace('const s=worldToSrc(p.x,p.y,z);',`const s=worldToSrc(p.x,p.y,z);
      if(log){const j=4*log.count++;log.values[j]=s[0];log.values[j+1]=s[1];log.values[j+2]=s[2];log.values[j+3]=p.T;}`)
  .replace('  t95Feed(dt);','  t95Feed(dt); if(log)log.cursor=sb.emitCursor;');
const code=advance+'\n'+repair+'\n'+await fs.readFile(path.join(here,'repair.js'),'utf8');
new Script(code);
await fs.mkdir(path.join(here,'local'),{recursive:true});await fs.writeFile(path.join(here,'local/plugin.js'),code);
console.log(sha(code));
