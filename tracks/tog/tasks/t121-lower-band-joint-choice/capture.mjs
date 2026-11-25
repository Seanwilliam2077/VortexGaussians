// The independent observer uses none of the three candidate calculation paths.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const self=fileURLToPath(import.meta.url), here=path.dirname(self);
let text=await fs.readFile(path.join(here,'../t109-common-parent-choice/capture.mjs'),'utf8');
assert.equal(createHash('sha256').update(text).digest('hex'),'35726e0159070e731546c9727fcce25853d50166cfe5d74098b14877f7a33c97');
text=text.replace('fileURLToPath(import.meta.url)',JSON.stringify(self))
  .replace('JSON.stringify(import.meta.url)',JSON.stringify(JSON.stringify(import.meta.url)))
  .replace('t109-sibling-native-v1','t121-lower-band-independent-native-v1');
process.env.T86_PLY=path.join(here,'../t101-playground-holdout/local/scene.ply');
process.argv[2]=path.resolve(process.argv[2]||path.join(here,'evidence/native'));
await import('data:text/javascript;base64,'+Buffer.from(text).toString('base64'));
