/* Purely inserted into demo/index.html's IIFE by assemble-source.mjs.
 * Installation does not step the solver. Only advanceTo() does so after load.
 */
(() => {
  'use strict';
  const SOURCE_SHA256 = 'e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0';
  const SEED = 12345, FPS = 24, DT = 1 / FPS, MAX_SECONDS = 58;
  const overrides = Object.freeze({
    solver: 'vpm', dimMode: 'layer', layers: 9, simLayers: 9, ppl: 160,
    mode: 'fire', paused: true, orbit: false, sliceMode: 'world', sliceDepth: 0.7,
    sceneOn: false, spreadOn: false, emitterOn: true, embers: false,
    box: false, filament: false
  });
  const state = { version: 1, ready: false, error: null, api: null };
  Object.defineProperty(window, '__a52FireBridge', { value: state });

  // The original embed listener remains in the copied source. A52 has a direct
  // synchronous API, so its legacy tick/reset/set messages must not be drivers.
  window.addEventListener('message', event => {
    if (event.source === window.parent && ['tick', 'reset', 'set'].includes(event.data?.t))
      event.stopImmediatePropagation();
  }, true);

  window.addEventListener('load', () => {
    try {
      if (!EMBED) throw new Error('A52 source requires ?embed=1');
      const initStarted = performance.now();
      Object.assign(P, RESEARCH_DEFAULTS, overrides);
      pointer.active = false;
      resetSim(SEED);
      resetSpreadCounters();
      const expectedP = { ...P };
      let frame = 0, requestedSeconds = 0, disposed = false;
      let advanceCalls = 0, readCalls = 0, stepMs = 0, readMs = 0, peakParticles = 0;
      const initializationMs = performance.now() - initStarted;
      const active = () => {
        if (disposed) throw new Error('A52 fire source is disposed');
        for (const key of Object.keys(expectedP)) {
          if (!Object.is(P[key], expectedP[key])) throw new Error('A52 fixed parameter changed: ' + key);
        }
        if (pointer.active) throw new Error('A52 source pointer became active');
      };
      const currentCount = () => layers.reduce((sum, layer) => sum + layer.ps.length, 0);
      function advanceTo(seconds) {
        active();
        if (!Number.isFinite(seconds) || seconds < 0 || seconds > MAX_SECONDS)
          throw new RangeError('A52 source time must be finite and in [0, 58]');
        if (seconds + 1e-9 < requestedSeconds)
          throw new RangeError('A52 source time must be monotonic');
        requestedSeconds = Math.max(requestedSeconds, seconds);
        const target = Math.min(MAX_SECONDS * FPS, Math.floor(seconds * FPS + 1e-8));
        advanceCalls++;
        const started = performance.now();
        while (frame < target) {
          // Same original call path as __demo.step(1, 1/24). stepAll itself uses
          // two VPM substeps because 1/24 > 1/45; do not replace that behavior.
          simTime += DT;
          stepAll(DT);
          frame++;
          peakParticles = Math.max(peakParticles, currentCount());
        }
        stepMs += performance.now() - started;
        return { frame, seconds: frame / FPS, particles: currentCount() };
      }
      function read() {
        active();
        const started = performance.now(), points = [], n = layers.length;
        for (let k = 0; k < n; k++) {
          // Exact depth convention of original gather() in world-fixed mode.
          const z = (n > 1 ? k / (n - 1) - 0.5 : 0) * P.sliceDepth;
          for (const p of layers[k].ps) {
            const radius = P.rad / 360 * (0.55 + 0.7 * p.d) *
              (1 + 0.5 * (1 - Math.min(1, p.T)));
            const point = { x: p.x, y: p.y, z, temperature: p.T, density: p.d, radius };
            if (!Object.values(point).every(Number.isFinite))
              throw new Error('A52 source contains a non-finite particle');
            points.push(point); // Copies; callers cannot edit the source particles.
          }
        }
        readCalls++;
        readMs += performance.now() - started;
        return points;
      }
      function summary() {
        active();
        const count = currentCount(), layerCounts = layers.map(layer => layer.ps.length);
        const ranges = { x: [Infinity, -Infinity], y: [Infinity, -Infinity],
          temperature: [Infinity, -Infinity], density: [Infinity, -Infinity] };
        for (const layer of layers) for (const p of layer.ps) {
          for (const [key, value] of [['x', p.x], ['y', p.y], ['temperature', p.T], ['density', p.d]]) {
            ranges[key][0] = Math.min(ranges[key][0], value);
            ranges[key][1] = Math.max(ranges[key][1], value);
          }
        }
        return {
          version: 1, source: 'demo/index.html', sourceSha256: SOURCE_SHA256,
          seed: SEED, dt: DT, maxSeconds: MAX_SECONDS, frame,
          seconds: frame / FPS, requestedSeconds, originalSimTime: simTime,
          internalVpmSubsteps: vpmTick, particles: count, layerCounts,
          peakParticles, particleBudget: overrides.layers * overrides.ppl,
          emittedParticles: spreadCounters.baseParticlesEmitted,
          ranges: count ? { ...ranges, z: [-P.sliceDepth / 2, P.sliceDepth / 2] } : null,
          parameters: { baseline: 'RESEARCH_DEFAULTS at sourceSha256', overrides: { ...overrides },
            buoy: P.buoy, baro: P.baro, eps: P.eps, cool: P.cool, gam: P.gam,
            theta: P.theta, turb: P.turb, couple: P.couple, interZ: P.interZ,
            wind: P.wind, vpmVisc: P.vpmVisc, rad: P.rad, rate: P.rate },
          mapping: { coordinates: 'world-fixed planar layers; x=p.x, y=p.y, z=(k/(N-1)-0.5)*sliceDepth',
            temperature: 'p.T: rendered dimensionless temperature, not Tb or Kelvin',
            density: 'p.d: rendered density weight, not a calibrated mass density',
            radius: 'rad/360*(0.55+0.7*d)*(1+0.5*(1-min(1,T))); isotropic visual base size, not vortex core or covariance axes' },
          costs: { initializationMs, advanceCalls, readCalls, stepMs, readMs },
          automaticSimulation: false
        };
      }
      function dispose() { disposed = true; state.ready = false; }
      state.api = Object.freeze({ advanceTo, read, summary, dispose });
      state.ready = true;
    } catch (error) {
      state.error = String(error?.stack || error);
    }
  }, { once: true });
})();
