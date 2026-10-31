import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
const here=path.dirname(fileURLToPath(import.meta.url));
if(!process.argv.includes('--execute')) { console.log('One existing-file check; <=90s; no render or re-encoding. --execute'); process.exit(0); }
const out=path.join(here,'saved-film-check-01');
await fs.mkdir(out,{recursive:false});
const started=performance.now(),wall=()=>(performance.now()-started)/1000;
const movie=path.join(here,'film-01/room-facing-away.mp4');
const original=path.join(here,'film-01/result.json');
const bin='C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/Library/bin';
const expected='635e62d7adc19759be525a2a54508635e6ef9c7dfbe082ec7e1049bafa5f69f3';
const sha=b=>createHash('sha256').update(b).digest('hex');
const identity=async f=>{const b=await fs.readFile(f);return {bytes:b.length,sha256:sha(b)};};
const result={schema:'a52-existing-media-check-v1',createdUTC:new Date().toISOString(),status:'started',limitSeconds:90,
  originalProductionStatus:'failed',childRuns:[],images:[],continuousViewing:false,
  scope:'Existing MP4 probe, full decode and original seven frame extraction only. Original failed production record remains immutable.'};
const children=new Set(),pending=new Set();let expired=false;
const timer=setTimeout(()=>{expired=true;for(const c of children)c.kill();},90000);
const check=()=>{if(expired||wall()>90)throw Error('Check deadline exceeded');};
async function run(name,exe,args){
  check();const at=wall(),stdoutFile=name+'.stdout.txt',stderrFile=name+'.stderr.txt';
  const stdout=await fs.open(path.join(out,stdoutFile),'wx');let stderr;
  try {
    stderr=await fs.open(path.join(out,stderrFile),'wx');
    const child=spawn(path.join(bin,exe),args,{windowsHide:true,stdio:['ignore',stdout.fd,stderr.fd]});
    children.add(child);
    const promise=new Promise((resolve,reject)=>{
      child.once('error',e=>{children.delete(child);reject(e);});
      child.once('close',(code,signal)=>{children.delete(child);resolve({code,signal});});
    });
    pending.add(promise);promise.then(()=>pending.delete(promise),()=>pending.delete(promise));
    const end=await promise;
    await stdout.close();await stderr.close();
    const so=await fs.readFile(path.join(out,stdoutFile),'utf8'),se=await fs.readFile(path.join(out,stderrFile),'utf8');
    const entry={name,exe,args,...end,wallSeconds:wall()-at,stdoutFile,stderrFile,stdout:so,stderr:se};
    result.childRuns.push(entry);
    if(end.code!==0||se.trim())throw Error(name+' failed or reported an error');
    check();return entry;
  }finally{await stdout.close().catch(()=>{});await stderr?.close().catch(()=>{});}
}
try{
  result.movieBefore=await identity(movie);result.originalBefore=await identity(original);
  result.scriptBefore=await identity(fileURLToPath(import.meta.url));
  if(result.movieBefore.sha256!==expected||JSON.parse(await fs.readFile(original,'utf8')).status!=='failed')throw Error('Existing artifact identity/status mismatch');
  const probe=await run('probe','ffprobe.exe',['-v','error','-select_streams','v:0','-show_entries',
    'format=duration,size:stream=codec_name,width,height,nb_frames,duration,r_frame_rate','-of','default',movie]);
  const streams=[...probe.stdout.matchAll(/\[STREAM\]\s*([\s\S]*?)\[\/STREAM\]/g)];
  const formats=[...probe.stdout.matchAll(/\[FORMAT\]\s*([\s\S]*?)\[\/FORMAT\]/g)];
  if(streams.length!==1||formats.length!==1)throw Error('Incomplete or ambiguous metadata sections');
  const fields=body=>Object.fromEntries(body.trim().split(/\r?\n/).map(line=>{const at=line.indexOf('=');if(at<1)throw Error('Bad metadata line');return [line.slice(0,at),line.slice(at+1).trim()];}));
  const stream=fields(streams[0][1]),format=fields(formats[0][1]);
  if(stream.codec_name!=='h264'||stream.width!=='1280'||stream.height!=='720'||stream.r_frame_rate!=='24/1'||stream.nb_frames!=='2880'
    ||Number(stream.duration)!==120||Number(format.duration)!==120||Number(format.size)!==result.movieBefore.bytes)throw Error('Media metadata mismatch');
  result.metadata={stream,format};
  const decoded=await run('decode','ffmpeg.exe',['-hide_banner','-v','error','-nostdin','-i',movie,'-map','0:v:0','-f','null','-','-progress','pipe:1','-nostats']);
  const counts=[...decoded.stdout.matchAll(/^frame=(\d+)\r?$/gm)].map(m=>Number(m[1]));
  if(counts.at(-1)!==2880||!/^progress=end\r?$/m.test(decoded.stdout))throw Error('Full decode frame count or completion missing');
  result.allFramesDecoded=true;result.decodedFrames=counts.at(-1);
  const selected=[0,576,1056,1440,2016,2496,2879];await fs.mkdir(path.join(out,'keyframes'));
  await run('keyframes','ffmpeg.exe',['-hide_banner','-v','error','-nostdin','-n','-i',movie,'-vf',
    'select='+selected.map(n=>'eq(n\\,'+n+')').join('+'),'-fps_mode','vfr',path.join(out,'keyframes','%02d.png')]);
  const files=(await fs.readdir(path.join(out,'keyframes'))).sort();
  if(files.length!==selected.length)throw Error('Wrong keyframe count');
  for(let i=0;i<selected.length;i++){
    const file='keyframes/'+String(i+1).padStart(2,'0')+'.png',b=await fs.readFile(path.join(out,file));
    if(!b.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))||b.readUInt32BE(16)!==1280||b.readUInt32BE(20)!==720)throw Error('Keyframe format/dimensions');
    result.images.push({file,encodedFrame:selected[i],seconds:selected[i]/24,bytes:b.length,sha256:sha(b)});
  }
  result.movieAfter=await identity(movie);result.originalAfter=await identity(original);result.scriptAfter=await identity(fileURLToPath(import.meta.url));
  if(result.movieBefore.sha256!==result.movieAfter.sha256||result.originalBefore.sha256!==result.originalAfter.sha256||result.scriptBefore.sha256!==result.scriptAfter.sha256)throw Error('Artifact changed during check');
  check();result.status='existing_film_verified';
}catch(e){result.status='failed';result.error={message:e.message,stack:e.stack};process.exitCode=1;}
finally{
  for(const c of children)c.kill();
  let grace;await Promise.race([Promise.allSettled([...pending]),new Promise(resolve=>{grace=setTimeout(resolve,3000);})]);clearTimeout(grace);clearTimeout(timer);
  result.remainingChildPIDs=[...children].map(c=>c.pid);result.expired=expired;result.wallSeconds=wall();
  if(expired||result.wallSeconds>90||children.size){result.status='failed';result.error??={message:'Deadline/cleanup incomplete'};process.exitCode=1;}
  result.costScope='Includes identity reads, three subprocesses, source media decoding, seven PNG writes, readback and cleanup; final JSON write excluded.';
  await fs.writeFile(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({status:result.status,wallSeconds:result.wallSeconds,decodedFrames:result.decodedFrames,images:result.images.length,error:result.error?.message,remainingChildPIDs:result.remainingChildPIDs}));
}
