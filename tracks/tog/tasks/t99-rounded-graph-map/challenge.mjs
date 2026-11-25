import assert from 'node:assert/strict';
import {bits,value,serial,descriptor,lookup,presummed,width} from './operator.mjs';
let state=0xf123778, checks=0, fast=0, fallback=0, singleDiff=0, paritySensitive=0;
const random=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296;};
function check(h, ds){
  const w=bits(h), rule=descriptor(Math.floor(w/width),ds);
  const got=lookup(w,rule), trueWord=bits(serial(h,ds));
  if(got===null){fallback++;assert.equal(bits(serial(h,ds)),trueWord);}else{fast++;assert.equal(got,trueWord);}
  if(rule && rule.every(x=>x!==null) && rule[0]!==rule[1])paritySensitive++;
  if(bits(Math.fround(h+presummed(ds)))!==trueWord)singleDiff++;
  checks++;
}
// Exercise every normal binary exponent, denormals, the max finite input and overflow.
// Fl64(fl32 input + double delta) can land on an F32 midpoint even when the
// exact real sum was just to one side of it.
for(let e=1;e<255;e++){
  const base=e*width, unit=2**(e-127-23);
  for(const mant of [0,1,2,3,4,5,width/2,width-4,width-3,width-2,width-1]){
    const h=value(base+mant);
    for(const s of [.5,.5-2**-53,.5+2**-52,1.5,3.5,.125,0])
      check(h,[s*unit,.5*unit,1.5*unit,.5*unit]);
    check(h,[]);check(h,[unit]);
  }
}
for(const w of [0,1,2,width-1])for(const d of [0,2**-149,2**-150,1])check(value(w),[d,d,0]);
for(let n=0;n<20000;n++){
  const e=1+Math.floor(random()*254), base=e*width, unit=2**(e-150);
  const h=value(base+Math.floor(random()*width));
  const count=Math.floor(random()*25);
  const ds=Array.from({length:count},()=>random()<.5 ? unit*(Math.floor(random()*24)+.5) :
    unit*random()*2**Math.floor(random()*27));
  check(h,ds);
}
assert(fast>0 && fallback>0 && paritySensitive>0 && singleDiff>0);
console.log(JSON.stringify({checks,fast,fallback,singleDiff,paritySensitive},null,2));
