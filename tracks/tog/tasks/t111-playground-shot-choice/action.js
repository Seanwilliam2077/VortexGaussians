const t111Bank=new Map();
function t111Install(camera,n,pairs){
  t108Weights=null;
  const result=t108Cache(n,pairs);
  t111Bank.set(camera,t108Weights);
  return result;
}
function t111Progress(cameras,audit){
  const ids=[],sb=sceneBurnState,mask=new Uint8Array(sb.state.length);
  const views=cameras.map(camera=>({camera,weights:t111Bank.get(camera),total:0,target:0,mass:0,
    first_frame:null,first_mass:0,first_count:0,witness:null,step_witness:null,step_count:0,curve:[]}));
  for(const id of t90Shell.ids){
    if(sb.state[id]!==0 || sb.fuel[id]<=0)continue;
    mask[id]=1;ids.push(id);
    for(const v of views){
      const weight=v.weights[id];
      if(!Number.isSafeInteger(weight)||weight<0)throw Error('Missing regional site in view');
      v.total+=weight;
    }
  }
  for(const v of views){
    if(!Number.isSafeInteger(v.total))throw Error('Unsafe integral opacity mass');
    v.target=Math.ceil(v.total/4);
  }
  const defined=views.some(v=>v.target>0);
  return {ids,mask,views,audit,count:0,total:defined?1:0,target:defined?1:0,
    get mass(){return this.views.every(v=>v.target===0 || v.mass>=v.target)?1:0;},
    set mass(z){
      if(z!==0)throw Error('Unexpected restart progress');
      for(const v of this.views)Object.assign(v,{mass:0,first_frame:null,first_mass:0,first_count:0,
                                                witness:null,step_witness:null,step_count:0,curve:[]});
    }};
}
function t111Add(p,id){
  p.count++;
  for(const v of p.views){
    if(!p.audit && v.first_frame!==null)continue;
    const w=v.weights[id];v.mass+=w;v.step_count++;
    if(w>0 && (v.step_witness===null || id<v.step_witness))v.step_witness=id;
  }
}
function t111Record(p,frame){
  for(const v of p.views){
    if(v.target>0 && v.first_frame===null && v.mass>=v.target){
      if(v.step_witness===null)throw Error('Crossed without positive-weight contributor');
      v.first_frame=frame;v.first_mass=v.mass;v.first_count=p.count;v.witness=v.step_witness;
    }
    if(p.audit)v.curve.push([frame,v.step_count,p.count,v.mass]);
    v.step_count=0;v.step_witness=null;
  }
}
function t111Sibling(mode,dt,pick,cameras,audit=false,frames=[]){
  const begin=performance.now();__t98.resetTrial();const forked=performance.now();
  let reply;
  try{
    const edit=__t86.ignite(pick,true);const clicked=performance.now();
    __t90.configure({...pick,radius:.12});const configured=performance.now();
    const p=t111Progress(cameras,audit);const ready=performance.now();
    const a=t111Answer(mode,p,90,dt,audit,frames);
    reply={pick:pick.name,clicked:edit.count,outer_fork_ms:forked-begin,click_ms:clicked-forked,
      shell_index_ms:configured-clicked,denominator_ms:ready-configured,work:a.work,phases:a.phases,
      boundaries:a.boundaries,views:p.views.map(v=>({camera:v.camera,defined:v.total>0,total:v.total,target:v.target,
        eligible:p.ids.length,first_frame:v.first_frame,count:v.first_frame===null?p.count:v.first_count,
        mass:v.first_frame===null?v.mass:v.first_mass,witness:v.witness,curve:v.curve}))};
  }finally{const t=performance.now();__t98.finishTrial();if(reply)reply.outer_restore_ms=performance.now()-t;}
  return reply;
}
function t111Action(mode,dt,picks,cameras){
  if(!['ordinary','restart','repair'].includes(mode)||dt!==1/60||picks.length!==2)throw Error('Unregistered edit');
  const start=performance.now(),tried=[],choices={};
  let waiting=cameras.slice();
  for(const pick of picks){
    if(!waiting.length)break;
    const result=t111Sibling(mode,dt,pick,waiting);tried.push(result);
    waiting=[];
    for(const v of result.views){
      if(!v.defined)choices[v.camera]='undefined';
      else if(v.first_frame!==null)choices[v.camera]=pick.name;
      else{choices[v.camera]='none';waiting.push(v.camera);}
    }
  }
  return {choices,tried,total_browser_ms:performance.now()-start};
}
window.__t111={install:t111Install,action:t111Action,sibling:t111Sibling,
  cold(){if(t102Context || t98Original)throw Error('Active fork');t102Anchor=null;}};
