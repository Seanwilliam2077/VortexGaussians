import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Script} from 'node:vm';
const here=path.dirname(fileURLToPath(import.meta.url)),sha=s=>createHash('sha256').update(s).digest('hex');
function once(s,a,b){assert.equal(s.split(a).length,2,a);return s.replace(a,()=>b);}
function section(s,a,b){const i=s.indexOf(a),j=s.indexOf(b,i+a.length);assert(i>=0&&j>i,a);return s.slice(i,j);}
const task=name=>path.join(here,'..',name);
const orig=await fs.readFile(task('t114-sitewise-material-repair/local/firewoods.js'),'utf8');
const replay=await fs.readFile(task('t100-material-repair/local/active-repair.js'),'utf8');
const temporal=await fs.readFile(task('t114-sitewise-material-repair/repair.js'),'utf8');
assert.equal(sha(replay),'3f1904a68c1eee4a94681140816c91de000243e82f03af4a140abf502a7f87eb');
assert.equal(sha(temporal),'89fa0f7e380d03875c7c0cac9c24a8d2fee88d48c878de09bbe1bcf54235b682');
let grid=await fs.readFile(path.join(here,'grid.js'),'utf8');
let tracked=grid.slice(grid.indexOf('function t116VisitRaw')).replace('t116VisitRaw','t116VisitTracked');
for(const [mark,act] of [['SAMPLE','samples'],['STALE','initially_noncold_in_bucket'],['CHECK','distance_tests'],['HIT','within_radius']])
  tracked=once(tracked,'/* T116_'+mark+' */','g.stats.'+act+'++;');
let full=section(orig,'function t108Full(','function t108Slice(').replace('t108Full','t116Full');
full=once(full,'const r=P.spreadIgnR;','const r=P.spreadIgnR, grid=t116Grid(sb,null);');
full=once(full,'hashQuery(worldToSrc','grid.walk(grid,worldToSrc');
full=once(full,'sb.state[i]=1; sb.burning.push(i);','sb.state[i]=1; t116Remove(grid,i); sb.burning.push(i);');
let slice=section(orig,'function t108Slice(','let t108Weights=').replace('t108Slice','t116Slice');
slice=once(slice,'let sampled=0;','const grid=t116Grid(sb,plan.cold);let sampled=0;');
slice=once(slice,'hashQuery(s,r,','grid.walk(grid,s,r,');
slice=once(slice,'sb.state[id]=1;t108Add(p,id);','sb.state[id]=1;t116Remove(grid,id);t108Add(p,id);');
let chr=section(replay,'function t100ReplayActive(','function t100FullStepActive(').replace('t100ReplayActive','t116Chronological');
chr=once(chr,'const data=frame.values;','const grid=t116Grid(sb,null),data=frame.values;');
chr=once(chr,'hashQuery(s,r,','grid.walk(grid,s,r,');
chr=once(chr,'sb.state[i]=1; sb.burning.push(i);','sb.state[i]=1; t116Remove(grid,i); sb.burning.push(i);');
let site=section(temporal,'function t114Sitewise(','function t114Repair(').replace('t114Sitewise','t116Sitewise');
site=once(site,'const start=performance.now(),graph','const grid=t116Grid(sb,null),start=performance.now(),graph');
site=once(site,'hashQuery(pos,r,','grid.walk(grid,pos,r,');
site=once(site,'state=1;born[i]=frame+1;','state=1;t116Remove(grid,i);born[i]=frame+1;');
let solve=section(orig,'function t108Answer(','window.__t108=').replaceAll('t108Answer','t116Answer').replaceAll('t108Click(','t116ClickCore(')
 .replaceAll('t108Full(','t116Full(').replaceAll('t108Slice(','t116Slice(').replaceAll('t114Repair(','t116DispatchRepair(');
const root=await fs.readFile(path.join(here,'control.js'),'utf8');
const code=[grid,tracked,full,slice,chr,site,solve,root].join('\n');
new Script(code);await fs.mkdir(path.join(here,'local'),{recursive:true});
await fs.writeFile(path.join(here,'local/plugin.js'),code);
console.log(sha(code));
