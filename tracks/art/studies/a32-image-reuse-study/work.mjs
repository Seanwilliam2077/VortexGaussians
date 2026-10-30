(() => {
  'use strict';

  const SOURCE_PATH = '../a25-public-request/inspection-01/04-request-returned.png';
  const CANVAS = Object.freeze({ x: 47, y: 296, width: 944, height: 471 });
  const CROP_HEIGHT = 214;
  const DURATION = 14000;
  const $ = (id) => document.getElementById(id);
  const stage = $('stage');
  const notice = $('notice');
  const paper = $('paper-stock');
  const slot = $('image-slot');
  const print = $('notice-print');
  const signatures = $('notice-signatures');
  const sourceWindow = $('source-window');
  const cropEdge = $('crop-edge');
  const request = $('request');
  const begin = $('begin');
  const pause = $('pause');
  const finish = $('finish');
  const status = $('status');
  const mobile = window.matchMedia('(max-width: 760px)');
  let sourceReady = false;
  let started = false;
  let running = false;
  let ended = false;
  let elapsedMs = 0;
  let lastTick = 0;
  let raf = 0;
  let loadError = null;
  let lastAction = 'load';
  let rendered = { cropHeight: CANVAS.height, cropProgress: 0, placement: 0, paperOpacity: 0, printOpacity: 0, signaturesOpacity: 0 };

  const clamp = (n) => Math.max(0, Math.min(1, n));
  const mix = (a, b, t) => a + (b - a) * t;
  const smooth = (t) => { const n = clamp(t); return n * n * (3 - 2 * n); };
  const segment = (from, to) => clamp((elapsedMs - from) / (to - from));
  const phase = () => ended ? 'ended' : !started ? 'ready' : elapsedMs < 3000 ? 'source' : elapsedMs < 7000 ? 'cropping' : elapsedMs < 11000 ? 'placing' : 'posted';

  // Spend most of the cut passing through the name row, rather than empty black.
  function cutHeight(t) {
    if (t <= .22) return mix(CANVAS.height, 340, smooth(t / .22));
    if (t <= .78) return mix(340, 222, smooth((t - .22) / .56));
    return mix(222, CROP_HEIGHT, smooth((t - .78) / .22));
  }

  function opacity(element, value) {
    element.style.opacity = String(value);
  }

  function render() {
    const cropProgress = segment(3000, 7000);
    const cropHeight = cutHeight(cropProgress);
    const placement = smooth(segment(7000, 11000));
    const paperOpacity = smooth(segment(7000, 8200));
    const printOpacity = smooth(segment(8200, 10300));
    const signaturesOpacity = smooth(segment(9500, 11000));
    const stageWidth = stage.clientWidth;
    const initialWidth = Math.min(CANVAS.width, stageWidth);
    const initialHeight = initialWidth * CANVAS.height / CANVAS.width;
    const paperWidth = notice.offsetWidth;
    const noticeLeft = (stageWidth - paperWidth) / 2;
    const initialX = (stageWidth - initialWidth) / 2 - noticeLeft;
    const initialY = (mobile.matches ? 24 : 80) - notice.offsetTop;
    const width = mix(initialWidth, slot.offsetWidth, placement);

    stage.style.height = mobile.matches
      ? `${mix(initialHeight + 48, notice.offsetHeight + 36, placement)}px`
      : '672px';
    sourceWindow.style.left = `${mix(initialX, slot.offsetLeft, placement)}px`;
    sourceWindow.style.top = `${mix(initialY, slot.offsetTop, placement)}px`;
    sourceWindow.style.width = `${width}px`;
    sourceWindow.style.height = `${width * cropHeight / CANVAS.width}px`;
    sourceWindow.style.visibility = sourceReady ? 'visible' : 'hidden';
    opacity(cropEdge, smooth(segment(3000, 3250)) * (1 - smooth(segment(7000, 8800))));
    opacity(paper, paperOpacity);
    opacity(print, printOpacity);
    opacity(signatures, signaturesOpacity);
    print.style.transform = `translateY(${(1 - printOpacity) * 18}px)`;
    signatures.style.transform = `translateY(${(1 - signaturesOpacity) * 14}px)`;
    print.setAttribute('aria-hidden', String(printOpacity === 0));
    signatures.setAttribute('aria-hidden', String(signaturesOpacity === 0));

    $('source-description').textContent = cropProgress === 0
      ? '固定画布：宁岚、叶青、沈舟三个旧名字与上方的火形。'
      : cropProgress < 1
        ? '固定画布的下缘正在被裁去，裁框向上经过三个旧名字。'
        : '从同一固定画布裁取的上部火形；三个旧名字均在窗口之外。';
    begin.hidden = started;
    begin.disabled = !sourceReady || ended;
    pause.disabled = !started || ended || elapsedMs >= DURATION;
    pause.textContent = running ? '暂停' : started && elapsedMs < DURATION && !ended ? '继续' : '暂停';
    finish.disabled = ended;
    const message = loadError || (ended ? '观看停在这里，原话仍留在纸外。'
      : !sourceReady ? '正在载入源图。'
      : !started ? '原图停在这里。'
      : !running && elapsedMs < DURATION ? '编排已暂停。'
      : phase() === 'source' ? '三个旧名字，仍在图中。'
      : phase() === 'cropping' ? '取上面的图。'
      : phase() === 'placing' ? '图进入纸面，文字重新排入。'
      : '告示留在这里。');
    if (status.textContent !== message) status.textContent = message;
    stage.dataset.phase = phase();
    rendered = { cropHeight, cropProgress, placement, paperOpacity, printOpacity, signaturesOpacity };
  }

  function settle(now) {
    if (!running) return;
    elapsedMs = Math.min(DURATION, elapsedMs + Math.max(0, now - lastTick));
    lastTick = now;
    if (elapsedMs >= DURATION) running = false;
  }

  function tick(now) {
    raf = 0;
    settle(now);
    render();
    if (running) raf = requestAnimationFrame(tick);
  }

  function stopClock() {
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
  }

  begin.addEventListener('click', () => {
    if (!sourceReady || started || ended) return;
    started = true;
    running = true;
    lastTick = performance.now();
    lastAction = 'begin';
    render();
    pause.focus({ preventScroll: true });
    raf = requestAnimationFrame(tick);
  });

  pause.addEventListener('click', () => {
    if (!started || ended || elapsedMs >= DURATION) return;
    if (running) {
      settle(performance.now());
      running = false;
      stopClock();
      lastAction = 'pause';
    } else {
      running = true;
      lastTick = performance.now();
      lastAction = 'resume';
      raf = requestAnimationFrame(tick);
    }
    render();
  });

  finish.addEventListener('click', () => {
    if (ended) return;
    settle(performance.now());
    running = false;
    ended = true;
    lastAction = 'finish';
    stopClock();
    render();
  });

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden || !running) return;
    settle(performance.now());
    running = false;
    lastAction = 'background-pause';
    stopClock();
    render();
  });
  window.addEventListener('resize', render);

  function rect(element) {
    const r = element.getBoundingClientRect();
    return { x: r.x, y: r.y, width: r.width, height: r.height };
  }

  // Rendered visibility is separate from being within a scrollable viewport.
  function visible(element) {
    const r = element.getBoundingClientRect();
    if (!r.width || !r.height) return false;
    let left = r.left, right = r.right, top = r.top, bottom = r.bottom;
    for (let e = element; e && e.nodeType === 1; e = e.parentElement) {
      const s = getComputedStyle(e);
      if (e.hidden || s.display === 'none' || s.visibility !== 'visible' || Number(s.opacity) === 0) return false;
      if (e !== element) {
        const p = e.getBoundingClientRect();
        if (['hidden', 'clip'].includes(s.overflowX)) { left = Math.max(left, p.left); right = Math.min(right, p.right); }
        if (['hidden', 'clip'].includes(s.overflowY)) { top = Math.max(top, p.top); bottom = Math.min(bottom, p.bottom); }
        if (left >= right || top >= bottom) return false;
      }
    }
    return true;
  }

  function snapshot() {
    const imageRect = rect(sourceWindow);
    const slotRect = rect(slot);
    const requestRect = rect(request);
    return {
      ready: sourceReady,
      phase: phase(),
      elapsedMs,
      durationMs: DURATION,
      running,
      ended,
      lastAction,
      error: loadError,
      source: {
        path: SOURCE_PATH,
        loaded: sourceReady,
        static: true,
        materialStep: 122,
        pngSize: { width: 1360, height: 1100 },
        canvas: { ...CANVAS },
        visible: sourceReady && visible(sourceWindow),
        screenRect: imageRect
      },
      clip: {
        x: CANVAS.x,
        y: CANVAS.y,
        width: CANVAS.width,
        height: rendered.cropHeight,
        bottom: CANVAS.y + rendered.cropHeight,
        progress: rendered.cropProgress,
        allOldNamesOutside: rendered.cropHeight <= CROP_HEIGHT,
        edgeVisible: visible(cropEdge)
      },
      notice: {
        visible: visible(paper),
        paperOpacity: rendered.paperOpacity,
        body: $('notice-body').textContent,
        bodyVisible: visible($('notice-body')),
        placementProgress: rendered.placement,
        imageAlignedWithSlot: ['x', 'y', 'width', 'height'].every((k) => Math.abs(imageRect[k] - slotRect[k]) < .5),
        signatures: Array.from(signatures.querySelectorAll('[data-signature]'), (el) => {
          const style = getComputedStyle(el);
          return { name: el.textContent, visible: visible(el), fontSize: style.fontSize, color: style.color };
        })
      },
      request: {
        text: $('request-text').textContent,
        visible: visible(request),
        insideNotice: notice.contains(request),
        fullyInViewport: requestRect.x >= 0 && requestRect.y >= 0 && requestRect.x + requestRect.width <= innerWidth && requestRect.y + requestRect.height <= innerHeight
      }
    };
  }

  Object.defineProperty(window, '__a32', {
    value: Object.freeze({ snapshot }),
    writable: false,
    configurable: false
  });

  const imageProbe = new Image();
  imageProbe.onload = () => {
    if (imageProbe.naturalWidth !== 1360 || imageProbe.naturalHeight !== 1100) {
      loadError = '源图尺寸与这次裁取不符，编排未开始。';
    } else {
      sourceReady = true;
      lastAction = ended ? lastAction : 'ready';
    }
    render();
  };
  imageProbe.onerror = () => {
    loadError = '源图未载入。请保留仓库目录关系后重新打开。';
    render();
  };
  render();
  imageProbe.src = SOURCE_PATH;
})();
