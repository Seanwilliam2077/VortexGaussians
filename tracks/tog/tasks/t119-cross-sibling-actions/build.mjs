import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const sha=x=>createHash('sha256').update(x).digest('hex');
export async function build(here,local){
  const pin=async(p,h)=>{const a=await fs.readFile(path.join(here,p),'utf8');assert.equal(sha(a),h,p);return a;};
  const cold=await pin('../t116-cold-flame-contacts/local/plugin.js','6144304de535350765f57e042c61fc206a73b35f5b54b01a25d546ffdc769e29');
  const transport=await pin('../t118-sibling-native-transport/transport.js','0466f994b4ebc8de786f1e3c0fb071279c30453a3ab1c316a54d07ab5e15575b');
  const first=transport.indexOf('    for (const id of extra) {'),last=transport.indexOf('    for (const end of samples)',first);
  assert(first>0 && last>first);
  const move='function t119Materialize(sb,lightIds,fullIds,steps,dt){\n'+
    'const lightSet=new Set(lightIds), extra=fullIds.filter(id=>!lightSet.has(id)), extraSet=new Set(extra);\n'+
    'const current=sceneBurnState,parentOrder=sb.burning;\n'+transport.slice(first,last)+'\n}\n';
  const until=cold.indexOf('function t116Sitewise(');assert(until>0);
  const kernel=cold.slice(0,until);assert.equal(kernel.split('t108Add(').length,3);
  const plugin=kernel.replaceAll('t108Add(','t111Add(')+'\n'+move+await fs.readFile(path.join(here,'sibling.js'),'utf8');
  const file=path.join(local,'plugin.js');await fs.writeFile(file,plugin);return file;
}
