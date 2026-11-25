import assert from 'node:assert/strict';

// Traverse a radius graph without allocating its (potentially dense) edge list.
// A point leaves its hash bucket immediately when its shortest hop count is discovered.
export function searchGraph(xyz,r,budget) {
  const n=xyz.length/3;
  const cell=Array.from({length:3},()=>new Int32Array(n));
  const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
  for(let i=0;i<n;i++)for(let k=0;k<3;k++){
    const v=Math.floor(xyz[3*i+k]/r);
    cell[k][i]=v;lo[k]=Math.min(lo[k],v);hi[k]=Math.max(hi[k],v);
  }
  const ny=hi[1]-lo[1]+3,nz=hi[2]-lo[2]+3,nx=hi[0]-lo[0]+3;
  assert(Number.isSafeInteger(nx*ny*nz));
  const key=new Float64Array(n),heads=new Map(),next=new Int32Array(n);
  for(let i=0;i<n;i++){
    const id=((cell[0][i]-lo[0]+1)*ny+(cell[1][i]-lo[1]+1))*nz+cell[2][i]-lo[2]+1;
    key[i]=id;next[i]=heads.get(id)??-1;heads.set(id,i);
  }
  const offsets=[];
  for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++)offsets.push((x*ny+y)*nz+z);
  const seen=new Int32Array(n).fill(-1),queue=new Int32Array(n);
  function expand(seeds) {
    let first=0,last=0;
    const hops=[];
    function add(i,d) {seen[i]=d;queue[last++]=i;hops[d]=(hops[d]??0)+1;}
    for(const i of seeds){assert.equal(seen[i],-1);add(i,0);}
    const r2=r*r;
    while(first<last) {
      if((first&1023)===0 && (performance.now()>budget.deadline || budget.tests>budget.limit))throw Error('Geometry budget exceeded');
      const i=queue[first++],d=seen[i]+1,start=key[i],a=i*3;
      for(const o of offsets) {
        const bucket=start+o;
        let j=heads.get(bucket)??-1,previous=-1;
        while(j!==-1) {
          const more=next[j];
          let remove=seen[j]!==-1;
          if(!remove) {
            const b=j*3,dx=xyz[a]-xyz[b],dy=xyz[a+1]-xyz[b+1],dz=xyz[a+2]-xyz[b+2];
            const d2=dx*dx+dy*dy+dz*dz;budget.tests++;
            if(d2<=r2 && Math.sqrt(d2)<r){add(j,d);remove=true;}
          }
          if(remove) {
            if(previous===-1)heads.set(bucket,more);else next[previous]=more;
          } else previous=j;
          j=more;
        }
      }
    }
    return {nodes:queue.subarray(0,last),hops};
  }
  return {expand,seen};
}

export function selfCheck() {
  const r=.25,points=[[0,0,0],[0,0,0],[r,0,0],[2*r,0,0],[r-Number.EPSILON,0,0],
    [-r,0,0],[-r+Number.EPSILON,0,0],[.5,1,.75],[100,100,100]];
  for(let i=0;i<137;i++)points.push([Math.sin(i*.51),Math.cos(i*.83),Math.sin(i*.712)]);
  const flat=Float64Array.from(points.flat()), seeds=[0,8,42],dist=points.map(()=>-1);
  const queue=[...seeds];for(const i of seeds)dist[i]=0;
  for(let k=0;k<queue.length;k++) {
    const i=queue[k];for(let j=0;j<points.length;j++)if(dist[j]<0) {
      const a=points[i],b=points[j],d=(a[0]-b[0])**2+(a[1]-b[1])**2+(a[2]-b[2])**2;
      if(d<=r*r && Math.sqrt(d)<r) {dist[j]=dist[i]+1;queue.push(j);}
    }
  }
  const s=searchGraph(flat,r,{tests:0,limit:1e9,deadline:Infinity});
  s.expand(seeds);assert.deepEqual([...s.seen],dist);
  // Native boundary recipients are enumerated but receive a zero heat increment.
  const two=searchGraph(Float64Array.from([0,0,0,r,0,0]),r,{tests:0,limit:1e9,deadline:Infinity});
  assert.equal(two.expand([0]).nodes.length,1);
  return {nodes:points.length,seeds:seeds.length,boundary:true};
}
