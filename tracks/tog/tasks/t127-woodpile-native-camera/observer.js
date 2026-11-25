// Injected beside the pinned native diagnostics. Only drawPartRange uses this flag.
let t127Drawing=null;
window.__t127={
  fingerprint:t108Fingerprint,
  backend(){
    const e=gl.getExtension('WEBGL_debug_renderer_info');
    return {vendor:gl.getParameter(e?e.UNMASKED_VENDOR_WEBGL:gl.VENDOR),
      renderer:gl.getParameter(e?e.UNMASKED_RENDERER_WEBGL:gl.RENDERER)};
  },
  draw(camera,wood){
    if(!P.paused || P.box || P.embers || !P.sceneOn || !P.sceneSorted || P.sceneBackdrop || P.sceneDepthTest ||
       P.dimMode!=='layer' || P.sliceMode!=='world' || !P.faithful || P.bloom!==0 || P.exposure!==1)
      throw Error('Unexpected native display path');
    const before=t108Fingerprint();
    __t42.camera(camera);
    t127Drawing={wood,instances:0};
    try{
      const total=render(), png=__t42.canvas(), after=t108Fingerprint();
      return {png,total,dynamic_instances:t127Drawing.instances,before,after,
        size:[gl.drawingBufferWidth,gl.drawingBufferHeight],error:gl.getError(),lost:gl.isContextLost()};
    }finally{t127Drawing=null;}
  }
};
