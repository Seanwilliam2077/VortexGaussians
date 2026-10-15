import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {NEW_ARM,SHARED_ARM,REFERENCE_ID,INHERITED_IDS,SOURCE_FILES,PARENT_ARCHIVE_SHA256} from './design.mjs';
import {verifyFile,ParentEvidenceError,qualityDecision,screenDecision,sameHashes} from './run.mjs';
const HERE=path.dirname(fileURLToPath(import.meta.url)),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
test('new plan contains exactly the fixed proxy32 arm and fourteen authenticated source dependencies',()=>{
 assert.deepEqual(NEW_ARM,{id:'dev-proxy32-r120',n:32,rate:120,role:'proxy'});assert.equal(SHARED_ARM.id,'dev-shared64-r120');assert.equal(REFERENCE_ID,'dev-ref256-r480');assert.deepEqual(INHERITED_IDS,[REFERENCE_ID,SHARED_ARM.id]);assert.equal(SOURCE_FILES.length,14);assert.equal(new Set(SOURCE_FILES).size,14);
});
test('all eight imported parent source files exactly match immutable archive pins',()=>{
 const pins=JSON.parse(fs.readFileSync(path.join(HERE,'baseline-pins.json'),'utf8'));assert.equal(pins.archive.sha256,PARENT_ARCHIVE_SHA256);assert.equal(pins.archive.members,34);assert.equal(pins.files.length,8);assert.equal(Object.keys(pins.sourceHashes).length,8);
 for(const [file,hash] of Object.entries(pins.sourceHashes))assert.equal(sha(fs.readFileSync(path.join(HERE,'p7-frozen',file))),hash);
});
test('proxy quality failure skips timing; inherited shared failure is an evidence error',()=>{
 const good={valid:true,primary:{panel:.001,regional:.002,display:.019}},bad={valid:true,primary:{panel:.001,regional:.002,display:.020001}};
 assert.equal(qualityDecision(good,bad).decision,'PROXY32_QUALITY_STOP');assert.equal(qualityDecision(good,bad).timingAllowed,false);assert.equal(qualityDecision(good,good).timingAllowed,true);assert.throws(()=>qualityDecision(bad,good),ParentEvidenceError);
});
test('cost and memory gate preserve old rules and produce explicitly follow-up decisions',()=>{
 const blocks=Array.from({length:6},()=>({shared:100,proxy:79})),memory={shared:{persistentBytes:395520,maximumAlgorithmOwnedArrayBytes:1000000,packedSurfacePositionBytes:196608,packedPositionBytes:197376},proxy:{persistentBytes:166912,maximumAlgorithmOwnedArrayBytes:500000}};
 assert.equal(screenDecision(blocks,memory).decision,'PROXY32_STRICT_FOLLOWUP_SCREEN');const slower=blocks.map(b=>({...b,proxy:90}));assert.equal(screenDecision(slower,memory).decision,'QUALITY_PASS_NO_STRICT_DOMINANCE');const larger=structuredClone(memory);larger.proxy.persistentBytes=200000;assert.equal(screenDecision(blocks,larger).screen.memoryPassed,false);
});
test('parent dependency authentication rejects same-size tampering, truncation and missing files',async()=>{
 const dir=fs.mkdtempSync(path.join(HERE,'.pin-test-')),file=path.join(dir,'tiny'),bytes=Buffer.from('frozen');
 try{fs.writeFileSync(file,bytes);const pin={path:'tiny',bytes:bytes.length,sha256:sha(bytes)};assert.equal((await verifyFile(file,pin)).sha256,pin.sha256);fs.writeFileSync(file,'broken');await assert.rejects(verifyFile(file,pin),ParentEvidenceError);fs.writeFileSync(file,'x');await assert.rejects(verifyFile(file,pin),ParentEvidenceError);await assert.rejects(verifyFile(path.join(dir,'missing'),pin),ParentEvidenceError);}
 finally{if(path.dirname(dir)!==HERE||!path.basename(dir).startsWith('.pin-test-'))throw new Error('unsafe test cleanup');fs.rmSync(dir,{recursive:true});}
 assert.ok(sameHashes({a:'1',b:'2'},{b:'2',a:'1'}));assert.ok(!sameHashes({a:'1'},{a:'2'}));
});
