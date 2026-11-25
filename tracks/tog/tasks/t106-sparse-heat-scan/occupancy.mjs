import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
const here=path.dirname(fileURLToPath(import.meta.url));
const result=[];
for(const [asset,folder] of [['firewoods','t86-ignition-margin'],['dead-tree','t92-transfer-workload/evidence']]){
  for(const arm of ['AB','BA'])for(const frame of [210,240,300]){
    const raw=await fs.readFile(path.join(here,'..',folder,'checkpoints',arm+'-'+frame+'.json.gz'));
    const c=JSON.parse(gunzipSync(raw)),byState=[0,0,0],all=[0,0,0];
    assert.equal(c.heat.length,c.state.length);
    const blocks=new Set();
    for(let i=0;i<c.heat.length;i++){
      assert([0,1,2].includes(c.state[i]) && Number.isFinite(c.heat[i]) && c.heat[i]>=0);
      all[c.state[i]]++;
      if(c.heat[i]>0){byState[c.state[i]]++;blocks.add(i>>>5);}
    }
    result.push({asset,arm,frame,sites:c.state.length,positive:byState.reduce((a,b)=>a+b,0),by_state:byState,
      sites_by_state:all,nonempty_words:blocks.size,bitmap_words:Math.ceil(c.state.length/32),
      checkpoint_sha256:createHash('sha256').update(raw).digest('hex')});
  }
}
await fs.writeFile(path.join(here,'OCCUPANCY.json'),JSON.stringify(result,null,2)+'\n');
for(const r of result)console.log(r.asset,r.arm,r.frame,r.positive+'/'+r.sites,r.by_state);
