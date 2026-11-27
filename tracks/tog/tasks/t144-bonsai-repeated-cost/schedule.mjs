import assert from 'node:assert/strict';

export async function runSchedule({page, cfg, historical, report, save, actual, rootState, compare}, processNumber) {
  assert([1,2].includes(processNumber));
  assert.deepEqual(report.parent, historical.parent);
  assert.deepEqual(report.shell, historical.shell);
  assert.equal(report.matte.native_weight_sha256, historical.matte.native_weight_sha256);
  assert.equal(report.matte.total, historical.matte.total);
  assert.equal(report.pick_audit.sourceCameraId, cfg.camera_ids[0]);
  assert.deepEqual(report.pick_audit.samples.map(s=>s.actual), historical.pick_audit.samples.map(s=>s.actual));
  const ordinary = historical.actions[0];
  report.process_number = processNumber;
  async function validate(method, audit) {
    const record = await actual(method, audit);
    compare(ordinary, record);
    assert.deepEqual(await rootState(), report.parent, 'Action did not restore parent');
    assert.equal(record.secondary, 'undefined');
    assert.deepEqual(record.branches.map(b=>[b.name,b.clicked]), ordinary.branches.map(b=>[b.name,b.clicked]));
    return record;
  }
  await page.evaluate(()=>__t141.diagnostic(true));
  const independent = await validate('ordinary-native', true);
  await page.evaluate(()=>__t141.diagnostic(false));
  for (const branch of independent.branches) {
    const hist=branch.result.contrast, sum=a=>a.reduce((s,v)=>s+v,0);
    assert.equal(sum(hist.pixel.all),cfg.width*cfg.height);
    assert.equal(sum(hist.block.all),cfg.width*cfg.height/4);
    assert.equal(sum(hist.block.target),report.matte.nonzero_cells);
    assert.equal(sum(hist.pixel.target),report.matte.nonzero_cells*4);
    assert.equal(sum(hist.massByBlockBin.slice(64)),branch.result.mass);
    assert(Math.abs(sum(hist.massByBlockBin)-report.matte.total)<1e-8);
  }
  for (const method of ['ordinary-indexed','transport']) {
    await page.evaluate(()=>__t141.cold());
    await validate(method,true);
  }
  report.waves=[];
  const forward=['ordinary-indexed','transport'], reverse=[...forward].reverse();
  function order(wave) {return (processNumber-1+wave)%2?reverse:forward;}
  for(const method of order(0)) {
    await page.evaluate(()=>__t141.cold());
    const row=await validate(method,false);
    row.timing_role='warmup';
    await save();
  }
  for(let wave=0;wave<6;wave++) {
    const methods=order(wave);
    for(const method of methods) {
      const row=await validate(method,false);
      row.wave=wave+1;row.timing_role='measured';
      await save();
    }
    report.waves.push({wave:wave+1,order:methods});
    await save();
  }
  report.status='replication_complete';
}
