import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
if(!process.argv.includes('--execute')){console.log('One fixed existing-film frame at94s; --execute');process.exit(0);}
const here=path.dirname(fileURLToPath(import.meta.url)),out=path.join(here,'saved-anchor-94');
await fs.mkdir(out,{recursive:false});
const at=performance.now(),sha=b=>createHash('sha256').update(b).digest('hex');
const movie=path.join(here,'../a52-room-facing-away/film-01/room-facing-away.mp4');
const oldResult=path.join(here,'../a52-room-facing-away/film-01/result.json');
const originalHash=sha(await fs.readFile(oldResult)),movieHash=sha(await fs.readFile(movie));
const result={createdUTC:new Date().toISOString(),status:'started',encodedFrame:2256,seconds:94,limitSeconds:30,movieSHA256:movieHash,originalResultSHA256:originalHash,continuousViewing:false};
try{
 if(movieHash!=='635e62d7adc19759be525a2a54508635e6ef9c7dfbe082ec7e1049bafa5f69f3')throw Error('Movie identity mismatch');
 const args=['-hide_banner','-v','error','-nostdin','-n','-i',movie,'-vf','select=eq(n\\,2256)','-frames:v','1','-fps_mode','vfr',path.join(out,'94s.png')];
 result.args=args;
 const remaining=Math.floor(30000-(performance.now()-at));if(remaining<=0)throw Error('Deadline before extraction');
 const stdout=execFileSync('C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/Library/bin/ffmpeg.exe',args,{timeout:remaining,windowsHide:true,encoding:'utf8',maxBuffer:65536,stdio:['ignore','pipe','pipe']});
 result.exitCode=0;result.stdout=stdout;
 const b=await fs.readFile(path.join(out,'94s.png'));
 if(!b.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))||b.readUInt32BE(16)!==1280||b.readUInt32BE(20)!==720)throw Error('Image identity/dimensions mismatch');
 result.image={file:'94s.png',bytes:b.length,sha256:sha(b),width:1280,height:720};
 result.sourceUnchanged=sha(await fs.readFile(movie))===movieHash&&sha(await fs.readFile(oldResult))===originalHash;
 if(!result.sourceUnchanged)throw Error('Source identity changed');
 if(performance.now()-at>30000)throw Error('Deadline exceeded');
 result.status='extracted';
}catch(e){result.status='failed';result.error={message:e.message,status:e.status,signal:e.signal,stdout:e.stdout,stderr:e.stderr};process.exitCode=1;}
result.wallSeconds=(performance.now()-at)/1000;
await fs.writeFile(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));
