// Untimed, closures inside the frozen native demo. No T119 kernel is changed.
window.__t121 = {
  parent(dt) {
    const saved=t90Fork();
    try {
      const before=t108Fingerprint();
      updateCam(cv.width/Math.max(1,cv.height));simTime+=dt;
      stepAll(dt);researchFrame++;
      return {before,successor:t108Fingerprint()};
    } finally {t90Restore(saved);}
  },
  physical(dt,pick,frames) {
    const results={};
    __t98.resetTrial();
    try {
      __t86.ignite(pick,true);
      for(const frame of [...new Set(frames)].sort((a,b)=>a-b)) {
        __t86.frames(frame,dt);
        results[researchFrame]=t108Fingerprint();
      }
      return results;
    } finally {__t98.finishTrial();}
  }
};
