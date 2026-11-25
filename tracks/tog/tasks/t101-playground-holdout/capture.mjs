// Run the pinned T92 observer with the independent recipe/asset. Retain native event and checkpoint hashes.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
let source=await readFile(path.join(here,'../t92-transfer-workload/capture.mjs'),'utf8');
assert.equal(createHash('sha256').update(source).digest('hex'),'39fabb977f259c590d5b272869efcc8df8e08dc7e593295a39045dd31f938318');
function change(from,to){
  assert.equal(source.split(from).length,2);
  source=source.replace(from,()=>to);
}
change("'../../../../research/lib/runtime.mjs'",JSON.stringify(pathToFileURL(path.resolve(here,'../../../../research/lib/runtime.mjs')).href));
source=source.replaceAll('import.meta.url',JSON.stringify(import.meta.url));
change("schema:'t92-transfer-native-v1'", "schema:'t101-playground-native-v1'");
change("await fs.mkdir(path.join(out,'checkpoints'));","");
change("        await packed('checkpoints/'+file,cut);","");
change("file:'checkpoints/'+file,","");
// All original native state, geometric stroke, counter and label assertions remain in force.
await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
