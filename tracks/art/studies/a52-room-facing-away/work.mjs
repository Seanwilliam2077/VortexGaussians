import { createFireSource } from './fire-source.mjs';
import { createScene, DURATION } from './scene.mjs';

const canvas=document.querySelector('#view');
const status=document.querySelector('#status');
const play=document.querySelector('#play');
const pause=document.querySelector('#pause');
const leave=document.querySelector('#leave');
let scene=null,source=null,time=-1,playing=false,raf=0,previousWallTime=0,disposed=false,last=null,finalSourceSummary=null;
const costs={renderCalls:0,renderMilliseconds:0,sourceAdvanceMilliseconds:0};

function stopPlayback(){playing=false;cancelAnimationFrame(raf);raf=0;play.disabled=disposed||time>=DURATION;pause.disabled=true;}
function renderAt(seconds){
  if(disposed)throw new Error('This viewing session has ended.');
  if(!scene||!source)throw new Error('A52 is not ready.');
  if(!Number.isFinite(seconds)||seconds<0||seconds>DURATION)throw new RangeError('Time must be finite and within 0–120 seconds.');
  if(seconds+1e-9<time)throw new RangeError('A52 only advances. Open a new page for a new viewing.');
  const started=performance.now(),sourceSeconds=Math.max(0,Math.min(58,seconds-46));
  const sourceStarted=performance.now();
  const advanced=source.advanceTo(sourceSeconds);
  costs.sourceAdvanceMilliseconds+=performance.now()-sourceStarted;
  last=scene.renderAt(seconds,seconds>46?source.read():[]);
  time=seconds;costs.renderCalls++;costs.renderMilliseconds+=performance.now()-started;
  status.textContent=seconds>=DURATION?'观看结束':`${Math.floor(seconds/60)}:${String(Math.floor(seconds%60)).padStart(2,'0')} / 2:00`;
  return {...last,source:{seconds:advanced.seconds,frame:advanced.frame,particles:advanced.particles}};
}
function inspect(){
  return {ready:!!scene&&!!source&&!disposed,seconds:time,playing,disposed,last,render:scene?.inspect(),source:disposed?finalSourceSummary:source?.summary(),
    costs:{renderCalls:costs.renderCalls,renderMilliseconds:+costs.renderMilliseconds.toFixed(3),sourceAdvanceMilliseconds:+costs.sourceAdvanceMilliseconds.toFixed(3)}};
}
function dispose(){
  if(disposed)return;stopPlayback();finalSourceSummary=source?.summary()||null;disposed=true;scene?.dispose();source?.dispose();
  play.disabled=true;pause.disabled=true;status.textContent='已离开';
}
function tick(wallTime){
  if(!playing)return;
  const dt=Math.min(.1,(wallTime-previousWallTime)/1000);previousWallTime=wallTime;
  renderAt(Math.min(DURATION,Math.max(0,time)+dt));
  if(time>=DURATION){stopPlayback();return;}raf=requestAnimationFrame(tick);
}
async function initialize(){
  scene=createScene(canvas);
  source=await createFireSource();
  if(disposed){source.dispose();return;}
  renderAt(0);play.disabled=false;status.textContent='就绪 · 2分钟 · 无声';
}
const ready=initialize().catch(error=>{status.textContent=`无法开始：${error.message}`;console.error(error);throw error;});
window.__a52={ready,renderAt,inspect,dispose};
play.addEventListener('click',async()=>{await ready;if(disposed||playing||time>=DURATION)return;playing=true;play.disabled=true;pause.disabled=false;previousWallTime=performance.now();raf=requestAnimationFrame(tick);});
pause.addEventListener('click',stopPlayback);
leave.addEventListener('click',()=>{dispose();canvas.hidden=true;leave.disabled=true;});
window.addEventListener('pagehide',dispose,{once:true});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopPlayback();});
if(new URLSearchParams(location.search).has('embed'))document.body.classList.add('embed');
