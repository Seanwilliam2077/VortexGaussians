import assert from 'node:assert/strict';

// Inject this function in the demo closure, where it can draw ranges from the
// unmodified native scene VBO using the camera uniforms installed by render().
function installPickAudit() {
  function require(ok, reason) {
    if (!ok) throw Error(reason);
  }

  window.__pickAudit = {
    capture({width, height, sites, samples}) {
      require(P.paused && P.sceneOn && P.sceneSorted && !P.sceneDepthTest && !P.sceneBackdrop &&
        !P.box && !P.embers && extCBF && !researchP3State && !window.__nativeMatte?.bits, 'Pick audit needs a normal sorted rest view');
      require(sceneGauss.length === sites && FBW === width && FBH === height &&
        cv.width === width && cv.height === height && HDR_IFMT === gl.RGBA16F, 'Native pick material/viewport/precision mismatch');
      require(!sceneBurnState || (!sceneBurnState.glow.some(v => v !== 0) && !sceneBurnState.char_.some(v => v !== 0)),
        'Pick geometry must precede treatment');
      const timeBefore = simTime;
      const start = performance.now();
      const dynamic = render();
      require(!gl.getError() && !gl.isContextLost(), 'Native rest draw failed');
      const originalId = i => sceneData[i * SC_STRIDE_F + 24];
      const wanted = new Set(samples.map(s => s.id));
      const ranks = new Map();
      for (let i = 0; i < sites; i++) {
        const id = originalId(i);
        if (wanted.has(id)) {
          require(!ranks.has(id), 'Repeated native original ID');
          ranks.set(id, i);
        }
      }
      require(ranks.size === wanted.size, 'Expected source ID absent from sorted native VBO');

      const query = name => gl.getParameter(name);
      const prev = {read:query(gl.READ_FRAMEBUFFER_BINDING), draw:query(gl.DRAW_FRAMEBUFFER_BINDING),
        program:query(gl.CURRENT_PROGRAM), vao:query(gl.VERTEX_ARRAY_BINDING), buffer:query(gl.ARRAY_BUFFER_BINDING),
        viewport:query(gl.VIEWPORT), scissor:query(gl.SCISSOR_BOX), scissorOn:gl.isEnabled(gl.SCISSOR_TEST),
        blend:gl.isEnabled(gl.BLEND), depth:gl.isEnabled(gl.DEPTH_TEST), mask:query(gl.COLOR_WRITEMASK),
        srcRGB:query(gl.BLEND_SRC_RGB), dstRGB:query(gl.BLEND_DST_RGB),
        srcAlpha:query(gl.BLEND_SRC_ALPHA), dstAlpha:query(gl.BLEND_DST_ALPHA),
        rgbEquation:query(gl.BLEND_EQUATION_RGB), alphaEquation:query(gl.BLEND_EQUATION_ALPHA),
        activeTex:query(gl.ACTIVE_TEXTURE)};
      gl.activeTexture(gl.TEXTURE0);
      const prevTexture = query(gl.TEXTURE_BINDING_2D);
      const scratch = gl.createTexture(), fbo = gl.createFramebuffer();
      const pixel = new Float32Array(4);
      const clear = new Float32Array(4);
      const read = (x,y) => {
        gl.readPixels(x,y,1,1,gl.RGBA,gl.FLOAT,pixel);
        const value = pixel[3];
        require(!gl.getError() && Number.isFinite(value) && value >= 0 && value <= 1, 'Invalid native alpha');
        return value;
      };
      const setAlpha = alpha => {
        clear[3] = alpha;
        gl.clearBufferfv(gl.COLOR,0,clear);
      };
      const enableWhen = (flag,on) => on ? gl.enable(flag) : gl.disable(flag);
      try {
        gl.bindFramebuffer(gl.FRAMEBUFFER,sceneFBO);
        const originalAlphas = samples.map(s => read(s.x,height-1-s.y));
        gl.bindTexture(gl.TEXTURE_2D,scratch);
        gl.texStorage2D(gl.TEXTURE_2D,1,HDR_IFMT,width,height);
        gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
        gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
        gl.bindFramebuffer(gl.FRAMEBUFFER,fbo);
        gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,scratch,0);
        require(gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE, 'Incomplete native-format pick target');
        gl.bindTexture(gl.TEXTURE_2D,prevTexture);
        gl.viewport(0,0,width,height);
        gl.enable(gl.SCISSOR_TEST);
        gl.disable(gl.DEPTH_TEST);
        gl.enable(gl.BLEND);
        gl.blendEquation(gl.FUNC_ADD);
        gl.blendFunc(gl.ONE_MINUS_DST_ALPHA,gl.ONE);
        gl.colorMask(true,true,true,true);
        gl.useProgram(pScene);
        const results = samples.map((s,n) => {
          const x=s.x, y=height-1-s.y, rank=ranks.get(s.id);
          gl.scissor(x,y,1,1);
          setAlpha(0);
          drawSceneRange(0,rank);
          const before=read(x,y);
          drawSceneRange(rank,1);
          const through=read(x,y);
          drawSceneRange(rank+1,sites-rank-1);
          const full=read(x,y);
          require(before <= through && through <= full, 'Nonmonotone native prefix');
          const fullMatches = full === originalAlphas[n];
          require(dynamic !== 0 || fullMatches, 'Static full draw disagrees with native scene alpha');
          let actual=null, searchReads=0;
          if (before < 0.5 && through >= 0.5) {
            actual={id:s.id, sortedIndex:rank, before, through};
          } else if (full >= 0.5) {
            // Search prefix lengths. Reinstall the exact read-back half-float
            // destination alpha at the known lower bound; RGB never feeds alpha.
            let lo=before >= 0.5 ? 0 : rank+1, hi=before >= 0.5 ? rank : sites;
            let lowAlpha=lo === 0 ? 0 : through;
            while (hi-lo > 1) {
              const mid=lo+Math.floor((hi-lo)/2);
              setAlpha(lowAlpha);
              drawSceneRange(lo,mid-lo);
              const test=read(x,y);
              searchReads++;
              require(test >= lowAlpha, 'Nonmonotone prefix search');
              if (test >= 0.5) hi=mid;
              else { lo=mid; lowAlpha=test; }
            }
            setAlpha(lowAlpha);
            drawSceneRange(lo,1);
            const upper=read(x,y);
            require(lowAlpha < 0.5 && upper >= 0.5, 'Cannot bracket first actual crossing');
            actual={id:originalId(lo), sortedIndex:lo, before:lowAlpha, through:upper};
          }
          return {displayPixel:[x,s.y],glPixel:[x,y],expectedSourceId:s.id,expectedSortedIndex:rank,
            expectedBefore:before,expectedThrough:through,actual,matched:actual?.id===s.id,
            fullStaticAlpha:full,originalSceneAlpha:originalAlphas[n],fullMatches,searchReads};
        });
        require(timeBefore === simTime && !gl.isContextLost(), 'Pick draw advanced time or lost its device');
        return {sites,width,height,nativeBuckets:SCENE_BUCKETS,format:'RGBA16F',threshold:0.5,
          sourceCameraId:staticSourceCamera?.id,clock:simTime,dynamicInstancesInNormalDraw:dynamic,
          elapsedMs:performance.now()-start,samples:results};
      } finally {
        gl.bindFramebuffer(gl.READ_FRAMEBUFFER,prev.read);
        gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER,prev.draw);
        gl.bindTexture(gl.TEXTURE_2D,prevTexture);
        gl.deleteFramebuffer(fbo); gl.deleteTexture(scratch);
        gl.activeTexture(prev.activeTex);
        gl.bindVertexArray(prev.vao); gl.bindBuffer(gl.ARRAY_BUFFER,prev.buffer);
        gl.useProgram(prev.program); gl.viewport(...prev.viewport); gl.scissor(...prev.scissor);
        gl.blendEquationSeparate(prev.rgbEquation,prev.alphaEquation);
        gl.blendFuncSeparate(prev.srcRGB,prev.dstRGB,prev.srcAlpha,prev.dstAlpha);
        gl.colorMask(...prev.mask);
        enableWhen(gl.SCISSOR_TEST,prev.scissorOn); enableWhen(gl.BLEND,prev.blend); enableWhen(gl.DEPTH_TEST,prev.depth);
      }
    }
  };
}

export function instrumentPickAudit(html) {
  const marker='window.__demo = {';
  assert.equal(html.split(marker).length,2,'Native demo instrumentation marker');
  return html.replace(marker, () => '(' + installPickAudit.toString() + ')();\n'+marker);
}

export async function auditPickPixels(page,primaryCamera,t139Results) {
  const [width,height]=t139Results.view_size;
  const samples=t139Results.nearest_pixel_diagnostic.map(s => {
    const [x,y]=s.display_pixel_center_xy;
    assert.ok(Number.isInteger(x) && Number.isInteger(y) && x>=0 && x<width && y>=0 && y<height);
    assert.equal(s.full.id,s.fp16.id);
    return {x,y,id:s.fp16.id};
  });
  assert.deepEqual(samples.map(s=>s.id),[205385,340163]);
  assert.deepEqual(samples.map(s=>[s.x,s.y]),[[670,519],[779,519]]);
  const args={width,height,sites:t139Results.source_rows,samples};
  return page.evaluate(({camera,args})=>{
    window.__t42.camera(camera);
    return window.__pickAudit.capture(args);
  },{camera:primaryCamera,args});
}
