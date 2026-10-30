// Same-origin, hidden source page. The original solver remains in its own realm.
export async function createFireSource() {
  const started = performance.now();
  const iframe = document.createElement('iframe');
  iframe.title = 'A52 deterministic fire particle source';
  iframe.setAttribute('aria-hidden', 'true');
  iframe.tabIndex = -1;
  iframe.style.cssText = 'position:fixed;left:-10000px;top:0;width:1px;height:1px;border:0;visibility:hidden;pointer-events:none';
  const url = new URL('./source.generated.html', import.meta.url);
  url.search = '?embed=1';
  let api, disposed = false, sourceLoadMs = 0;
  try {
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => finish(new Error('A52 fire source load timed out')), 30000);
      const finish = error => {
        clearTimeout(timeout);
        iframe.onload = iframe.onerror = null;
        error ? reject(error) : resolve();
      };
      iframe.onerror = () => finish(new Error('A52 fire source failed to load; run assemble-source.mjs'));
      iframe.onload = () => {
        try {
          const bridge = iframe.contentWindow?.__a52FireBridge;
          if (!bridge?.ready || !bridge.api)
            throw new Error(bridge?.error || 'A52 bridge unavailable; assemble source.generated.html first');
          api = bridge.api;
          finish();
        } catch (error) { finish(error); }
      };
      iframe.src = url.href;
      (document.body || document.documentElement).appendChild(iframe);
    });
    sourceLoadMs = performance.now() - started;
  } catch (error) {
    iframe.remove();
    throw error;
  }
  const active = () => {
    if (disposed) throw new Error('A52 fire source is disposed');
  };
  return Object.freeze({
    advanceTo(seconds) { active(); return api.advanceTo(seconds); },
    read() { active(); return api.read(); },
    summary() {
      active();
      const result = api.summary();
      return { ...result, costs: { ...result.costs, sourceLoadMs } };
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      try { api.dispose(); } finally { iframe.remove(); }
    }
  });
}
