// The two views expose the nonnegative binary32 value and its monotone integer encoding.
const wordView=new Uint32Array(1), floatView=new Float32Array(wordView.buffer);
export const width=0x800000;
export function bits(x){floatView[0]=x;return wordView[0];}
export function value(word){wordView[0]=word;return floatView[0];}
export function serial(h,ds){for(const d of ds)h=Math.fround(h+d);return h;}

export function descriptor(block, ds) {
  // Two normal, interior starts with opposite stored significand parity.
  if(block<=0 || block>=255)return null;
  const base=block*width;
  const shift=[];
  for(const parity of [0,1]){
    const origin=base+2+parity;
    const target=bits(serial(value(origin),ds));
    shift.push(target>=origin && target<base+width-1 ? target-origin : null);
  }
  return shift;
}

export function lookup(word,rule) {
  if(!rule)return null;
  const start=word%width, advance=rule[word%2];
  if(advance===null || start===0 || start+advance>=width-1)return null;
  return word+advance;
}

export function presummed(ds){let sum=0;for(const d of ds)sum+=d;return sum;}
