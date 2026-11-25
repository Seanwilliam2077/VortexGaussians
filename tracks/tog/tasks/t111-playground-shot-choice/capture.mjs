// Reuse the validated two-sibling native observer; only the asset location and study receipt differ.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const here=path.dirname(fileURLToPath(import.meta.url));
let text=await fs.readFile(path.join(here,'../t109-common-parent-choice/capture.mjs'),'utf8');
assert.equal(createHash('sha256').update(text).digest('hex'),'35726e0159070e731546c9727fcce25853d50166cfe5d74098b14877f7a33c97');
text=text.replace('fileURLToPath(import.meta.url)',JSON.stringify(fileURLToPath(import.meta.url)))
         .replace('JSON.stringify(import.meta.url)',JSON.stringify(JSON.stringify(import.meta.url)))
         .replace('t109-sibling-native-v1','t111-playground-sibling-native-v1');
process.env.T86_PLY=path.resolve(here,'../t101-playground-holdout/local/scene.ply');
await import('data:text/javascript;base64,'+Buffer.from(text).toString('base64'));
