import assert from 'node:assert/strict';

export async function schedule145({page,report,save,actual,rootState,compare,historical}, number) {
  assert([1,2].includes(number));report.process_number=number;
  assert.deepEqual(report.parent,historical.parent);
  assert.deepEqual(report.shell,historical.shell);
  assert.deepEqual(report.matte,historical.matte);
  const at=performance.now();
  report.roi=await page.evaluate(()=>__t145.setup());report.roi_setup_ms=performance.now()-at;
  const ref=historical.actions[0];
  async function checked(method,audit){
    const row=await actual(method,audit);
    compare(ref,row);
    assert.deepEqual(await rootState(),report.parent);
    assert.deepEqual(row.branches.map(b=>[b.name,b.clicked]),ref.branches.map(b=>[b.name,b.clicked]));
    assert.equal(row.secondary,'undefined');
    return row;
  }
  const oracle=await checked('ordinary-native',true);
  for(const b of oracle.branches)assert.equal(b.result.cropHashes.length,2);
  await page.evaluate(()=>__t145.enable());
  const both=['ordinary-indexed','transport'];
  for(const method of both){
    await page.evaluate(()=>__t141.cold());
    const row=await checked(method,true);
    for(const b of row.branches){
      const refBranch=oracle.branches.find(x=>x.name===b.name);
      assert.deepEqual(b.result.cropHashes,refBranch.result.cropHashes);
    }
  }
  await page.evaluate(()=>__t145.closeAudit());
  const order=wave=>(number-1+wave)%2?[...both].reverse():both;
  for(const method of order(0)){
    await page.evaluate(()=>__t141.cold());
    const row=await checked(method,false);row.timing_role='warmup';await save();
  }
  report.waves=[];
  for(let w=0;w<6;w++){
    for(const method of order(w)){
      const row=await checked(method,false); row.timing_role='measured';row.wave=w+1;
      for(const b of row.branches)assert.equal(b.result.cropHashes.length,0);
      await save();
    }
    report.waves.push({wave:w+1,order:order(w)});await save();
  }
  report.status='replication_complete';
}
