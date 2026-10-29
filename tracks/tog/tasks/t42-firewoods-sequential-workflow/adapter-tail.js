// Inspection and camera dispatch only; existing dynamics are unchanged.
const t42NativeUpdateCam=updateCam;
updateCam=function(aspect){
  if(staticSourceCamera) return staticUpdateCam();
  return t42NativeUpdateCam(aspect);
};
window.__t42={
  camera(c){staticSourceCamera=c;updateCam(cv.width/cv.height);},
  state(){
    const s=researchSnapshot({detail:true});
    return {...s,frontier:sceneBurnState.burning.slice(),emitCursor:sceneBurnState.emitCursor,
      sceneInfo:{center:sceneInfo.center.slice(),extent:sceneInfo.extent},
      camera:JSON.parse(JSON.stringify(cam)),buffer:[gl.drawingBufferWidth,gl.drawingBufferHeight],
      glError:gl.getError(),contextLost:gl.isContextLost()};
  },
  canvas(){return cv.toDataURL('image/png');},
  renderCount(){return lastCount;}
};
