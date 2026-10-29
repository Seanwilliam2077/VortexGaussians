// Diagnostic-only closure extension. No simulation steps or ignition.
let staticSourceCamera = null;
function staticUpdateCam() {
  const c = staticSourceCamera, R = c.rotation;
  const cy=Math.cos(P.sceneYaw), sy=Math.sin(P.sceneYaw);
  const cp=Math.cos(P.scenePitch), sp=Math.sin(P.scenePitch);
  const Q=[[cy,sy*sp,sy*cp],[0,cp,-sp],[-sy,cy*sp,cy*cp]];
  const eye=srcToWorld(c.position), signs=[1,-1,-1];
  // Rows of D R^T Q^T. JSON R is camera-to-world with right/down/forward axes.
  const A=Array.from({length:3},(_,i)=>Array.from({length:3},(_,j)=>
    signs[i]*R.reduce((sum,row,k)=>sum+row[i]*Q[j][k],0)));
  const V=[A[0][0],A[1][0],A[2][0],0,A[0][1],A[1][1],A[2][1],0,
    A[0][2],A[1][2],A[2][2],0,
    ...A.map(row=>-row.reduce((sum,v,k)=>sum+v*eye[k],0)),1];
  const near=.05,far=50,nf=1/(near-far);
  const fx=c.fx*cv.width/c.width,fy=c.fy*cv.height/c.height;
  const projection=[2*fx/cv.width,0,0,0,0,2*fy/cv.height,0,0,
    0,0,(far+near)*nf,-1,0,0,2*far*near*nf,0];
  cam.eye=eye; cam.V=V; cam.VP=m4Mul(projection,V); cam.focal=[fx,fy];
  cam.bx=A[0].slice(); cam.by=A[1].slice(); cam.fh=A[2].map(v=>-v);
  const f=m4Apply(cam.VP,0,.06,0);cam.fireUV=[f[0]*.5+.5,f[1]*.5+.5];
}
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
