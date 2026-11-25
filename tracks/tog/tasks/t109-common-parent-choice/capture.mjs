// The production solver, original T86 observer and pinned global admission operator are identical.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
let src=await readFile(path.join(here,'../t92-transfer-workload/capture.mjs'),'utf8');
assert.equal(createHash('sha256').update(src).digest('hex'),'39fabb977f259c590d5b272869efcc8df8e08dc7e593295a39045dd31f938318');
function change(a,b){assert.equal(src.split(a).length,2,a);src=src.replace(a,()=>b);}
change("'../../../../research/lib/runtime.mjs'",JSON.stringify(pathToFileURL(path.resolve(here,'../../../../research/lib/runtime.mjs')).href));
src=src.replaceAll('import.meta.url',JSON.stringify(import.meta.url));
change("path.join(here,'local/scene.ply')","(process.env.T86_PLY||path.resolve(root,'../real-asset-ingest/foreground.ply'))");
change("schema:'t92-transfer-native-v1'","schema:'t109-sibling-native-v1'");
change("for(const arm of ['AB','BA'])","for(const arm of ['AL','AF'])");
change("await fs.mkdir(path.join(out,'checkpoints'));","");
change("        await packed('checkpoints/'+file,cut);","");
change("file:'checkpoints/'+file,","");
await import('data:text/javascript;base64,'+Buffer.from(src).toString('base64'));
