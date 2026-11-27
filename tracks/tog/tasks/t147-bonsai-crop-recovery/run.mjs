import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {registerHooks} from 'node:module';

const here=new URL('../t145-bonsai-crop-choice/',import.meta.url);
const runner=new URL('run.mjs',here), observer=new URL('crop.mjs',here);
const oldGuard=`if(active || !bounds || owner!==t141Weights || !P.faithful || P.bloom!==0 || P.exposure!==1 ||
       !P.paused || researchP3State || FBW!==cv.width || FBH!==cv.height)throw Error('ROI preconditions changed');`;
const newGuard=`const checks={noActive:!active, bounds:!!bounds, sameTarget:owner===t141Weights,
      faithful:!!P.faithful, zeroBloom:P.bloom===0, unitExposure:P.exposure===1,
      embed:EMBED, normalRenderer:!researchP3State, sameWidth:FBW===cv.width, sameHeight:FBH===cv.height};
    for(const [name,ok] of Object.entries(checks))if(!ok)throw Error('ROI precondition failed: '+name);`;

function replaceOnce(source,oldText,newText) {
  assert.equal(source.split(oldText).length,2,oldText);
  return source.replace(oldText,()=>newText);
}
const sources=new Map();
for(const file of [runner,observer]){
  const source=readFileSync(file,'utf8').replaceAll('\r\n','\n');
  sources.set(file.href,file===observer
    ?replaceOnce(source,oldGuard,newGuard)
    :replaceOnce(source,'t145-bonsai-scalar-scissor-v1','t147-bonsai-embedded-scalar-scissor-v1'));
}
const hook=registerHooks({load(url,context,next){
  return sources.has(url)?{format:'module',source:sources.get(url),shortCircuit:true}:next(url,context);
}});
try {await import(runner.href);} finally {hook.deregister();}
