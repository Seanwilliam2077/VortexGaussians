// The outer fork resets the benchmark to its pre-click starting state and is
// outside delivery timing. Each real preview still forks/restores inside its own query.
let t98Original = null;
window.__t98 = {
  eligibleAfterClick() {
    if(!t86Global || researchFrame!==180) throw Error('Expected post-click state');
    const sb=sceneBurnState;
    return t90Shell.ids.filter(i=>sb.state[i]===0 && sb.fuel[i]>0);
  },
  resetTrial() {
    if (t98Original || t86Global || researchFrame !== 180) throw Error('Invalid pre-click state');
    const oldShell=t90Shell;
    t98Original = {live:t90Fork(),oldShell};
  },
  click(method,h,dt,pick) {
    if (!t98Original) throw Error('Missing trial reset');
    const start=performance.now();
    const stroke=__t86.ignite(pick,true), afterClick=performance.now();
    __t90.configure(pick);
    const afterRegion=performance.now(), r=__t90.query(method,h,dt);
    return {yes:r.yes, first_frame:r.first_frame, witness:r.witness, prefix_steps:r.prefix_steps,
            fork_ms:r.fork_ms, restore_ms:r.restore_ms, compute_ms:r.compute_ms,
            plan_active:r.plan_active ?? null, cache_build:r.cache_build ?? null, cache_rows:r.cache_rows ?? null,
            shell_index_ms:afterRegion-afterClick, click_ms:afterClick-start, clicked:stroke.count,
            preview_browser_ms:r.browser_ms, total_browser_ms:performance.now()-start};
  },
  finishTrial() {
    if(!t98Original) throw Error('No trial');
    t90Restore(t98Original.live);
    t90Shell=t98Original.oldShell;
    t86Global=false;
    t98Original=null;
  }
};
