"""Headless driver for demo/index.html, built on the page's own __demo hooks.

Usage:  python tools/harness.py <command> [--adapter high|low] ...
Needs:  pip install playwright pillow numpy  (uses the installed Chrome, no browser download)

Commands
  hash       deterministic-replay anchors, for checking a change left the solver alone
  bench      per-frame cost of the shipping presets on the selected GPU
  deflect    plume deflection around a sphere obstacle, solver path on vs. off
  light      cost and effect of the world-space fire light on a loaded scene
  shots      high-resolution stills
  video      a short 1080p take of the quality preset
"""
import argparse, base64, functools, http.server, io, json, os, shutil, socketserver, statistics
import subprocess, sys, threading
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
QUALITY = dict(ppl=1300, theta=0.7, layers=9, simLayers=9)
# offline look: more elements so a smaller radius still tiles (paper Fig. 8), and an emission
# low enough that the core keeps structure instead of clipping to white
HERO = dict(ppl=3000, theta=0.7, layers=9, simLayers=9, rad=20, emitN=16, emis=2.0, thresh=0.9, bloom=0.7, covMax=5.0)
INTERACTIVE = dict(ppl=600, theta=0.9, layers=9, simLayers=9)


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    handler.log_message = lambda *a, **k: None
    srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), handler)
    srv.RequestHandlerClass = type('Quiet', (http.server.SimpleHTTPRequestHandler,), dict(log_message=lambda *a: None,
        __init__=lambda self, *a, **k: http.server.SimpleHTTPRequestHandler.__init__(self, *a, directory=str(ROOT), **k)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


class Page:
    def __init__(self, adapter='high', size=(1280, 800), demo='demo/'):
        self.srv, port = serve()
        self.pw = sync_playwright().start()
        gpu = '--force_high_performance_gpu' if adapter == 'high' else '--force_low_power_gpu'
        self.browser = self.pw.chromium.launch(channel='chrome', headless=True, args=[
            '--use-gl=angle', '--use-angle=d3d11', '--ignore-gpu-blocklist', '--enable-gpu',
            '--disable-frame-rate-limit', '--disable-gpu-vsync', gpu])
        self.page = self.browser.new_page(viewport=dict(width=size[0], height=size[1]))
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.goto(f'http://127.0.0.1:{port}/{demo}')
        self.page.wait_for_function('window.__demo!==undefined')
        self.page.evaluate('''([w,h])=>{ const D=__demo; D.P.paused=true; D.P.orbit=false;
            document.getElementById('panel').style.display='none'; D.forceSize(w,h); }''', list(size))

    def js(self, code, arg=None):
        return self.page.evaluate(code, arg)

    def renderer(self):
        return self.js('''()=>{ const g=__demo.gl, e=g.getExtension('WEBGL_debug_renderer_info');
            return e?g.getParameter(e.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER); }''')

    def load_ply(self, rel):
        data = (ROOT / rel).read_bytes()
        self.js('''async b=>{ const s=atob(b), u=new Uint8Array(s.length);
            for(let i=0;i<s.length;i++) u[i]=s.charCodeAt(i);
            return __demo.loadPLY(u.buffer); }''', base64.b64encode(data).decode())

    def grab(self):
        """Render and read the canvas back as an RGB array."""
        b64 = self.js('''()=>{ __demo.render(); return document.getElementById('cv').toDataURL('image/png').split(',')[1]; }''')
        return np.asarray(Image.open(io.BytesIO(base64.b64decode(b64))).convert('RGB'))

    def close(self):
        if self.errors:
            print('page errors:', self.errors[:3], file=sys.stderr)
        self.browser.close(); self.pw.stop(); self.srv.shutdown()


def preset(page, cfg):
    page.js('c=>{ Object.assign(__demo.P,c); __demo.rebuild(); }', cfg)


def cmd_hash(a):
    p = Page(a.adapter, demo=a.demo)
    out = {}
    for name, cfg in (('interactive', INTERACTIVE), ('quality', QUALITY)):
        preset(p, cfg)
        for seed in (42, 12345):
            out[f'{name}/{seed}'] = p.js('s=>{ __demo.reset(s); __demo.step(120); return __demo.hash(); }', seed)
    print(json.dumps(dict(renderer=p.renderer(), hashes=out), indent=1))
    p.close()


def cmd_bench(a):
    """__demo.bench() does not wait for the GPU, so frames are timed here with a readback."""
    p = Page(a.adapter, (1280, 800))
    if a.scene:
        p.load_ply(a.scene)
    rows = []
    for label, cfg in (('interactive', INTERACTIVE), ('quality', QUALITY)):
        preset(p, cfg)
        runs = []
        for seed in (7, 11, 17, 23, 42):
            runs.append(p.js('''s=>{ const D=__demo, gl=D.gl, px=new Uint8Array(4);
                D.P.box=false; D.reset(s); D.step(120);
                let t0=performance.now(); D.step(120); const sim=(performance.now()-t0)/120;
                D.render(); gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,px);
                t0=performance.now();
                for(let i=0;i<60;i++){ D.render(); gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,px); }
                const draw=(performance.now()-t0)/60;
                return {sim, draw, total:sim+draw, gaussians:D.render()}; }''', seed))
        row = {k: round(statistics.median(r[k] for r in runs), 2) for k in ('sim', 'draw', 'total', 'gaussians')}
        row['fps'] = round(1000 / row['total'], 1)
        rows.append(dict(label=label, **row))
    print(json.dumps(dict(renderer=p.renderer(), scene=a.scene or None, sceneN=p.js('()=>__demo.sceneN'), rows=rows), indent=1))
    p.close()

def plume_stats(p):
    """Mean and spread of hot particles in the band above the obstacle."""
    pts = np.array(p.js('()=>__demo.particles()'))
    return pts


def cmd_deflect(a):
    """Sphere on the plume axis at y=1.0. Twenty paired seeds, solver path off then on."""
    p = Page(a.adapter)
    preset(p, INTERACTIVE)
    p.js('()=>{ __demo.P.sliceMode="world"; __demo.P.box=false; }')
    R = 0.24
    sphere = dict(x=0.0, y=1.0, z=0.0, r=R)
    res = {'off': [], 'on': []}
    for seed in a.seeds:
        for mode in ('off', 'on'):
            acc = []
            p.js('''([m,s,o])=>{ const D=__demo; D.P.obstOn=(m==='on'); D.obstacles([o]); D.reset(s); D.step(360); }''',
                 [mode, seed, sphere])
            for _ in range(12):
                p.js('()=>__demo.step(5)')
                acc.append(plume_stats(p))
            pts = np.concatenate(acc)
            hot = pts[pts[:, 3] > 0.15]
            # 3D distance: outer slices pass beside the sphere, and a particle pushed to the
            # slice circle sits exactly on the surface, so test just inside it
            d = np.sqrt(hot[:, 0] ** 2 + (hot[:, 1] - 1.0) ** 2 + hot[:, 2] ** 2)
            inside = float(np.mean(d < R * 0.97))
            bin_in_core = hot[(np.abs(hot[:, 1] - 1.0) < 0.05)]
            axial = float(np.mean(np.abs(bin_in_core[:, 0]) < 0.12)) if len(bin_in_core) else float('nan')
            above = hot[(hot[:, 1] > 1.3) & (hot[:, 1] < 1.8)]
            res[mode].append(dict(seed=seed, n=int(len(hot)), inside=inside, axial=axial,
                                  width=float(np.std(above[:, 0])) if len(above) else float('nan')))
    summary = {m: {k: float(np.nanmean([r[k] for r in v])) for k in ('inside', 'axial', 'width')} for m, v in res.items()}
    # cost of the path itself, measured at the same preset
    cost = {}
    for mode in ('off', 'on'):
        cost[mode] = p.js('''([m,o])=>{ const D=__demo; D.P.obstOn=(m==='on'); D.obstacles(Array.from({length:12},(_,i)=>({x:o.x+(i-5.5)*0.15,y:o.y,z:o.z,r:0.1})));
            const r=D.bench([{solver:'vpm',layers:9,ppl:600,seed:42,warm:90,frames:180}]).configs[0]; return r.simMs; }''', [mode, sphere])
    print(json.dumps(dict(renderer=p.renderer(), seeds=a.seeds, radius=R, summary=summary, simMs=cost, runs=res), indent=1))
    p.close()


def cmd_light(a):
    p = Page(a.adapter)
    p.load_ply('static/test_scene.ply')
    preset(p, INTERACTIVE)
    p.js('()=>{ const P=__demo.P; P.sceneLight=0.25; __demo.reset(42); __demo.step(240); }')
    t = {}
    for on in (False, True):
        p.js('v=>{ __demo.P.fireLight=v; }', on)
        t['on' if on else 'off'] = p.js('''()=>{ const n=40; __demo.render(); const gl=__demo.gl, b=new Uint8Array(4);
            const t0=performance.now(); for(let i=0;i<n;i++){ __demo.render(); gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,b); }
            return (performance.now()-t0)/n; }''')
    p.js('()=>{ __demo.P.fireLight=false; }'); off = p.grab().astype(float)
    p.js('()=>{ __demo.P.fireLight=true; }'); on = p.grab().astype(float)
    print(json.dumps(dict(renderer=p.renderer(), frameMs=t, meanLumaOff=off.mean(), meanLumaOn=on.mean(),
                          lights=p.js('()=>__demo.lights()')), indent=1))
    p.close()


def save(arr, path):
    os.makedirs(Path(path).parent, exist_ok=True)
    Image.fromarray(arr).save(path, quality=93)
    print('wrote', path)


def cmd_shots(a):
    out = Path(a.out)
    p = Page(a.adapter, (1920, 1200))
    for name, cfg in (('quality', QUALITY), ('hero', HERO)):
        preset(p, cfg)
        p.js('()=>{ __demo.P.box=false; __demo.reset(42); __demo.step(300); }')
        img = p.grab(); save(img, out / f'fire_{name}.jpg')
        grey = img.astype(float).mean(axis=2)
        print(name, 'gaussians', p.js('()=>__demo.count'), 'mean gradient', float(np.mean(np.hypot(*np.gradient(grey)))))

    p.load_ply('static/test_scene.ply')
    p.js('()=>{ const P=__demo.P; P.sceneLight=0.22; P.camDist=4.0; P.camElev=0.24; __demo.reset(42); __demo.step(300); }')
    for flag, name in ((False, 'light_off'), (True, 'light_on')):
        p.js('v=>{ __demo.P.fireLight=v; }', flag)
        save(p.grab(), out / f'{name}.jpg')
    p.close()


def cmd_deflect_shots(a):
    out = Path(a.out)
    p = Page(a.adapter, (1400, 1000))
    preset(p, HERO)
    p.js('()=>{ const P=__demo.P; P.sliceMode="world"; P.box=false; P.camElev=0.12; P.camDist=4.4; P.yaw=0; }')
    sphere = dict(x=0.0, y=1.0, z=0.0, r=0.24)
    for mode in ('off', 'on'):
        p.js('''([m,o])=>{ const D=__demo; D.P.obstOn=(m==='on'); D.obstacles([o]); D.reset(42); D.step(360); }''', [mode, sphere])
        save(p.grab(), out / f'deflect_{mode}.jpg')
    p.close()


def cmd_video(a):
    import imageio_ffmpeg
    w, h = 1920, 1080
    p = Page(a.adapter, (w, h))
    preset(p, HERO)
    p.js('()=>{ __demo.P.box=false; }')
    if a.scene:
        p.load_ply(a.scene)
        p.js('()=>{ const P=__demo.P; P.sceneLight=0.22; P.camDist=4.0; P.camElev=0.2; }')
    p.js('()=>{ __demo.reset(42); __demo.step(200); }')
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    enc = subprocess.Popen([ff, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', '60', '-i', '-',
                            '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', a.out],
                           stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for f in range(a.frames):
        # one fixed 1/60 s step per frame: playback speed is true, wall clock is not
        p.js('f=>{ const P=__demo.P; P.yaw=f*0.0022; __demo.step(1); }', f)
        enc.stdin.write(p.grab().tobytes())
    enc.stdin.close(); enc.wait()
    print('wrote', a.out)
    p.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['hash', 'bench', 'deflect', 'deflect_shots', 'light', 'shots', 'video'])
    ap.add_argument('--adapter', default='high', choices=['high', 'low'])
    ap.add_argument('--out', default='out')
    ap.add_argument('--scene', default='')
    ap.add_argument('--demo', default='demo/')
    ap.add_argument('--frames', type=int, default=480)
    ap.add_argument('--seeds', type=int, nargs='+', default=[7, 11, 17, 23, 42, 101, 202, 303])
    args = ap.parse_args()
    globals()['cmd_' + args.cmd](args)
