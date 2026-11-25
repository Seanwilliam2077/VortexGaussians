// Untimed live check with an editor selection at a different radius and center.
window.__t123CheckSelection = function (method,dt,picks,cameras) {
  const initial=t90Shell, pick=picks[0];
  try {
    __t90.configure({...pick,radius:0.05,world:pick.world.map((v,i)=>i===0?v+0.08:v)});
    const selected=t90Shell;
    const guard=t119Guard, injected=new Error('selection audit injection');
    let caught=false;
    try {
      t119Guard=()=>{throw injected;};
      __t123(method,dt,picks,cameras);
    } catch(error) {
      if(error!==injected)throw error;
      caught=true;
    } finally {
      t119Guard=guard;
    }
    if(!caught || t90Shell!==selected)throw Error('Failed to preserve selection on guard error');
    const result=__t123(method,dt,picks,cameras);
    if(t90Shell!==selected || !result.equivalence?.admitted)throw Error('Failed to restore earlier selection');
    result.selection_audit={sites:selected.ids.length,same_object_after_guard_error:true,same_object_after_query:true};
    return result;
  } finally {
    t90Shell=initial;
  }
};
