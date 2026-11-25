// Independent untimed equality check. Gives comparison replay its own transient
// material context and keeps the exact gas at the recorded end of the block.
const t114Production=t114Repair;
t114Repair=function(mode,logs,dt,profile=false){
  if(mode!=='sitewise' || !profile)return t114Production(mode,logs,dt,profile);
  let atBoundary,next;
  const currentContext=t102Context,oldGraph=t97Graph,oldBuild=t97Build,branch=t90Fork();
  t102Context=null;
  try{
    t102Start('active-fresh',dt);
    for(const frame of logs)t100ReplayActive(frame,dt);
    atBoundary=t100Physical();t94StepFull(dt);next=t100Physical();
  }finally{
    if(t102Context)t102Stop();
    t102Context=currentContext;t97Graph=oldGraph;t97Build=oldBuild;t90Restore(branch);
  }
  const receipt=t114Production(mode,logs,dt,true);
  if(!t100Equal(atBoundary,t100Physical()))throw Error('Direct material/gas mismatch at '+researchFrame);
  const after=t90Fork();
  try{t94StepFull(dt);if(!t100Equal(next,t100Physical()))throw Error('Direct continuation mismatch at '+researchFrame);}
  finally{t90Restore(after);}
  receipt.direct_state={frame:researchFrame,matched_boundary:true,matched_next:true,typed_fields:atBoundary.material.length,
    bytes:atBoundary.material.reduce((s,a)=>s+a.byteLength,0),frontier:atBoundary.frontier.length,
    particles:atBoundary.gas.reduce((s,v)=>s+v[4].length,0)};
  return receipt;
};
