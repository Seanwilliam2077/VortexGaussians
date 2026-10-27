/* Art rehearsal host. Uses only the existing public __demo API; no solver or shader changes. */
'use strict';
(() => {
  const VERSION = 1;
  const STORAGE_KEY = 'vortex-gaussians.art.memory.v1';
  const SEED = 20261027;
  const DT = 1 / 60;
  const MAX_FILE_BYTES = 64 * 1024 * 1024;
  const MAX_NOTES = 200;
  const MAX_EVENTS = 1200;
  const $ = id => document.getElementById(id);
  const fields = ['context', 'choice', 'observation'];
  const stageNames = { space: '保存的空间', intervene: '介入燃烧', revisit: '重置重看' };
  const kindNames = { 'author-draft': '作者草稿', 'author-observation': '作者观察', 'audience-observation': '真实观众记录（自行标注）' };
  const now = () => new Date().toISOString();
  const uid = () => globalThis.crypto?.randomUUID?.() || `local-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const state = { api: null, stage: 'space', loading: false, running: false, raf: null, remaining: 0,
    steps: 0, scene: null, runId: null, runNumber: 0, storageOK: true, storageReadBlocked: false, journal: null };
  let saveTimer;
  let connectPromise = null;

  function newJournal() {
    return { schema: 'vortex-gaussians-art-journal', version: VERSION, createdAt: now(), sessionId: uid(),
      title: '可燃的数字记忆（暂定）', hypothesis: '保存、介入与重新开始之间的创作张力；尚无观众验证。',
      notes: [], events: [], omittedEventCount: 0, resetReceiptVisible: true,
      draft: { kind: 'author-draft', context: '', choice: '', observation: '' } };
  }
  function readJournal() {
    const fresh = newJournal();
    try {
      const text = localStorage.getItem(STORAGE_KEY);
      if (!text) return fresh;
      const saved = JSON.parse(text);
      if (saved.schema !== fresh.schema || saved.version !== VERSION || !Array.isArray(saved.notes) || !Array.isArray(saved.events)) throw new Error('不支持的本地记录格式');
      // Stored text is always rendered with textContent, never as HTML.
      return { ...fresh, ...saved, notes: saved.notes.slice(0, MAX_NOTES), events: saved.events.slice(-MAX_EVENTS),
        draft: { ...fresh.draft, ...(saved.draft || {}) } };
    } catch (error) {
      state.storageOK = false; state.storageReadBlocked = true;
      $('save-status').textContent = '无法读取本地记录；当前新草稿仅在内存中，请导出备份。';
      return fresh;
    }
  }
  function persist(message = '已保存到本浏览器；这不是仿真状态备份。') {
    if (state.storageReadBlocked) {
      $('save-status').textContent = '旧本地记录无法读取，已避免覆盖；当前内容仅在内存中，请导出 JSON。';
      return;
    }
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state.journal));
      state.storageOK = true;
      $('save-status').textContent = message;
    } catch (error) {
      state.storageOK = false;
      $('save-status').textContent = '本地保存不可用或空间不足。记录仍在当前页，请立即导出 JSON。';
    }
  }
  function draftFromForm() {
    return { kind: $('note-kind').value, ...Object.fromEntries(fields.map(id => [id, $(id).value])) };
  }
  function saveDraft() { state.journal.draft = draftFromForm(); persist(); }
  function record(type, detail = {}) {
    state.journal.events.push({ at: now(), type, stage: state.stage, runId: state.runId, simulationStep: state.steps, ...detail });
    if (state.journal.events.length > MAX_EVENTS) {
      state.journal.events.shift(); state.journal.omittedEventCount += 1;
    }
    persist();
    if (type === 'reinitialize') renderReceipt();
  }
  function renderReceipt() {
    // Derived from an existing public-counter snapshot. Never restores or writes simulation state.
    const event = [...state.journal.events].reverse().find(item => item.type === 'reinitialize'
      && item.reason === '作者选择重新开始' && item.previous);
    $('receipt-empty').hidden = Boolean(event);
    $('receipt-toggle').hidden = !event;
    const visible = Boolean(event) && state.journal.resetReceiptVisible !== false;
    $('receipt-content').hidden = !visible;
    $('receipt-toggle').setAttribute('aria-expanded', String(visible));
    $('receipt-toggle').textContent = visible ? '暂时收起回执' : '再次展开回执';
    if (!event) return;
    const previous = event.previous;
    const count = value => Number.isFinite(value) ? value.toLocaleString() : '未记录';
    const seconds = Number.isFinite(previous.simulatedSeconds) ? `${previous.simulatedSeconds.toFixed(2)} s` : '未记录';
    const kind = previous.scene?.kind === 'synthetic-campfire-example' ? '合成示例，非实拍记忆' : '本地资产，来源由作者说明';
    $('receipt-context').textContent = `${previous.scene?.name || '未命名场景'} · ${kind}`;
    $('receipt-time').textContent = seconds;
    $('receipt-burning').textContent = count(previous.counts?.burning);
    $('receipt-charred').textContent = count(previous.counts?.charred);
    $('receipt-at').textContent = `重新初始化操作时间：${event.at}。当前画面可能已经进入另一段排练。`;
  }
  function setStatus(text, kind = '') {
    $('status').textContent = text;
    $('connection-dot').className = `dot ${kind}`;
  }
  function safeSnapshot() {
    if (!state.api || !state.scene) return null;
    return { scene: { ...state.scene }, runId: state.runId, simulationStep: state.steps,
      simulatedSeconds: state.steps * DT, seed: SEED, counts: state.api.spreadInfo(),
      scenePoints: state.api.sceneN, parameters: Object.fromEntries([
        'solver', 'dimMode', 'sliceMode', 'layers', 'simLayers', 'ppl', 'emitterOn', 'spreadOn',
        'spreadClockMode', 'spreadParticlePolicy', 'spreadMeasureMode', 'spreadFrontierCap',
        'spreadSampleCap', 'spreadFeedCap', 'sceneScale', 'sceneLift', 'sceneYaw', 'scenePitch',
        'sceneOffX', 'sceneOffZ', 'yaw', 'sceneSH', 'sceneSorted', 'sceneBackdrop', 'sceneDepthTest'
      ].map(key => [key, state.api.P[key]])), scope: 'Selected public counters and parameters; not a complete checkpoint or physical measurement.' };
  }
  function updateControls() {
    const ready = Boolean(state.api && state.scene && !state.loading);
    document.querySelectorAll('[data-sim-control]').forEach(el => { el.disabled = !ready || state.running; });
    $('pause').disabled = !state.running;
    $('start-example').disabled = state.loading;
    $('load-example').disabled = state.loading || state.running;
    $('local-ply').disabled = state.loading || state.running;
    $('time-label').textContent = `模拟时间 ${(state.steps * DT).toFixed(2)} s`;
  }
  function readout() {
    updateControls();
    if (!state.api || !state.scene) return;
    const stats = state.api.spreadInfo();
    $('scene-count').textContent = state.api.sceneN.toLocaleString();
    $('burning-count').textContent = (stats?.burning ?? 0).toLocaleString();
    $('char-count').textContent = (stats?.charred ?? 0).toLocaleString();
    $('run-count').textContent = String(state.runNumber);
  }
  function pause(reason, log = true) {
    const wasRunning = state.running;
    state.running = false; state.remaining = 0;
    if (state.raf !== null) cancelAnimationFrame(state.raf);
    state.raf = null;
    if (state.api) state.api.P.paused = true;
    if (wasRunning && log) record('pause', { reason });
    readout();
    if (wasRunning) setStatus(`已暂停：${reason}。`, 'ready');
  }
  function selectStage(stage) {
    if (!Object.hasOwn(stageNames, stage)) return;
    pause('切换阶段');
    state.stage = stage;
    document.querySelectorAll('[data-stage]').forEach(button => {
      const active = button.dataset.stage === stage;
      button.classList.toggle('active', active);
      if (active) button.setAttribute('aria-current', 'step'); else button.removeAttribute('aria-current');
    });
    Object.keys(stageNames).forEach(key => { $(`panel-${key}`).hidden = key !== stage; });
    record('stage', { selected: stage });
  }
  async function connect() {
    if (state.api) return state.api;
    if (connectPromise) return connectPromise;
    connectPromise = new Promise((resolve, reject) => {
      const frame = $('demo-frame');
      let done = false;
      const finish = (error, api) => {
        if (done) return;
        done = true; clearTimeout(timer); frame.removeEventListener('load', loaded);
        if (error) { connectPromise = null; reject(error); } else { state.api = api; resolve(api); }
      };
      const loaded = () => {
        try {
          const api = frame.contentWindow.__demo;
          const required = ['reset', 'loadPLY', 'ignite', 'step', 'render', 'spreadInfo'];
          if (!api?.P || required.some(key => typeof api[key] !== 'function')) throw new Error('原 demo 未就绪：请确认 WebGL2 可用并从同一个本地 HTTP 地址打开。');
          finish(null, api);
        } catch (error) {
          finish(new Error(`无法连接同源 demo。请在仓库目录启动本地 HTTP 服务，再打开 /tracks/art/。${error.message}`));
        }
      };
      const timer = setTimeout(() => finish(new Error('原 demo 启动超时。请检查 WebGL2 或改用 README 的本地 HTTP 启动方式。')), 20000);
      frame.addEventListener('load', loaded);
      frame.src = '../../demo/index.html?embed=1&solver=vpm&orbit=0';
    });
    return connectPromise;
  }
  async function digest(buffer) {
    if (!globalThis.crypto?.subtle) return null;
    const hash = await crypto.subtle.digest('SHA-256', buffer);
    return Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join('');
  }
  function resetState(reason) {
    const previous = safeSnapshot();
    const api = state.api;
    pause(reason);
    api.P.paused = true; api.P.orbit = false; api.P.emitterOn = false; api.P.spreadOn = false;
    api.reset(SEED);
    state.steps = 0; state.runId = uid(); state.runNumber += 1;
    api.render();
    record('reinitialize', { reason, previous, semantics: 'Clears current flow and scene burn state. Not reverse combustion or checkpoint restoration.' });
    readout();
  }
  async function loadScene(file) {
    if (state.loading || state.running) return;
    state.loading = true; updateControls();
    setStatus('正在载入原 demo 与场景；不会自动点火。');
    try {
      const api = await connect();
      let buffer;
      if (file) {
        if (!file.name.toLowerCase().endsWith('.ply')) throw new Error('请选择 .ply 文件。');
        if (file.size > MAX_FILE_BYTES) throw new Error('文件超过本入口 64 MiB 上限；可另开原 demo 自行处理。');
        buffer = await file.arrayBuffer();
      } else {
        const response = await fetch('../../static/test_scene.ply', { credentials: 'same-origin' });
        if (!response.ok) throw new Error(`合成示例读取失败（HTTP ${response.status}）。`);
        buffer = await response.arrayBuffer();
      }
      if (buffer.byteLength > MAX_FILE_BYTES) throw new Error('场景超过本入口 64 MiB 上限。');
      const sha256 = await digest(buffer);
      Object.assign(api.P, { paused: true, orbit: false, emitterOn: false, spreadOn: false,
        sceneMax: 800000, sceneYaw: 0, scenePitch: 0, sceneOffX: 0, sceneOffZ: 0, sceneLift: 0.6, yaw: 0 });
      $('camera-yaw').value = '0'; $('yaw-value').textContent = '0°';
      const loaded = api.loadPLY(buffer);
      state.scene = { name: file ? file.name : 'test_scene.ply', kind: file ? 'user-selected-local-asset' : 'synthetic-campfire-example',
        bytes: buffer.byteLength, sha256, kept: loaded.kept, total: loaded.total,
        authenticity: file ? 'User-supplied; capture status and permissions not verified by this tool.' : 'Synthetic example, not a real captured memory.' };
      $('scene-label').textContent = file ? `本地资产：${file.name} · 来源由作者说明` : '合成营火示例 · 非实拍记忆';
      $('empty-state').hidden = true;
      resetState('载入场景');
      selectStage('space');
      setStatus(`已载入 ${loaded.kept.toLocaleString()} / ${loaded.total.toLocaleString()} 个点。当前暂停；请先观察、记录情境。`, 'ready');
      record('load-scene', { scene: { ...state.scene } });
    } catch (error) {
      setStatus(error.message, 'error');
      record('load-error', { message: error.message });
    } finally {
      state.loading = false; $('local-ply').value = ''; readout();
    }
  }
  function ignite() {
    if (!state.api || !state.scene || state.running) return;
    const names = ['ignite-x', 'ignite-y', 'ignite-z', 'ignite-radius'];
    if (names.some(id => !$(id).reportValidity())) return;
    const position = names.slice(0, 3).map(id => Number($(id).value));
    const radius = Number($('ignite-radius').value);
    if (![...position, radius].every(Number.isFinite)) return;
    state.api.P.spreadOn = true;
    const ignitedPoints = state.api.ignite(...position, radius);
    state.api.render();
    record('ignite', { position, radius, ignitedPoints, snapshot: safeSnapshot() });
    readout();
    setStatus(ignitedPoints ? `此次点燃 ${ignitedPoints.toLocaleString()} 个未燃点。尚未推进；可先记录选择。` : '此位置没有点燃新点：可能未命中场景，或该处已燃烧。请检查位置与半径。', 'ready');
  }
  function advance(frames) {
    if (!state.api || !state.scene || state.running || state.stage !== 'intervene') return;
    state.running = true; state.remaining = frames;
    record('advance-start', { requestedFrames: frames, dt: DT });
    updateControls();
    setStatus(`正在推进 ${(frames * DT).toFixed(0)} 秒模拟；可随时暂停。`, 'ready');
    const tick = () => {
      if (!state.running) return;
      if (document.hidden) { pause('页面已隐藏'); return; }
      try {
        // raw __demo.step is explicit; paused also gates the original ember emission.
        state.api.P.paused = false;
        try { state.api.step(1, DT); state.steps += 1; state.api.render(); }
        finally { state.api.P.paused = true; }
        state.remaining -= 1;
        $('time-label').textContent = `模拟时间 ${(state.steps * DT).toFixed(2)} s`;
        if (state.steps % 30 === 0) readout();
        if (state.remaining <= 0) {
          state.running = false; state.raf = null;
          record('advance-complete', { snapshot: safeSnapshot() });
          readout(); setStatus('本段推进完成，已暂停。请记录变化，再决定下一步。', 'ready');
          return;
        }
        state.raf = requestAnimationFrame(tick);
      } catch (error) {
        pause('运行出现异常');
        setStatus(`已停止推进：${error.message}`, 'error');
        record('runtime-error', { message: error.message });
      }
    };
    state.raf = requestAnimationFrame(tick);
  }
  function renderNotes() {
    const list = $('notes'); list.replaceChildren();
    $('note-count').textContent = `${state.journal.notes.length} 条记录`;
    if (!state.journal.notes.length) {
      const empty = document.createElement('li'); empty.className = 'no-notes';
      empty.textContent = '尚无记录。你不必先点火才能写下理由。'; list.append(empty); return;
    }
    for (const note of [...state.journal.notes].reverse()) {
      const item = document.createElement('li');
      const meta = document.createElement('p'); meta.className = 'note-meta';
      meta.textContent = `${kindNames[note.kind] || '未识别记录'} · ${stageNames[note.stage] || '未记阶段'} · ${note.at}`;
      item.append(meta);
      for (const [key, label] of [['context', '情境'], ['choice', '选择'], ['observation', '观察 / 问题']]) {
        if (!note[key]) continue;
        const paragraph = document.createElement('p'); paragraph.className = 'note-field';
        const title = document.createElement('strong'); title.textContent = label;
        paragraph.append(title, document.createTextNode(String(note[key]))); item.append(paragraph);
      }
      list.append(item);
    }
  }
  function addNote(event) {
    event.preventDefault();
    const draft = draftFromForm();
    if (!fields.some(key => draft[key].trim())) { $('save-status').textContent = '请先写下一项情境、选择或观察。'; return; }
    if (draft.kind === 'audience-observation' && (!draft.context.trim() || !draft.observation.trim())) {
      $('save-status').textContent = '真实观众记录需要实际观看情境和观察内容；没有发生过的观看请使用作者草稿。'; return;
    }
    if (state.journal.notes.length >= MAX_NOTES) { $('save-status').textContent = '本入口已达 200 条记录上限。请先导出，不会自动删除旧笔记。'; return; }
    state.journal.notes.push({ id: uid(), at: now(), stage: state.stage, ...draft, snapshot: safeSnapshot(), audienceEvidenceVerified: false });
    fields.forEach(id => { $(id).value = ''; });
    state.journal.draft = draftFromForm();
    persist('记录已保存。观众性质来自作者标注，工具未替你验证。');
    renderNotes();
  }
  function exportJournal() {
    clearTimeout(saveTimer); state.journal.draft = draftFromForm();
    record('export');
    const payload = { ...state.journal, exportedAt: now(), tool: 'tracks/art/index.html',
      limitations: ['Author rehearsal, not a completed artwork or validated audience study.',
        'Notes and selected metadata only; no asset bytes, screenshots or resumable simulation checkpoint.',
        'Reset reinitializes current flow and scene burn; it does not reverse combustion.',
        'Artistic claims and TOG technical claims require independent evidence.'],
      currentSnapshot: safeSnapshot() };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' }));
    const link = document.createElement('a'); link.href = url;
    link.download = `digital-memory-journal-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  state.journal = readJournal();
  $('note-kind').value = Object.hasOwn(kindNames, state.journal.draft.kind) ? state.journal.draft.kind : 'author-draft';
  fields.forEach(id => { $(id).value = String(state.journal.draft[id] || ''); });
  const kindChanged = () => { $('audience-help').hidden = $('note-kind').value !== 'audience-observation'; };
  kindChanged(); renderNotes(); renderReceipt(); updateControls();
  document.querySelectorAll('[data-stage]').forEach(button => button.addEventListener('click', () => selectStage(button.dataset.stage)));
  $('start-example').addEventListener('click', () => loadScene(null));
  $('load-example').addEventListener('click', () => loadScene(null));
  $('local-ply').addEventListener('change', () => { if ($('local-ply').files[0]) loadScene($('local-ply').files[0]); });
  $('ignite').addEventListener('click', ignite);
  $('advance').addEventListener('click', () => advance(60));
  $('play').addEventListener('click', () => advance(600));
  $('pause').addEventListener('click', () => pause('作者主动暂停'));
  $('reset').addEventListener('click', () => {
    if (!state.api || !state.scene || state.running) return;
    saveDraft(); resetState('作者选择重新开始');
    selectStage('space'); setStatus('已重新初始化：本次烧损与流动已清空，笔记保留。这不是历史倒放。', 'ready');
  });
  $('camera-yaw').addEventListener('input', () => {
    if (!state.api || state.running) return;
    const degrees = Number($('camera-yaw').value);
    state.api.P.yaw = degrees / 180; // Public P.yaw is half-turn units: original camera uses P.yaw * PI.
    state.api.render(); // Updates the original camera before any later explicit step.
    $('yaw-value').textContent = `${degrees}°`;
  });
  $('camera-yaw').addEventListener('change', () => record('view-angle', { degrees: Number($('camera-yaw').value) }));
  $('note-form').addEventListener('submit', addNote);
  $('note-form').addEventListener('input', () => { kindChanged(); clearTimeout(saveTimer); saveTimer = setTimeout(saveDraft, 350); });
  $('receipt-toggle').addEventListener('click', () => {
    state.journal.resetReceiptVisible = state.journal.resetReceiptVisible === false;
    record('receipt-visibility', { visible: state.journal.resetReceiptVisible,
      semantics: 'Presentation only; no event deletion or simulation state change.' });
    renderReceipt();
  });
  $('export').addEventListener('click', exportJournal);
  document.addEventListener('visibilitychange', () => { if (document.hidden) { pause('页面已隐藏'); saveDraft(); } });
  window.addEventListener('pagehide', () => { pause('离开页面'); saveDraft(); });
})();
