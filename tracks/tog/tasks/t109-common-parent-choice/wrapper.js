// Render weights are static per camera. The physical brush radius is allowed
// to differ while the evaluation remains attached to the same exterior shell.
window.__t109={
  install(count,pairs){t108Weights=null;return t108Cache(count,pairs);},
  click(mode,h,dt,pick,audit=false,auditFrames=[]){
    if(!['ordinary','restart','repair'].includes(mode)||h!==90||dt!==1/60||![.06,.12].includes(pick.radius))
      throw Error('Unregistered sibling choice');
    const start=performance.now(),stroke=__t86.ignite(pick,true),clicked=performance.now();
    __t90.configure({...pick,radius:.12});
    const region=performance.now(),p=t108Progress(),ready=performance.now();
    const answer=t108Answer(mode,p,h,dt,audit,auditFrames);
    return {...answer,clicked:stroke.count,click_ms:clicked-start,shell_index_ms:region-clicked,
      denominator_ms:ready-region,total_browser_ms:performance.now()-start};
  }
};
