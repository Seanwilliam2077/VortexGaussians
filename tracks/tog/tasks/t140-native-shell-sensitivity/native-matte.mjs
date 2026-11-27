import assert from 'node:assert/strict';

// Install inside the original demo closure; retain normal appearance outside the call.
function install() {
  let bits = null;
  let suppressed = 0;
  const mode = gl.getUniformLocation(pScene, 'uNativeTag');
  if (mode === null) throw Error('Missing native tag uniform');
  function encode(array) {
    const bytes = new Uint8Array(array.buffer);
    let chunks = [];
    for (let i = 0; i < bytes.length; i += 16384) {
      chunks.push(String.fromCharCode(...bytes.subarray(i, i + 16384)));
    }
    return btoa(chunks.join(''));
  }
  function captureArrays(ids, {block = 2} = {}) {
    if (bits || !P.paused || !P.sceneOn || !P.sceneSorted || P.sceneDepthTest || P.sceneBackdrop ||
        P.box || P.embers || !extCBF || (block !== 1 && block !== 2)) throw Error('Invalid native matte draw setup');
    if (sceneBurnState && (sceneBurnState.char_.some(v => v !== 0) || sceneBurnState.glow.some(v => v !== 0))) {
      throw Error('Capture shell in the untreated rest state');
    }
    const mask = new Uint8Array(sceneGauss.length);
    for (const id of ids) {
      if (!Number.isInteger(id) || id < 0 || id >= mask.length || mask[id]) throw Error('Duplicate or invalid splat ID');
      mask[id] = 1;
    }
    const clock = simTime;
    suppressed = 0;
    bits = mask;
    try {
      const dynamic = render();
      gl.bindFramebuffer(gl.FRAMEBUFFER, sceneFBO);
      if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE || FBW % block || FBH % block ||
          FBW !== cv.width || FBH !== cv.height || clock !== simTime || dynamic !== suppressed) throw Error('Draw contract');
      const rgba = new Float32Array(FBW * FBH * 4);
      gl.readPixels(0, 0, FBW, FBH, gl.RGBA, gl.FLOAT, rgba);
      if (gl.getError() || gl.isContextLost()) throw Error('Floating-point native readback failed');
      const width = FBW / block, height = FBH / block;
      const eligible = new Float32Array(width * height), all = new Float32Array(width * height);
      let greenAlpha = 0, complementError = 0, exceed = 0, total = 0, tagged = 0;
      for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
        let redSum = 0, greenSum = 0;
        for (let dy = 0; dy < block; dy++) for (let dx = 0; dx < block; dx++) {
          const i = 4 * ((FBH - 1 - (block * y + dy)) * FBW + block * x + dx);
          const red = rgba[i], green = rgba[i+1], blue = rgba[i+2], alpha = rgba[i+3];
          if (!Number.isFinite(red+green+blue+alpha) || Math.min(red,green,blue,alpha) < 0 ||
              Math.max(red,green,blue,alpha) > 1.004) throw Error('Nonphysical native matte');
          greenAlpha = Math.max(greenAlpha, Math.abs(green-alpha));
          complementError = Math.max(complementError, Math.abs(red+blue-green));
          exceed = Math.max(exceed, red-green, blue-green);
          redSum += red;
          greenSum += green;
        }
        const index = y * width + x;
        eligible[index] = redSum / (block * block);
        all[index] = greenSum / (block * block);
        tagged += eligible[index];
        total += all[index];
      }
      if (!(total > 0) || greenAlpha > 0.004 || exceed > 0.004) throw Error('Tagged versus total opacity check failed');
      return {width, height, block, eligible, all, stats: {sites:mask.length, tagCount:ids.length, dynamic, suppressed,
        sourceWidth:FBW, sourceHeight:FBH, greenAlpha, complementError, exceed, total, tagged, clock}};
    } finally {
      bits = null;
      gl.useProgram(pScene);
      gl.uniform1i(mode, 0);
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    }
  }
  window.__nativeMatte = {
    captureArrays,
    capture(ids, options) {
      const result = captureArrays(ids, options);
      return {...result, eligible:encode(result.eligible), all:encode(result.all)};
    },
    get bits() {return bits;},
    setDrawMode() {gl.uniform1i(mode, bits ? 1 : 0);},
    suppress(count) {if (bits) suppressed += count; return bits !== null;}
  };
}

export function instrumentNativeMatte(input) {
  let html = input;
  function change(original, replacement) {
    assert.equal(html.split(original).length, 2, original);
    html = html.replace(original, () => replacement);
  }
  change('out vec2 v_uv; out vec3 v_color; out float v_opa; out float v_glow;',
    'uniform bool uNativeTag; out vec2 v_uv; out vec3 v_color; out float v_opa; out float v_glow;');
  change('uniform float uTime; uniform float uDepthPre;', 'uniform bool uNativeTag; uniform float uTime; uniform float uDepthPre;');
  change('v_color = mix(base, sooted, aChar)*uSceneLight;', 'v_color = uNativeTag ? aColor : mix(base, sooted, aChar)*uSceneLight;');
  change('o=vec4(v_color*a + ember, a);', 'o=vec4(v_color*a + (uNativeTag ? vec3(0.0) : ember), a);');
  const color = 'arr[o++]=g.c[0]; arr[o++]=g.c[1]; arr[o++]=g.c[2];';
  change(color, 'if(window.__nativeMatte?.bits){ const tag=window.__nativeMatte.bits[bi]; arr[o++]=tag; arr[o++]=1; arr[o++]=1-tag; }else{' + color + '}');
  const uniforms = 'gl.uniformMatrix4fv(uScene.VP, false, cam.VP); gl.uniform1f(uScene.Light, P.sceneLight);';
  change(uniforms, uniforms + 'window.__nativeMatte?.setDrawMode();');
  const particles = 'function drawPartRange(start,count){ if(count<=0) return;';
  change(particles, particles + ' if(window.__nativeMatte?.suppress(count)) return;');
  change('window.__demo = {', '(' + install.toString() + ')();\nwindow.__demo = {');
  return html;
}
