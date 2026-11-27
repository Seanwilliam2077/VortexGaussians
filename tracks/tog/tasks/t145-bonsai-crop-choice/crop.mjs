import assert from 'node:assert/strict';

function one(s,a,b) {assert.equal(s.split(a).length,2,a);return s.replace(a,()=>b);}

// The diagnostic supplies a zero bloom texture while preserving the original
// composite shader, including its screen-space dither and scene texture filter.
function scope145() {
  let enabled=false, active=null, emptyBloom=null, bounds=null, owner=null;
  const oracleCrops=new Map();
  let auditing=true;
  function setup(){
    if(!P.faithful || P.bloom!==0 || P.exposure!==1 || researchP3State || !P.sceneSorted ||
       P.sceneBackdrop || P.sceneDepthTest || FBW!==cv.width || FBH!==cv.height ||
       !t141Weights || gl.isEnabled(gl.SCISSOR_TEST))throw Error('Unsupported scalar ROI');
    const {indices,weights,total,box}=t141Weights;
    let sum=0;
    for(let i=0;i<indices.length;i++) {
      const p=indices[i]/4,x=p%box.w,y=Math.floor(p/box.w);
      if(x%2 || y%2 || x<0 || x+1>=box.w || y<0 || y+1>=box.h || !(weights[i]>0))throw Error('ROI omitted positive sample');
      sum+=weights[i];
    }
    if(sum!==total || indices.length!==weights.length)throw Error('Incomplete native target');
    const x=Math.max(0,box.x-1), y=Math.max(0,box.y-1);
    bounds=[x,y,Math.min(cv.width,box.x+box.w+1)-x,Math.min(cv.height,box.y+box.h+1)-y];
    owner=t141Weights;
    const old=gl.getParameter(gl.TEXTURE_BINDING_2D);
    emptyBloom=gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D,emptyBloom);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA8,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array(4));
    gl.bindTexture(gl.TEXTURE_2D,old);
    if(gl.getError()!==gl.NO_ERROR)throw Error('Zero bloom texture failed');
    return {crop:box,sceneScissor:bounds,targetCells:indices.length,total,viewport:[cv.width,cv.height]};
  }
  async function run(draw) {
    if(!enabled)return draw();
    if(active || !bounds || owner!==t141Weights || !P.faithful || P.bloom!==0 || P.exposure!==1 ||
       !P.paused || researchP3State || FBW!==cv.width || FBH!==cv.height)throw Error('ROI preconditions changed');
    const was=gl.isEnabled(gl.SCISSOR_TEST), previous=gl.getParameter(gl.SCISSOR_BOX);
    active={frame:researchFrame,time:simTime,scene:sceneGauss,burn:sceneBurnState,count:null,firstVP:null,draws:0};
    try {
      gl.enable(gl.SCISSOR_TEST);gl.scissor(...bounds);
      const value=await draw();
      if(active.draws!==2 || researchFrame!==active.frame || simTime!==active.time)throw Error('Incorrect ROI draw transaction');
      return value;
    } finally {
      active=null;gl.scissor(...previous);if(!was)gl.disable(gl.SCISSOR_TEST);
    }
  }
  function gatherStatic() {
    if(!active)return gatherScene();
    if(sceneGauss!==active.scene || sceneBurnState!==active.burn || researchFrame!==active.frame ||
       simTime!==active.time)throw Error('Static stream belongs to a different endpoint');
    active.draws++;
    if(active.draws===1 && !t141HideGas) {
      active.firstVP=Array.from(cam.VP);
      active.count=gatherScene();
    } else if(active.draws!==2 || !t141HideGas || active.count!==sceneGauss.length ||
              !active.firstVP.every((v,i)=>v===cam.VP[i]))throw Error('Endpoint/camera changed between paired draws');
    return active.count;
  }
  async function verifyPixels(branch, suppress, img) {
    if(!auditing)throw Error('Reference access in a measured call');
    const key=branch+':'+suppress;
    if(enabled){
      const original=oracleCrops.get(key);
      if(!original || original.length!==img.length)throw Error('Missing reference crop');
      for(let i=0;i<img.length;i++)if(img[i]!==original[i])throw Error('Full/crop byte mismatch '+key+' at '+i);
    } else {
      if(oracleCrops.has(key))throw Error('Duplicate original crop');
      oracleCrops.set(key,img.slice());
    }
    return digest141(img);
  }
  window.__t145={setup,run,gatherStatic,verifyPixels,
    get active(){return !!active;},get emptyBloom(){return emptyBloom;},get enabled(){return enabled;},
    enable(){enabled=true;},
    closeAudit(){if(oracleCrops.size!==4)throw Error('Missing oracle crops');oracleCrops.clear();auditing=false;}
  };
}

export function instrumentRenderer(html) {
  html=one(html,'const ns=gatherScene();','const ns=window.__t145 ? __t145.gatherStatic() : gatherScene();');
  html=one(html,'gl.viewport(0,0,BW,BH);','if(!window.__t145?.active){gl.viewport(0,0,BW,BH);');
  html=one(html,'// ---- 3) composite + ACES tonemap','}\n  // ---- 3) composite + ACES tonemap');
  html=one(html,'gl.bindTexture(gl.TEXTURE_2D,bloomA); gl.uniform1i(uComp.Bloom,1);',
    'gl.bindTexture(gl.TEXTURE_2D,window.__t145?.active ? __t145.emptyBloom : bloomA); gl.uniform1i(uComp.Bloom,1);');
  return one(html,'window.__demo = {','('+scope145.toString()+')();\nwindow.__demo = {');
}

export function instrumentAction(input) {
  let s=one(input,'async function image141(audit){','async function image141(audit,branch){');
  s=one(s,'const images=[], hashes=[];','const images=[], hashes=[], cropHashes=[];');
  s=one(s,'if(audit){\n        const full=', 'if(audit)cropHashes.push(await __t145.verifyPixels(branch,suppress,image));\n      if(audit && !__t145.enabled){\n        const full=');
  s=one(s,'passes:4*changed>=total,hashes','passes:4*changed>=total,hashes,cropHashes');
  return one(s,'const result=await image141(audit);','const result=await __t145.run(()=>image141(audit,name));');
}
