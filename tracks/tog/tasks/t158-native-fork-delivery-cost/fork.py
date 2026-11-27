"""Device-native prefix sharing with either two surfaces or one guarded surface."""
from dataclasses import replace
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "t154-native-surface-fork"))
import run as t154


def word_ok(words):
    return (words < 0x3c00) & ((words >= 0x0800) | ((words & 1) == 0))


class HalfGuard:
    def __init__(self, gpu):
        self.gpu = gpu
        self.scan = gpu.kernel(str(HERE/"guard.wgsl"), ["utex3d", "buf"])
        self.halve = gpu.kernel(str(HERE/"half_atlas.wgsl"), ["utex3d", "st3d:rgba16float:w"])

    def admit(self):
        # All 65,536 binary16 encodings, followed by only the supported nonnegative safe cells.
        gpu = self.gpu
        words = np.arange(65536, dtype=np.uint16).reshape(1,256,256)
        safe = word_ok(words)
        fixture = np.zeros((*words.shape,4), np.float16)
        fixture[...,0] = np.float16(.75)
        fixture[...,2] = np.float16(1)
        src = gpu.texture3d((256,256,1),"rgba16float","t158-admit-in")
        dst = gpu.texture3d(src.size,src.format,"t158-admit-out")
        bad = gpu.buffer(4,"t158-admit-failures")
        result = {}
        for label, test, expected in (("all", words, int((~safe).sum())),
                                      ("certified", np.where(safe,words,0).astype(np.uint16), 0)):
            fixture[...,1].view(np.uint16)[:] = test
            gpu.upload(src, fixture)
            with gpu.batch() as b:
                b.clear_buffer(bad)
                b.run(self.scan,[src,bad],None,src.size)
                if label == "certified":
                    b.run(self.halve,[src,dst],None,src.size)
            count = int(np.frombuffer(gpu.read_buffer(bad), np.uint32)[0])
            t154.require(count == expected,"Device classification "+label+f" found {count} expected {expected}")
            result[label+"_flagged"] = count
        expected = fixture.copy()
        expected[...,1] = (expected[...,1].astype(np.float32)*np.float32(.5)).astype(np.float16)
        t154.require(np.array_equal(expected.view(np.uint16),gpu.read(dst).view(np.uint16)),
                     "Device half reconstruction differs from certified CPU result")
        for item in (src,dst,bad):
            item.destroy()
        return dict(**result, signed_words=words.size, supported_words=int(safe.sum()))


def copy_buffer(gpu, batch, src, label):
    dst = gpu.buffer(src.size, label)
    batch.copy_buffer(src,dst)
    return dst


def gpu_fork(engine, slow_atlas):
    s, gpu, rad, heat = engine.solver, engine.gpu, engine.radiant, engine.objheat
    t154.require(s._carried().keys() == {"vel","p","scal","scal_fine","burn"} and rad.built and rad.grid
                 and heat.liquid_j is None and heat.matter_j is None, "Unexpected checkpoint layout")
    fields = {}
    with gpu.batch() as batch:
        for name, src in s._carried().items():
            shadow = gpu.texture3d(src.size, src.format, "t158-"+name)
            batch.copy_texture(src,shadow)
            fields[name] = shadow
        radiant = {name: copy_buffer(gpu,batch,getattr(rad,name),"t158-"+name) for name in ("RA","RLC","RL")}
    fields["burn_obj"] = slow_atlas
    return dict(fields=fields,radiant=radiant,temperatures=heat.state(),
                contacts=[t.touch_s.copy() for t in heat.things],embers=engine.embers.save_state(),
                frame=engine.sim_frame, clock=(s.time,s.steps,s.max_speed,s.bbox,s.burning),
                rad_settings=(rad.grid,rad._cleared,rad.built,rad.n_objects))


def rehydrate(engine, scene, packet):
    s, rad, heat = engine.solver, engine.radiant, engine.objheat
    frame = packet["frame"]
    t154.prepare(engine, scene)
    s._prm = scene.solver_params(frame)
    s.set_meshes(scene.mesh_items(frame),scene.data["domain"]["mesh_resolution"])
    s.colliders = []
    s.set_colliders(scene.colliders_gpu(frame))
    with engine.gpu.batch() as b:
        s._init_burn(b,s._prm)
        for name, dst in s._carried().items():
            b.copy_texture(packet["fields"][name],dst)
        b.copy_texture(packet["fields"]["burn"],s.burn[1])
        for dst in s.burn_obj:
            b.copy_texture(packet["fields"]["burn_obj"],dst)
        for name, src in packet["radiant"].items():
            b.copy_buffer(src,getattr(rad,name))
    for resource in [*packet["fields"].values(),*packet["radiant"].values()]:
        resource.destroy()
    s.time,s.steps,s.max_speed,s.bbox,s.burning = packet["clock"]
    rad.grid,rad._cleared,rad.built,rad.n_objects = packet["rad_settings"]
    heat.load_state(packet["temperatures"])
    for item, contacts in zip(heat.things,packet["contacts"],strict=True):
        item.touch_s = contacts.copy()
    engine.embers.load_state(packet["embers"])
    engine.sim_frame = frame


def prefix(engine, scene, method, kernels, phases, details):
    gpu, s = engine.gpu, engine.solver
    atlas = []
    scan_calls = native_slow_calls = expected_steps = 0
    flag = gpu.buffer(4,"t158-history") if method == "S" else None
    init0, react0 = s._init_burn,s._react
    def initialize(b, prm):
        nonlocal scan_calls
        init0(b,prm)
        src = s.burn_obj[0]
        if flag:
            b.clear_buffer(flag)
            b.run(kernels.scan,[src,flag],None,src.size)
            scan_calls += 1
        else:
            for label in ("read","write"):
                x = gpu.texture3d(src.size,src.format,"t158-dual-"+label)
                b.copy_texture(src,x)
                atlas.append(x)

    def react(b, dt, prm, ems, fine=False):
        nonlocal scan_calls,native_slow_calls
        if not fine:
            t154.require(dt == forecast_dt and prm.spread.catch_time == .35 and prm.spread.spotting == 0
                    and not prm.spread.ground and not s.water and not any(e.douse > 0 for e in ems)
                    and s.pieces_step is None, "Unsupported surface interaction")
            if flag:
                src = s.burn_obj[0]
                b.run(kernels.scan,[src,flag],None,src.size)
                scan_calls += 1
            else:
                read,write = atlas
                slow = replace(prm,spread=replace(prm.spread,catch_time=.70))
                b.run(s._k["burn_obj"],s._burn_obj_res(read,write),s._burn_obj_uniforms(dt,slow,[]),read.size)
                atlas.reverse()
                native_slow_calls += 1
        return react0(b,dt,prm,ems,fine=fine)

    with phases("common_prefix"):
        upper = 0.0
        with patch.object(s,"_init_burn",initialize), patch.object(s,"_react",react):
            for frame in range(1,37):
                candidate,n,forecast_dt = t154.forecast(engine,scene,frame,upper)
                if candidate is None:
                    break
                t154.to_frame(engine,scene,frame)
                t154.require(n == engine.last_substeps, "Native CFL prediction changed")
                expected_steps += n
                upper = candidate
    with phases("history_decision_and_fork"):
        t154.require(engine.sim_frame and frame == engine.sim_frame+1 and expected_steps == s.steps, "No defined fork")
        details.update(split=engine.sim_frame, common_steps=expected_steps, guard_dispatches=scan_calls,
                       native_slow_dispatches=native_slow_calls, upper=upper)
        if flag:
            bad = int(np.frombuffer(gpu.read_buffer(flag),np.uint32)[0])
            flag.destroy()
            details["ambiguous_or_invalid_words"] = bad
            t154.require(scan_calls == expected_steps+1, "Missing online boundary test")
            if bad:
                details.update(fallback=True,device_shadow_bytes=0)
                return None
            fast = s.burn_obj[0]
            slow = gpu.texture3d(fast.size,fast.format,"t158-half-slow")
            with gpu.batch() as b:
                b.run(kernels.halve,[fast,slow],None,fast.size)
        else:
            t154.require(native_slow_calls == expected_steps, "Missing native slow update")
            slow, scratch = atlas
            scratch.destroy()
        packet = gpu_fork(engine,slow)
        details.update(fallback=False,device_shadow_bytes=sum(v.nbytes for v in packet["fields"].values())
                       +sum(v.size for v in packet["radiant"].values()), material_temporary_bytes=
                       slow.nbytes*(1 if method=="S" else 2), guard_history_bytes=4 if flag else 0)
        return packet
