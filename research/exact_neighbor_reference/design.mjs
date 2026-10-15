export const PARAMS = Object.freeze({h:.30,beta:4,dt:1/60,safety:.9,maxSubsteps:100000});
export const SHAPES = Object.freeze({500:[10,25],5000:[50,50],50000:[100,250]});
export const PATTERNS = ['smooth','hotpatch','checkerboard'];
export const METHODS = ['allpairs-rebuild','hash-rebuild','hash-cached'];
export const ORDER = [METHODS,[METHODS[1],METHODS[2],METHODS[0]],
  [METHODS[2],METHODS[0],METHODS[1]],[METHODS[2],METHODS[1],METHODS[0]],
  [METHODS[0],METHODS[2],METHODS[1]]];
export function temperature(kind,[x,y,z],pattern) {
  if(pattern==='smooth') return kind==='surface' ? 320+40*(y-.1)/.8+20*(z+.4)/.8 : 600+80*(x+.2)/.4+60*(y-.1)/.8-40*(z+.4)/.8;
  if(pattern==='hotpatch') return kind==='gas' && (x*x+(y-.5)*(y-.5))+z*z < .12*.12 ? 900 : 300;
  if(pattern==='checkerboard') {const k=Math.floor((x+.017)/.125)+Math.floor((y+.031)/.125)+Math.floor((z+.047)/.125);return 300+500*((k%2+2)%2);}
  throw new Error(`unknown pattern ${pattern}`);
}
export function fixture(size,pattern) {
  const shape=SHAPES[size];if(!shape||!PATTERNS.includes(pattern))throw new Error('unknown fixture');
  const nodes=[],[ny,nz]=shape;
  function add(id,kind,position,measure,capacityPerMeasure){nodes.push({id,kind,position,measure,capacityPerMeasure,capacity:measure*capacityPerMeasure,temperature:temperature(kind,position,pattern)});}
  for(let side=0;side<2;side++)for(let iy=0;iy<ny;iy++)for(let iz=0;iz<nz;iz++)
    add(`s-${side}-${iy}-${iz}`,'surface',[side===0?-.2:.2,.1+(iy+.5)*.8/ny,-.4+(iz+.5)*.8/nz],1.28/size,2);
  for(let ix=0;ix<10;ix++)for(let iy=0;iy<10;iy++)for(let iz=0;iz<6;iz++)
    add(`g-${ix}-${iy}-${iz}`,'gas',[-.2+(ix+.5)*.4/10,.1+(iy+.5)*.8/10,-.4+(iz+.5)*.8/6],.256/600,3);
  return {surfaceCount:size,nodes};
}
export function definitions(){return Object.keys(SHAPES).map(Number).flatMap(size=>PATTERNS.map(pattern=>({id:`s${size}-${pattern}`,surfaceCount:size,gasCount:600,surfaceShape:SHAPES[size],pattern,steps:1,dt:PARAMS.dt})));}
