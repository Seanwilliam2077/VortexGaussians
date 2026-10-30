// A52: one explicit world, one planar reflection. No image or room proxy in the mirror.
export const WIDTH = 1280;
export const HEIGHT = 720;
export const DURATION = 120;
const RAD = Math.PI / 180;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const smooth = x => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };
const add = (a, b) => a.map((x, i) => x + b[i]);
const sub = (a, b) => a.map((x, i) => x - b[i]);
const mul = (a, s) => a.map(x => x * s);
const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
const unit = a => mul(a, 1 / Math.max(1e-9, Math.hypot(...a)));

export const SPACE = Object.freeze({
  room: { x: [-3.4, 3.4], z: [-6.2, 0], height: 3.2 },
  door: { x: [-1.3, 1.5], z: 0, height: 2.65 },
  table: { center: [.7, .8675, -2.6], size: [1.8, .065, 1.4], top: .9 },
  cup: { base: [.03, .9, -3.09], radius: .115, height: .22, handleToward: [-.76, 0, .65] },
  chair: { center: [-.66, .5, -2.55], facing: [1, 0, 0] },
  mirror: { center: [0, 1.605, 3.5], width: 1.35, height: 2.05, yawDegrees: 12 },
  fire: { origin: [.18, .9, -2.12], scale: [.62, .70, .62], start: 46, sourceEnd: 58 },
  verticalFovDegrees: 48,
});

// Time, camera x, camera z, yaw from +z, downward pitch. Eye height is fixed.
// Hermite interpolation shares derivatives at knots; there are no cuts or per-request views.
export const CAMERA_KEYS = Object.freeze([
  [0, 2.55, -4.90, -45, 12], [12, 2.35, -4.50, -47, 12],
  [20, 2.20, -4.10, -42, 11], [24, 2.12, -3.83, -33, 9],
  [30, 1.92, -2.78, -18, 5], [34, 1.83, -1.85, -12, 4], [38, 1.15, -1.10, -8, 3],
  [46, .40, 1.00, -1, 3], [50, .47, 1.28, -3, 3],
  [60, .91, 1.35, -7, 3], [72, 1.45, 1.39, -11, 3],
  [84, 1.99, 1.43, -14, 3], [90, 2.26, 1.46, -18, 3],
  [94, 2.44, 1.48, -12, 3], [100, 2.72, 1.75, 15, 3],
  [104, 2.90, 2.05, 20, 3], [112, 3.10, 2.65, 7, 3],
  [120, 3.15, 3.25, 0, 3],
]);

function keyValue(t, col) {
  let i = 0;
  while (i < CAMERA_KEYS.length - 2 && t > CAMERA_KEYS[i + 1][0]) i++;
  const a = CAMERA_KEYS[i], b = CAMERA_KEYS[i + 1];
  const previous = CAMERA_KEYS[Math.max(0, i - 1)];
  const next = CAMERA_KEYS[Math.min(CAMERA_KEYS.length - 1, i + 2)];
  const dt = b[0] - a[0], u = clamp((t - a[0]) / dt, 0, 1);
  const ma = (b[col] - previous[col]) / (b[0] - previous[0]);
  const mb = (next[col] - a[col]) / (next[0] - a[0]);
  return (2*u*u*u - 3*u*u + 1)*a[col] + (u*u*u - 2*u*u + u)*dt*ma
    + (-2*u*u*u + 3*u*u)*b[col] + (u*u*u - u*u)*dt*mb;
}

export function cameraAt(seconds) {
  const t = clamp(seconds, 0, DURATION);
  const eye = [keyValue(t, 1), 1.62, keyValue(t, 2)];
  const yaw = keyValue(t, 3) * RAD, pitch = keyValue(t, 4) * RAD;
  const direction = [Math.sin(yaw)*Math.cos(pitch), -Math.sin(pitch), Math.cos(yaw)*Math.cos(pitch)];
  return { eye, target: add(eye, direction), yawDegrees: yaw/RAD, pitchDegrees: pitch/RAD };
}

function identity() { return new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]); }
function matrixMultiply(a, b) {
  const r = new Float32Array(16);
  for (let c=0;c<4;c++) for(let row=0;row<4;row++)
    for(let k=0;k<4;k++) r[c*4+row] += a[k*4+row] * b[c*4+k];
  return r;
}
function perspective(fov, aspect, near, far) {
  const f = 1/Math.tan(fov/2), n = 1/(near-far);
  return new Float32Array([f/aspect,0,0,0, 0,f,0,0, 0,0,(far+near)*n,-1, 0,0,2*far*near*n,0]);
}
function lookAt(eye, target) {
  const z=unit(sub(eye,target)), x=unit(cross([0,1,0],z)), y=cross(z,x);
  return new Float32Array([x[0],y[0],z[0],0, x[1],y[1],z[1],0, x[2],y[2],z[2],0, -dot(x,eye),-dot(y,eye),-dot(z,eye),1]);
}
const mirrorU = [Math.cos(12*RAD), 0, Math.sin(12*RAD)];
const mirrorN = [Math.sin(12*RAD), 0, -Math.cos(12*RAD)];
const mirrorM = SPACE.mirror.center;
const mirrorD = -dot(mirrorN, mirrorM);
export const MIRROR_PLANE = Object.freeze([...mirrorN, mirrorD]);
function reflectionMatrix() {
  const r=identity(), n=mirrorN;
  for(let c=0;c<3;c++) for(let row=0;row<3;row++) r[c*4+row] -= 2*n[c]*n[row];
  for(let row=0;row<3;row++) r[12+row] = -2*mirrorD*n[row];
  return r;
}
export function reflectedPoint(p) { return sub(p, mul(mirrorN, 2*(dot(mirrorN,p)+mirrorD))); }
export function mirrorIntersection(eye, point) {
  const virtual=reflectedPoint(point), ray=sub(virtual,eye);
  const f=-(dot(mirrorN,eye)+mirrorD)/dot(mirrorN,ray);
  const hit=add(eye,mul(ray,f));
  return { hit, u:dot(sub(hit,mirrorM),mirrorU), v:hit[1]-mirrorM[1], fraction:f };
}

class Mesh {
  constructor() { this.data=[]; }
  vertex(p,n,c,e=0) { this.data.push(...p,...n,...c,e); }
  tri(a,b,c,color,emission=0,normal=null) {
    const n=normal || unit(cross(sub(b,a),sub(c,a)));
    for(const p of [a,b,c]) this.vertex(p,n,color,emission);
  }
  quad(a,b,c,d,color,emission=0,normal=null) {
    this.tri(a,b,c,color,emission,normal); this.tri(a,c,d,color,emission,normal);
  }
  box(center,size,color,emission=0) {
    const [x,y,z]=center, [a,b,c]=size.map(v=>v/2);
    const p=[[x-a,y-b,z-c],[x+a,y-b,z-c],[x+a,y+b,z-c],[x-a,y+b,z-c],
      [x-a,y-b,z+c],[x+a,y-b,z+c],[x+a,y+b,z+c],[x-a,y+b,z+c]];
    for(const [a0,b0,c0,d0] of [[0,3,2,1],[4,5,6,7],[0,4,7,3],[1,2,6,5],[0,1,5,4],[3,7,6,2]])
      this.quad(p[a0],p[b0],p[c0],p[d0],color,emission);
  }
  rod(a,b,r,color,sides=10) {
    const along=unit(sub(b,a)), u=unit(cross(along,Math.abs(along[1])>.9?[1,0,0]:[0,1,0]));
    const v=cross(along,u);
    for(let j=0;j<sides;j++) {
      const phi=j*2*Math.PI/sides, psi=(j+1)*2*Math.PI/sides;
      const na=add(mul(u,Math.cos(phi)),mul(v,Math.sin(phi)));
      const nb=add(mul(u,Math.cos(psi)),mul(v,Math.sin(psi)));
      const aa=add(a,mul(na,r)), ab=add(a,mul(nb,r)), ba=add(b,mul(na,r)), bb=add(b,mul(nb,r));
      this.quad(aa,ab,bb,ba,color); this.tri(a,ab,aa,color,0,mul(along,-1)); this.tri(b,ba,bb,color,0,along);
    }
  }
}

const C = {
  wall:[.43,.435,.41], hall:[.405,.425,.413], floor:[.285,.266,.235], ceiling:[.37,.385,.373],
  wood:[.285,.205,.135], edge:[.095,.075,.058], metal:[.115,.135,.13], seat:[.235,.225,.185],
  white:[.87,.85,.78], window:[.48,.53,.53], frame:[.24,.265,.255],
};
function verticalWall(mesh,a,b,height,color) {
  mesh.quad([a[0],0,a[1]],[b[0],0,b[1]],[b[0],height,b[1]],[a[0],height,a[1]],color);
}
function mirrorQuad(mesh,width,height,color,offset=0,emission=0) {
  const center=add(mirrorM,mul(mirrorN,offset)), u=mul(mirrorU,width/2), v=[0,height/2,0];
  mesh.quad(sub(sub(center,u),v),add(sub(center,v),u),add(add(center,u),v),add(sub(center,u),v),color,emission,mirrorN);
}
function cup(mesh) {
  const [x,y,z]=SPACE.cup.base, h=.22, outer=.115, inner=.09, n=40;
  for(let i=0;i<n;i++) {
    const a=i*Math.PI*2/n,b=(i+1)*Math.PI*2/n;
    const p=(r,yy,phi)=>[x+r*Math.cos(phi),yy,z+r*Math.sin(phi)];
    mesh.quad(p(outer,y,a),p(outer,y,b),p(outer,y+h,b),p(outer,y+h,a),C.white);
    mesh.quad(p(inner,y+.045,b),p(inner,y+.045,a),p(inner,y+h,a),p(inner,y+h,b),[.54,.535,.495]);
    mesh.quad(p(outer,y+h,a),p(outer,y+h,b),p(inner,y+h,b),p(inner,y+h,a),[.94,.92,.85]);
    mesh.tri([x,y+.044,z],p(inner,y+.044,a),p(inner,y+.044,b),[.40,.39,.35],0,[0,1,0]);
  }
  const d=unit(SPACE.cup.handleToward), side=unit(cross(d,[0,1,0]));
  const center=add([x,y+.115,z],mul(d,.125));
  const p=(a,b)=>add(add(center,mul(d,(.092+.020*Math.cos(b))*Math.cos(a))),
    add([0,(.092+.020*Math.cos(b))*Math.sin(a),0],mul(side,.020*Math.sin(b))));
  for(let i=0;i<28;i++) for(let j=0;j<8;j++) {
    const a=i*2*Math.PI/28,b=(i+1)*2*Math.PI/28,c=j*2*Math.PI/8,d0=(j+1)*2*Math.PI/8;
    mesh.quad(p(a,c),p(b,c),p(b,d0),p(a,d0),C.white);
  }
}
function makeWorld() {
  const m=new Mesh();
  // Room shell, with a genuinely absent door rectangle.
  m.box([0,-.075,-3.1],[6.8,.15,6.2],C.floor);
  m.box([0,3.25,-3.1],[6.9,.10,6.3],C.ceiling);
  m.box([0,1.6,-6.25],[6.9,3.2,.10],C.wall);
  m.box([-3.45,1.6,-3.1],[.1,3.2,6.2],C.wall);
  m.box([3.45,1.6,-3.1],[.1,3.2,6.2],C.wall);
  m.box([-2.35,1.6,0],[2.1,3.2,.16],C.wall);
  m.box([2.45,1.6,0],[1.9,3.2,.16],C.wall);
  m.box([.1,2.925,0],[2.8,.55,.16],C.wall);
  for(const x of [-1.33,1.53]) m.box([x,1.33,-.045],[.07,2.66,.22],[.29,.30,.275]);
  m.box([.1,2.68,-.045],[2.93,.07,.22],[.29,.30,.275]);
  m.box([.1,.012,0],[2.8,.024,.25],[.33,.31,.27]);
  // Open leaf stands inward, perpendicular to the doorway plane.
  m.box([1.565,1.31,-.66],[.055,2.60,1.27],[.285,.284,.247]);
  m.rod([1.53,1.04,-1.16],[1.44,1.04,-1.16],.024,C.metal);
  m.rod([1.44,1.04,-1.16],[1.44,1.04,-1.03],.017,C.metal);
  // Quiet gray window: no image, exterior scene or autobiographical details.
  m.box([-3.382,1.85,-3.1],[.025,1.42,2.15],C.frame);
  m.box([-3.363,1.85,-3.1],[.014,1.31,2.04],C.window,.25);
  m.box([-3.30,1.15,-3.1],[.18,.055,2.22],[.35,.37,.345]);
  m.box([-3.388,.065,-3.1],[.024,.13,6.1],[.25,.26,.238]);
  m.box([3.388,.065,-3.1],[.024,.13,6.1],[.25,.26,.238]);
  m.box([0,.065,-6.188],[6.76,.13,.024],[.25,.26,.238]);
  // Table: pale highlights reveal its dark narrow rim throughout the shot.
  m.box(SPACE.table.center,SPACE.table.size,C.wood);
  m.box([.7,.898,-3.294],[1.80,.025,.020],C.edge);
  m.box([.7,.898,-1.906],[1.80,.025,.020],C.edge);
  m.box([-.194,.898,-2.6],[.020,.025,1.40],C.edge);
  m.box([1.594,.898,-2.6],[.020,.025,1.40],C.edge);
  for(const x of [-.08,1.48]) for(const z of [-3.18,-2.02]) m.box([x,.42,z],[.075,.84,.075],[.235,.17,.115]);
  m.box([.7,.775,-3.17],[1.63,.13,.035],[.25,.18,.12]);
  m.box([.7,.775,-2.03],[1.63,.13,.035],[.25,.18,.12]);
  // A folding chair with physical crossed legs and a separated back crossbar.
  m.box([-.66,.515,-2.55],[.61,.055,.61],C.seat);
  for(const z of [-2.82,-2.28]) {
    m.rod([-1.025,.045,z],[-.36,.55,z],.019,C.metal);
    m.rod([-.31,.045,z],[-1.02,1.27,z],.019,C.metal);
    m.rod([-.97,.50,z],[-1.02,1.27,z],.019,C.metal);
  }
  m.rod([-1.02,1.26,-2.82],[-1.02,1.26,-2.28],.023,C.metal);
  m.rod([-1.00,.98,-2.82],[-1.00,.98,-2.28],.022,C.metal);
  m.box([-1.01,1.15,-2.55],[.035,.14,.55],C.seat);
  m.rod([-.32,.08,-2.82],[-.32,.08,-2.28],.017,C.metal);
  cup(m);
  // Corridor has a right-hand continuation, then a bend toward +z.
  m.box([.55,-.075,1.99],[7.9,.15,4.0],[.30,.305,.282]);
  m.box([3.5,-.075,6.1],[2.0,.15,4.3],[.30,.305,.282]);
  m.box([.55,3.25,1.99],[7.9,.10,4.0],C.ceiling);
  m.box([3.5,3.25,6.1],[2.0,.10,4.3],C.ceiling);
  m.box([-3.45,1.6,2.0],[.1,3.2,4.0],C.hall);
  m.box([4.55,1.6,4.1],[.1,3.2,8.2],C.hall);
  m.box([3.5,1.6,8.25],[2.1,3.2,.1],C.hall);
  m.box([2.45,1.6,6.1],[.1,3.2,4.3],C.hall);
  m.box([3.5,1.6,-.02],[2.0,3.2,.1],C.hall);
  // The opposite wall's small angled facet supports the mirror plane.
  const wallCenter=sub(mirrorM,mul(mirrorN,.026)), half=mul(mirrorU,1.05);
  const left=sub(wallCenter,half), right=add(wallCenter,half);
  verticalWall(m,[-3.4,4.0],[left[0],left[2]],3.2,C.hall);
  verticalWall(m,[left[0],left[2]],[right[0],right[2]],3.2,C.hall);
  verticalWall(m,[right[0],right[2]],[2.5,4.0],3.2,C.hall);
  // Sparse architectural joints, with no labels or added possessions.
  for(const z of [-4.0,-1.65,1.05,3.55,5.85]) {
    if(z<0) m.box([0,.001,z],[6.76,.002,.005],[.27,.25,.223]);
    else if(z<4) m.box([.55,.001,z],[7.84,.002,.006],[.278,.285,.262]);
    else m.box([3.5,.001,z],[1.98,.002,.006],[.278,.285,.262]);
  }
  return m;
}
function makeMirrorFrame() {
  const m=new Mesh(), w=SPACE.mirror.width, h=SPACE.mirror.height;
  const corner=(u,v,offset)=>add(add(mirrorM,mul(mirrorU,u)),add([0,v,0],mul(mirrorN,offset)));
  const line=(a,b)=>m.rod(a,b,.022,[.14,.155,.15],8);
  line(corner(-w/2,-h/2,.011),corner(w/2,-h/2,.011));
  line(corner(-w/2,h/2,.011),corner(w/2,h/2,.011));
  line(corner(-w/2,-h/2,.011),corner(-w/2,h/2,.011));
  line(corner(w/2,-h/2,.011),corner(w/2,h/2,.011));
  return m;
}

const meshVertex = `
attribute vec3 aPosition; attribute vec3 aNormal; attribute vec3 aColor; attribute float aEmission;
uniform mat4 uVP; varying vec3 vPosition; varying vec3 vNormal; varying vec3 vColor; varying float vEmission;
void main(){vPosition=aPosition;vNormal=aNormal;vColor=aColor;vEmission=aEmission;gl_Position=uVP*vec4(aPosition,1.0);}`;
const meshFragment = `
precision highp float;
varying vec3 vPosition; varying vec3 vNormal; varying vec3 vColor; varying float vEmission;
uniform vec4 uPlane; uniform float uClip; uniform float uFire; uniform float uTime; uniform float uFlat; uniform vec4 uFlatColor;
void main(){
 if(uClip>0.5 && dot(uPlane,vec4(vPosition,1.0))<0.002) discard;
 if(uFlat>0.5){gl_FragColor=uFlatColor;return;}
 vec3 n=normalize(vNormal); if(!gl_FrontFacing)n=-n;
 float windowLight=max(0.0,dot(n,normalize(vec3(-0.65,0.85,-0.35))));
 float overhead=max(0.0,n.y);
 float ambient=0.37+0.08*clamp(vPosition.y/3.2,0.0,1.0);
 vec3 color=vColor*(ambient+0.40*windowLight+0.13*overhead);
 vec3 light=vec3(0.18,1.24,-2.12)-vPosition;float d=length(light);
 float nearFire=max(0.0,1.0-d/4.1);nearFire*=nearFire;
 float lambert=max(0.0,dot(n,normalize(light)));
 float pulse=1.0+0.055*sin(uTime*9.7)+0.035*sin(uTime*16.13+0.8);
 color+=vColor*vec3(1.0,0.45,0.10)*uFire*nearFire*(0.24+0.95*lambert)*pulse;
 // Very low amplitude analytic finish; it is not a photographic texture.
 float grain=sin(vPosition.x*39.0+vPosition.z*17.0)*sin(vPosition.y*41.0-vPosition.z*31.0);
 color*=1.0+0.009*grain;
 color+=vColor*vEmission;
 // Small contact fields are authored shading, not claimed shadow transport.
 if(vPosition.y<0.02 && vPosition.z<0.0){
   vec2 q=(vPosition.xz-vec2(0.7,-2.6))/vec2(1.18,.99);
   color*=1.0-0.16*exp(-dot(q,q)*2.0);
 }
 color=pow(max(color,vec3(0.0)),vec3(0.77));
 gl_FragColor=vec4(color,1.0);
}`;
const fireVertex = `
attribute vec3 aPosition; attribute vec3 aState;
uniform mat4 uVP; uniform mat4 uView; uniform float uPixelScale;
varying vec3 vState; varying vec3 vPosition;
void main(){vState=aState;vPosition=aPosition;gl_Position=uVP*vec4(aPosition,1.0);
 float depth=max(0.1,-(uView*vec4(aPosition,1.0)).z);
 gl_PointSize=clamp(2.0*aState.z*uPixelScale/depth,1.0,72.0);}`;
const fireFragment = `
precision highp float; varying vec3 vState; varying vec3 vPosition;
uniform float uFireAlpha; uniform vec4 uPlane; uniform float uClip;
void main(){
 if(uClip>0.5 && dot(uPlane,vec4(vPosition,1.0))<0.002) discard;
 vec2 q=gl_PointCoord*2.0-1.0;q.x*=1.25;
 float r=dot(q,q);if(r>1.0)discard;
 float temperature=clamp(vState.x,0.0,1.0), density=clamp(vState.y,0.0,1.0);
 float edge=pow(1.0-r,1.65);
 float alpha=edge*(.15+.24*density)*uFireAlpha*(.36+.64*temperature);
 vec3 color=mix(vec3(.52,.07,.012),vec3(1.0,.46,.055),smoothstep(.13,.62,temperature));
 color=mix(color,vec3(1.0,.88,.50),smoothstep(.60,1.0,temperature)*(1.0-.48*r));
 gl_FragColor=vec4(color*alpha,alpha);
}`;
function program(gl,vs,fs) {
  const compile=(type,code)=>{
    const shader=gl.createShader(type);gl.shaderSource(shader,code);gl.compileShader(shader);
    if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(shader));
    return shader;
  };
  const a=compile(gl.VERTEX_SHADER,vs),b=compile(gl.FRAGMENT_SHADER,fs),p=gl.createProgram();
  gl.attachShader(p,a);gl.attachShader(p,b);gl.linkProgram(p);gl.deleteShader(a);gl.deleteShader(b);
  if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(p));
  return p;
}
function uniforms(gl,p,names){return Object.fromEntries(names.map(n=>[n,gl.getUniformLocation(p,n)]));}

export function createScene(canvas) {
  const gl=canvas.getContext('webgl',{alpha:false,antialias:true,depth:true,stencil:true,preserveDrawingBuffer:true,premultipliedAlpha:false});
  if(!gl)throw new Error('WebGL is unavailable.');
  if(gl.getParameter(gl.STENCIL_BITS)<1)throw new Error('A stencil buffer is required for the planar mirror.');
  canvas.width=WIDTH;canvas.height=HEIGHT;
  const meshProgram=program(gl,meshVertex,meshFragment),fireProgram=program(gl,fireVertex,fireFragment);
  const mu=uniforms(gl,meshProgram,['uVP','uPlane','uClip','uFire','uTime','uFlat','uFlatColor']);
  const fu=uniforms(gl,fireProgram,['uVP','uView','uPixelScale','uFireAlpha','uPlane','uClip']);
  const ma=['aPosition','aNormal','aColor','aEmission'].map(n=>gl.getAttribLocation(meshProgram,n));
  const fa=['aPosition','aState'].map(n=>gl.getAttribLocation(fireProgram,n));
  const buffers=[];
  const upload=mesh=>{
    const buffer=gl.createBuffer();buffers.push(buffer);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
    gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(mesh.data),gl.STATIC_DRAW);
    return {buffer,count:mesh.data.length/10};
  };
  const world=upload(makeWorld()),frame=upload(makeMirrorFrame());
  const planeMesh=new Mesh();mirrorQuad(planeMesh,SPACE.mirror.width,SPACE.mirror.height,[.1,.1,.1]);
  const mirror=upload(planeMesh),fireBuffer=gl.createBuffer();buffers.push(fireBuffer);
  const projection=perspective(SPACE.verticalFovDegrees*RAD,WIDTH/HEIGHT,.045,40),reflection=reflectionMatrix();
  const pixelScale=HEIGHT/(2*Math.tan(SPACE.verticalFovDegrees*RAD/2));
  const allLocations=[...new Set([...ma,...fa])];
  let last=null,disposed=false;
  function bindMesh(mesh,vp,time,fire,clip,flat=null) {
    gl.useProgram(meshProgram);
    for(const a of allLocations)gl.disableVertexAttribArray(a);
    gl.bindBuffer(gl.ARRAY_BUFFER,mesh.buffer);
    for(let i=0;i<4;i++){gl.enableVertexAttribArray(ma[i]);gl.vertexAttribPointer(ma[i],i===3?1:3,gl.FLOAT,false,40,i*12);}
    gl.uniformMatrix4fv(mu.uVP,false,vp);gl.uniform4fv(mu.uPlane,MIRROR_PLANE);
    gl.uniform1f(mu.uClip,clip?1:0);gl.uniform1f(mu.uFire,fire);gl.uniform1f(mu.uTime,time);
    gl.uniform1f(mu.uFlat,flat?1:0);gl.uniform4fv(mu.uFlatColor,flat||[0,0,0,1]);
    gl.drawArrays(gl.TRIANGLES,0,mesh.count);
  }
  function drawFire(points,vp,view,time,clip) {
    if(time<=46||points.length===0)return;
    const ordered=points.map(p=>({p,world:[.18+.62*p.x,.9+.70*p.y,-2.12+.62*p.z]}));
    // Conventional back-to-front transparency, preserving opaque table/chair/door depth.
    ordered.sort((a,b)=>{
      const depth=p=>view[2]*p.world[0]+view[6]*p.world[1]+view[10]*p.world[2]+view[14];
      return depth(a)-depth(b);
    });
    const values=new Float32Array(ordered.length*6);
    ordered.forEach(({p,world},i)=>values.set([...world,p.temperature,p.density,.70*p.radius],i*6));
    gl.useProgram(fireProgram);for(const a of allLocations)gl.disableVertexAttribArray(a);
    gl.bindBuffer(gl.ARRAY_BUFFER,fireBuffer);gl.bufferData(gl.ARRAY_BUFFER,values,gl.DYNAMIC_DRAW);
    for(let i=0;i<2;i++){gl.enableVertexAttribArray(fa[i]);gl.vertexAttribPointer(fa[i],3,gl.FLOAT,false,24,i*12);}
    gl.uniformMatrix4fv(fu.uVP,false,vp);gl.uniformMatrix4fv(fu.uView,false,view);
    gl.uniform1f(fu.uPixelScale,pixelScale);gl.uniform1f(fu.uFireAlpha,smooth((time-46)/3));
    gl.uniform4fv(fu.uPlane,MIRROR_PLANE);gl.uniform1f(fu.uClip,clip?1:0);
    gl.enable(gl.BLEND);gl.blendFunc(gl.ONE,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false);
    gl.drawArrays(gl.POINTS,0,ordered.length);
    gl.depthMask(true);gl.disable(gl.BLEND);
  }
  function renderAt(seconds,points=[]) {
    if(disposed)throw new Error('The scene has been disposed.');
    const time=clamp(seconds,0,DURATION),camera=cameraAt(time);
    const view=lookAt(camera.eye,camera.target),vp=matrixMultiply(projection,view);
    const reflectedView=matrixMultiply(view,reflection),reflectedVP=matrixMultiply(projection,reflectedView);
    const fire=smooth((time-46)/14)*1.42;
    gl.viewport(0,0,WIDTH,HEIGHT);gl.clearColor(.25,.27,.255,1);gl.clearDepth(1);gl.clearStencil(0);
    gl.colorMask(true,true,true,true);gl.depthMask(true);gl.stencilMask(0xff);
    gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT|gl.STENCIL_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.disable(gl.CULL_FACE);gl.disable(gl.BLEND);gl.disable(gl.STENCIL_TEST);
    bindMesh(world,vp,time,fire,false);bindMesh(frame,vp,time,fire,false);
    // Stamp only pixels of the physical mirror that pass the main scene's depth test.
    gl.enable(gl.STENCIL_TEST);gl.stencilFunc(gl.ALWAYS,1,0xff);gl.stencilOp(gl.KEEP,gl.KEEP,gl.REPLACE);
    gl.colorMask(false,false,false,false);gl.depthMask(false);
    bindMesh(mirror,vp,time,fire,false,[0,0,0,1]);
    gl.stencilMask(0x00);gl.stencilFunc(gl.EQUAL,1,0xff);gl.stencilOp(gl.KEEP,gl.KEEP,gl.KEEP);
    // Reset depth to the far plane exclusively inside the visible stencil rectangle.
    gl.depthMask(true);gl.depthFunc(gl.ALWAYS);gl.depthRange(1,1);gl.colorMask(true,true,true,true);
    bindMesh(mirror,vp,time,fire,false,[.23,.255,.245,1]);
    gl.depthRange(0,1);gl.depthFunc(gl.LEQUAL);
    // Exactly the same original world buffers, through view * planar reflection.
    gl.frontFace(gl.CW); // Reflection reverses handedness; retain original surface lighting.
    bindMesh(world,reflectedVP,time,fire,true);
    drawFire(points,reflectedVP,reflectedView,time,true);
    gl.frontFace(gl.CCW);
    // A restrained silver coating also restores the physical mirror's surface depth.
    gl.depthFunc(gl.ALWAYS);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
    bindMesh(mirror,vp,time,fire,false,[.48,.53,.51,.065]);
    gl.disable(gl.BLEND);gl.depthFunc(gl.LEQUAL);gl.disable(gl.STENCIL_TEST);gl.stencilMask(0xff);
    drawFire(points,vp,view,time,false);
    last={seconds:time,camera:{eye:camera.eye.map(v=>+v.toFixed(5)),yawDegrees:+camera.yawDegrees.toFixed(5),pitchDegrees:+camera.pitchDegrees.toFixed(5)},
      particles:points.length,fireLight:+fire.toFixed(5),mirrorPasses:1,worldTriangles:world.count/3};
    return last;
  }
  return {
    renderAt,
    inspect:()=>({last,dimensions:[WIDTH,HEIGHT],space:SPACE,mirrorPlane:MIRROR_PLANE,
      technique:'shared world geometry; stencil-constrained single planar reflection; ordinary premultiplied point sprites; authored local fire lighting',
      physicalDestruction:false,recursiveReflection:false}),
    dispose(){if(disposed)return;disposed=true;for(const b of buffers)gl.deleteBuffer(b);gl.deleteProgram(meshProgram);gl.deleteProgram(fireProgram);},
  };
}
