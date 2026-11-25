// Keep all four frozen numerical methods. Only the ROI and requested deadline change.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url)), base=path.join(here,'../t100-material-repair');
const active=path.join(here,'../t102-active-recipients'), local=path.join(here,'local');
const digest=data=>createHash('sha256').update(data).digest('hex');
async function pinned(filename,hash) {
  const data=await fs.readFile(filename,'utf8'); assert.equal(digest(data),hash,filename); return data;
}
function replaceOnce(s,from,to){assert.equal(s.split(from).length,2,from);return s.replace(from,()=>to);}
await fs.mkdir(local,{recursive:true});
const pins=[
  [path.join(base,'local/plugin.js'),'35ffeaccd926572685d1f1c0b7e3c3a785c953925762820400ce5735579bfb98'],
  [path.join(base,'local/active-repair.js'),'3f1904a68c1eee4a94681140816c91de000243e82f03af4a140abf502a7f87eb'],
  [path.join(active,'local/plugin.js'),'3311852d29e7c1ee2b6f9b615235174ece6550c79b0c889e6e7b3b7f4c1e8474'],
  [path.join(active,'audit.js'),'8011178b2d71699d05e3d38eaa617cd428bef3e8e440c7133f9b20c4d3d7efbf']];
for(const [file,hash] of pins){
  const src=await pinned(file,hash);
  if(path.dirname(file)===path.join(base,'local')) await fs.writeFile(path.join(local,path.basename(file)),src);
}
const query=await pinned(path.join(here,'../t90-callable-regional-query/query.js'),
  '0e0cd4cecba197fb109e61cdd522f591bfc4d22722f3ff43a0923d35b3f27036');
const head=query.indexOf('function t90Configure(pick)'), tail=query.indexOf('function t90Fork()');
assert(head>=0 && tail>head);
const selection=JSON.parse(await fs.readFile(path.join(here,'selection.json'),'utf8'));
let region=query.slice(head,tail).replace('function t90Configure(pick)', 'function t105Configure()');
region=region.replaceAll('pick.world','t105World');
region=replaceOnce(region,'d > pick.radius && d <= pick.radius + P.spreadIgnR','d <= '+selection.radius);
region='\nconst t105World='+JSON.stringify(selection.world)+';\n'+region+'\nwindow.__t90.configure=t105Configure;\n';

let source=await pinned(path.join(base,'run.mjs'),'2abbd95d84d4e290cfb235402bd80e9c2115319b4626ea9eb3bed8c49fd5cf20');
source=replaceOnce(source,'const here=path.dirname(fileURLToPath(import.meta.url));','const here='+JSON.stringify(base)+';');
source=replaceOnce(source,"\nconst local=path.join(here,'local');",'\nconst local='+JSON.stringify(local)+';');
source=replaceOnce(source,"await fs.writeFile(path.join(local,'click.js'),click);","await fs.writeFile(path.join(local,'click.js'),click+"+JSON.stringify(region)+");");
source=replaceOnce(source,"for(const horizon of [30,60,180])","for(const horizon of [180])");
source=replaceOnce(source,"JSON.stringify(portable(fileURLToPath(import.meta.url)))","JSON.stringify("+JSON.stringify(fileURLToPath(import.meta.url).split(path.sep).join('/'))+")");
source=replaceOnce(source,"schema:'t100-material-repair-v1'","schema:'t105-protected-selection-v1'");
const geom=path.join(here,'../t101-playground-holdout/local/scene.ply');
const flags=process.argv.slice(2);
assert(flags.length===0 || (flags.length===2 && flags[0]==='--out'),'Optional --out NEW_DIR');
process.argv=process.argv.slice(0,2).concat('--out',flags[1]||path.join(here,'evidence/timing'),
  '--methods','active-anchor,restart-active,repair-active,active-fresh','--repeats','4',
  '--asset',geom,'--recipe',path.join(here,'recipe.json'),'--reference',path.join(here,'evidence/native/capture-report.json'),
  '--traces',path.join(here,'evidence/native'),'--external-targets',path.join(here,'REFERENCE.json'),
  '--asset-name','protected','--active-plugin',pins[2][0],'--active-audit',pins[3][0]);
await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
