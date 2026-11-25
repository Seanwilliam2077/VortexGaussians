// The authoritative native heat stays in the float32 array. Projected shell
// arrays never reach this routine. A rewind/branch swap invalidates the bitmap.
let t106Index=null,t106Stats=null;
function t106Start(){
  if(t106Stats)throw Error('Nested sparse context');
  t106Stats={build_ms:0,builds:0,bitmap_bytes:0,initial_positive:[],scans:0,visited:0};t106Index=null;
}
function t106Stop(){const s=t106Stats;t106Stats=null;t106Index=null;return s;}
function t106Ensure(sb){
  if(t106Index?.heat===sb.h)return;
  const start=performance.now(),words=new Uint32Array(Math.ceil(sb.h.length/32));
  let positive=0;
  for(let i=0;i<sb.h.length;i++)if(sb.h[i]>0){words[i>>>5]|=1<<(i&31);positive++;}
  t106Index={heat:sb.h,words};t106Stats.builds++;t106Stats.bitmap_bytes+=words.byteLength;
  t106Stats.initial_positive.push(positive);t106Stats.build_ms+=performance.now()-start;
}
function t106Scan(sb,q,dt){
  const words=t106Index.words,decay=1-dt*.35;
  let visited=0;t106Stats.scans++;
  for(let w=0;w<words.length;w++){
    let bits=words[w];
    while(bits){
      const bit=bits & -bits,i=w*32+31-Math.clz32(bit);bits^=bit;visited++;
      if(sb.h[i]>0){
        sb.h[i]*=decay;
        if(sb.state[i]===0 && sb.fuel[i]>0 && sb.h[i]>=P.spreadIgnH){
          sb.state[i]=1;sb.burning.push(i);
          if(q && q.mask[i]){q.witness=i;t106Stats.visited+=visited;return true;}
        }
      }
      if(!(sb.h[i]>0))words[w]&=~bit;
    }
  }
  t106Stats.visited+=visited;return false;
}
const t106DenseQuery=window.__t90.query;
function t106Ordinary(method,h,dt){
  if(method!=='sparse-active')return t106DenseQuery(method,h,dt);
  const start=performance.now(),previous=stepSpread;
  t106Start();t102Start('active-anchor',dt);stepSpread=t106Spread;
  try {
    const answer=t102Previous('rank-only',h,dt);
    answer.active_stats=t102Stop();answer.cache_build=answer.active_stats;answer.sparse=t106Stop();
    answer.browser_ms=performance.now()-start;return answer;
  } finally {
    stepSpread=previous;if(t102Context)t102Stop();if(t106Stats)t106Stop();
  }
}
