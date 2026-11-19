# 0028 v3 "Black ink fired into milk" - rebuilt in real 3D (owner, Nov 19 2026: "continue the milk + black reel", picked
# "anew in 3D"). Core look (confirmed): a bright white milk world; black ink "bullets" blast into it and, in slow motion,
# bloom into real 3D mushrooms, vortex rings and curling fingers; the shots keep coming until the black takes over the
# white ("like a whole glass of ink"); black and white only, calm pace, soft creamy sound; one last drop, fade.
# Simulation: Blender Mantaflow gas (heavy ink: negative density buoyancy, vorticity confinement), baked once and saved
# as a .blend; Cycles renders the baked volumes: black absorption for the ink inside a faint white scattering "milk"
# haze (far ink reads lighter = depth), a soft backlit white world, one key light for form.
# Usage:
#   blender -b --factory-startup -P ink_milk.py -- <outdir> bake <seconds> <fps>          (env IM_RES, IM_NOISE)
#   blender -b <outdir>/scene.blend -P ink_milk.py -- <outdir> render <t0> <t1> <k> <n>  (env IM_RES_PX, IM_SAMPLES)
import json
import math
import os
import sys
import time

import bpy

a_ = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(a_[0]); MODE = a_[1]
os.makedirs(OUT, exist_ok=True)
BLEND = os.path.join(OUT, "scene.blend")
PRE = 1.8          # seconds of simulation before the video starts (frame 0 is already mid-blast)

# shots: (real time s, x, y, z, dir (dx,dz), speed, radius, emit seconds). Beat sheet (30 s):
#  0      HOOK: a big black bullet already tearing down through the centre (fired during the pre-roll)
#  1.2-8  pairs left/right, mushrooms roll and curl
#  8.5-14 bigger shots, faster, from three directions; the plumes start to merge
#  15-19  CLIMAX: a volley across the width, then one giant blast in the centre - the black takes over
#  19-26  everything slows; black clouds billow and fill the milk, white only in the gaps
#  26.3   one last small drop falls into the calm; 28.4-29.9 fade to black
SHOTS = [
    (-1.6, 0.00, 0.0, 2.05, (0.0, -1.0), 4.2, 0.13, 0.18),
    (1.2, -0.42, 0.05, 1.90, (0.12, -1.0), 2.8, 0.063, 0.16),
    (2.1, 0.45, -0.05, 1.90, (-0.1, -1.0), 2.8, 0.063, 0.16),
    (3.4, -0.10, 0.1, 1.90, (0.05, -1.0), 3.2, 0.070, 0.16),
    (4.6, 1.04, 0.0, 1.30, (-0.6, -0.8), 2.6, 0.056, 0.16),
    (5.4, -1.10, -0.1, 1.30, (0.6, -0.8), 2.6, 0.056, 0.16),
    (6.8, 0.20, 0.05, 1.90, (-0.05, -1.0), 3.4, 0.077, 0.16),
    (8.5, -0.35, 0.0, 1.90, (0.1, -1.0), 3.4, 0.084, 0.16),
    (9.3, 0.38, 0.1, 1.90, (-0.1, -1.0), 3.4, 0.084, 0.16),
    (10.4, 0.00, -0.1, 1.90, (0.0, -1.0), 3.8, 0.091, 0.16),
    (11.5, 1.20, 0.0, 0.90, (-0.9, -0.4), 3.0, 0.070, 0.16),
    (12.2, -1.20, 0.05, 0.90, (0.9, -0.4), 3.0, 0.070, 0.16),
    (13.4, -0.20, 0.0, 1.90, (0.05, -1.0), 3.6, 0.091, 0.16),
    (14.6, -0.55, 0.0, 1.90, (0.05, -1.0), 3.6, 0.084, 0.22),
    (14.86, -0.20, 0.1, 1.90, (0.0, -1.0), 3.6, 0.084, 0.22),
    (15.12, 0.20, -0.1, 1.90, (0.0, -1.0), 3.6, 0.084, 0.22),
    (15.39, 0.55, 0.0, 1.90, (-0.05, -1.0), 3.6, 0.084, 0.22),
    (16.4, 0.00, 0.0, 1.92, (0.0, -1.0), 4.4, 0.20, 0.45),
    (17.75, -0.6, 0.1, 1.95, (0.05, -1.0), 2.0, 0.17, 0.7),      # slow heavy pours: the black billows and fills the milk
    (18.8, 0.6, -0.1, 1.95, (-0.05, -1.0), 2.0, 0.17, 0.7),
    (19.85, 0.0, 0.0, 1.95, (0.0, -1.0), 2.2, 0.22, 0.9),
    (23.08, 0.12, 0.0, 1.90, (0.0, -1.0), 1.8, 0.035, 0.12),
]


def build_and_bake(secs, fps):
    res = int(os.environ.get("IM_RES", "160")); use_noise = os.environ.get("IM_NOISE", "0") == "1"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    nf = int(round((secs + PRE) * fps))
    sc.frame_start, sc.frame_end = 1, nf; sc.render.fps = fps
    # the milk tank (portrait)
    bpy.ops.mesh.primitive_cube_add(size=1); dom = bpy.context.active_object; dom.name = "Domain"
    dom.scale = (3.0, 0.8, 4.4); bpy.ops.object.transform_apply(scale=True)
    m = dom.modifiers.new("F", "FLUID"); m.fluid_type = "DOMAIN"; d = m.domain_settings
    d.domain_type = "GAS"; d.resolution_max = res
    d.alpha = -1.0; d.beta = 0.0; d.vorticity = 0.05; d.time_scale = 0.42      # ink, not smoke: low vorticity, no noise      # heavy ink, curly, slow motion
    d.use_dissolve_smoke = False
    # adaptive domain: the solver only works in the box around the ink -> a much finer grid at a bearable bake time
    d.use_adaptive_domain = True; d.adapt_margin = 6; d.adapt_threshold = 0.002
    for _k, _v in (("openvdb_data_depth", "16"), ("openvdb_cache_compress_type", "BLOSC")):
        try:
            setattr(d, _k, _v)
        except Exception as e:  # noqa: BLE001
            print("VDB OPT", _k, e)
    d.cache_type = "ALL"; d.cache_directory = os.path.join(OUT, "cache"); d.cache_frame_start = 1; d.cache_frame_end = nf
    if use_noise:
        d.use_noise = True; d.noise_scale = 2; d.noise_strength = float(os.environ.get("IM_NOISE_STR", "0.35"))
    # the shots: each is a small sphere that emits black ink with a strong initial velocity for a moment
    for i, (ts, x, y, z, (dx, dz), spd, r, emit) in enumerate(SHOTS):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x, y, z)); b = bpy.context.active_object; b.name = "Shot%02d" % i
        f = b.modifiers.new("F", "FLUID"); f.fluid_type = "FLOW"; s = f.flow_settings
        s.flow_type = "SMOKE"; s.flow_behavior = "INFLOW"; s.smoke_color = (0, 0, 0); s.density = 1.0
        n_ = math.hypot(dx, dz); s.use_initial_velocity = True; s.velocity_coord = (spd * dx / n_, 0.0, spd * dz / n_)
        s.subframes = 3
        f0 = max(1, int(round((ts + PRE) * fps))); f1 = f0 + max(2, int(round(emit * fps)))
        s.use_inflow = False; s.keyframe_insert("use_inflow", frame=1)
        if f0 > 1:
            s.keyframe_insert("use_inflow", frame=f0 - 1)
        s.use_inflow = True; s.keyframe_insert("use_inflow", frame=f0); s.keyframe_insert("use_inflow", frame=f1)
        s.use_inflow = False; s.keyframe_insert("use_inflow", frame=f1 + 1)     # (boolean keys step: on/off, no blend)
        b.hide_render = True
    build_look(sc, dom)
    bpy.ops.object.select_all(action="DESELECT"); dom.select_set(True); bpy.context.view_layer.objects.active = dom
    bpy.context.view_layer.update(); sc.frame_set(1); bpy.context.view_layer.update()
    if os.environ.get("IM_ATTACH"):
        # attach to a cache another process is still baking (frames 1..IM_ATTACH_UPTO already written): render while it bakes
        d.cache_directory = os.environ["IM_ATTACH"]; d.cache_resumable = True
        try:
            d.cache_frame_pause_data = int(os.environ.get("IM_ATTACH_UPTO", "0"))
        except Exception as e:  # noqa: BLE001
            print("PAUSE ERR", e)
        print("ATTACH baked:", d.has_cache_baked_data, "pause:", d.cache_frame_pause_data)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
        return
    if os.environ.get("IM_RESUME_FROM"):
        # continue an interrupted bake from the last written frame (run it on a COPY of the cache first)
        d.cache_resumable = True; d.cache_frame_pause_data = int(os.environ["IM_RESUME_FROM"])
        print("RESUME from", d.cache_frame_pause_data)
    t0 = time.time()
    with bpy.context.temp_override(object=dom, active_object=dom, selected_objects=[dom]):
        r = bpy.ops.fluid.bake_all()
    print("BAKE", r, "%.0fs" % (time.time() - t0), "frames", nf, "res", res, "noise", use_noise, "baked", d.has_cache_baked_data)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    json.dump({"pre": PRE, "fps": fps, "secs": secs, "shots": [{"t": s_[0], "x": s_[1], "r": s_[6], "spd": s_[5]} for s_ in SHOTS]},
              open(os.path.join(OUT, "events.json"), "w"))


def build_look(sc, dom):
    sc.render.engine = "CYCLES"; sc.cycles.device = "GPU"
    sc.view_settings.view_transform = "Standard"
    sc.cycles.volume_bounces = 2; sc.cycles.max_bounces = 6
    # world: bright, slightly warm milk-white, a little brighter at the top (light comes through the milk from above)
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; wn, wl = w.node_tree.nodes, w.node_tree.links
    bg = wn["Background"]; tc = wn.new("ShaderNodeTexCoord"); sx = wn.new("ShaderNodeSeparateXYZ"); rp = wn.new("ShaderNodeValToRGB")
    wl.new(tc.outputs["Generated"], sx.inputs[0]); wl.new(sx.outputs["Z"], rp.inputs["Fac"])
    rp.color_ramp.elements[0].position = 0.3; rp.color_ramp.elements[0].color = (0.82, 0.81, 0.79, 1)
    rp.color_ramp.elements[1].position = 0.8; rp.color_ramp.elements[1].color = (1.0, 0.99, 0.97, 1)
    # a faint, soft milky texture (+-4%) so the white is never a flat border (Instagram) and reads as liquid
    nz = wn.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 26.0; nz.inputs["Detail"].default_value = 8
    wl.new(tc.outputs["Generated"], nz.inputs["Vector"])
    mr = wn.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 0.955; mr.inputs["To Max"].default_value = 1.02
    wl.new(nz.outputs["Fac"], mr.inputs["Value"])
    mx = wn.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
    wl.new(rp.outputs["Color"], mx.inputs["A"]); wl.new(mr.outputs["Result"], mx.inputs["B"])
    wl.new(mx.outputs["Result"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0
    # the ink: black absorption by density + a faint white milky scatter everywhere in the tank (depth haze)
    mat = bpy.data.materials.new("InkMilk"); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "density"
    mu = nt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu.inputs[1].default_value = float(os.environ.get("IM_INK", "260"))
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption"); ab.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1)
    scv = nt.nodes.new("ShaderNodeVolumeScatter"); scv.inputs["Color"].default_value = (0.97, 0.96, 0.94, 1)
    scv.inputs["Density"].default_value = 0.12
    inks = nt.nodes.new("ShaderNodeVolumeScatter"); inks.inputs["Color"].default_value = (0.05, 0.05, 0.05, 1)
    mu2 = nt.nodes.new("ShaderNodeMath"); mu2.operation = "MULTIPLY"; mu2.inputs[1].default_value = 0.08
    add1 = nt.nodes.new("ShaderNodeAddShader"); add2 = nt.nodes.new("ShaderNodeAddShader")
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.5   # crisper ink edges
    nt.links.new(at.outputs["Fac"], pw.inputs[0]); nt.links.new(pw.outputs[0], mu.inputs[0]); nt.links.new(mu.outputs[0], ab.inputs["Density"])
    mat.cycles.volume_step_rate = 0.5
    nt.links.new(mu.outputs[0], mu2.inputs[0]); nt.links.new(mu2.outputs[0], inks.inputs["Density"])
    inks.inputs["Color"].default_value = (0.04, 0.04, 0.04, 1); mu2.inputs[1].default_value = 0.04   # black ink: it absorbs, thin edges go grey
    nt.links.new(ab.outputs[0], add2.inputs[0]); nt.links.new(inks.outputs[0], add2.inputs[1])
    nt.links.new(add2.outputs[0], out.inputs["Volume"]); dom.data.materials.append(mat)
    # (no extra milk haze volume: lit by the key it veiled the ink grey; the bright white world reads as milk)
    # a soft key from the upper left gives the ink clouds form (lit edges)
    kl = bpy.data.lights.new("Key", "AREA"); kl.energy = 1400; kl.size = 3.0
    ko = bpy.data.objects.new("Key", kl); ko.location = (-3.0, -3.0, 3.5); sc.collection.objects.link(ko)
    ko.rotation_euler = (0.9, 0, -0.75)
    cd = bpy.data.cameras.new("C"); cd.lens = 32; cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
    cd.dof.use_dof = False
    cam.location = (0.0, -3.1, 0.15); cam.rotation_euler = (math.radians(88), 0, 0)


def render(t0, t1, k, n):
    sc = bpy.context.scene
    p = bpy.context.preferences.addons["cycles"].preferences; p.compute_device_type = "OPTIX"; p.get_devices()
    for dv in p.devices:
        dv.use = True
    w_, h_ = [int(v) for v in os.environ.get("IM_RES_PX", "540x960").split("x")]
    sc.render.resolution_x, sc.render.resolution_y = w_, h_
    sc.cycles.samples = min(int(os.environ.get("IM_SAMPLES", "48")), int(os.environ.get("IM_SAMPLES_CAP", "20"))); sc.cycles.use_denoising = True
    for m_ in bpy.data.materials:                     # speed: Blender's default volume step (the scene used a 2x finer one)
        m_.cycles.volume_step_rate = float(os.environ.get("IM_STEP", "1.0"))
    fps = sc.render.fps
    cam = sc.camera
    frames = list(range(int(round(t0 * fps)), int(round(t1 * fps))))
    for vf in frames[k::n]:
        t = vf / fps
        # the camera breathes very slowly closer, then eases back as the black takes over (no spin)
        def _sm(a, b):
            q = max(0.0, min(1.0, (t - a) / (b - a))); return q * q * (3 - 2 * q)
        # close on the first blast, slowly following the ink down, then easing back as the black takes over the milk
        cam.location = (0.06 * math.sin(t * 0.21), -2.35 - 0.95 * _sm(12, 21), 0.8 - 0.75 * _sm(0, 12) + 0.04 * math.sin(t * 0.3))
        sc.frame_set(vf + int(round(PRE * fps)) + 1)
        sc.render.filepath = os.path.join(OUT, "f_%04d.png" % vf)
        bpy.ops.render.render(write_still=True)
    print("RENDERED")


def vdb_render(cache, t0, t1, k, n, secs, fps):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.render.fps = fps
    bpy.ops.mesh.primitive_cube_add(size=1); tmp = bpy.context.active_object
    build_look(sc, tmp)
    mat = tmp.data.materials[0]
    for nd in mat.node_tree.nodes:
        if nd.type == "ATTRIBUTE" and nd.attribute_name == "density":
            nd.attribute_name = "density_noise"
    bpy.data.objects.remove(tmp)
    vol = bpy.data.volumes.new("Ink"); vob = bpy.data.objects.new("Ink", vol); sc.collection.objects.link(vob)
    vob.location = (-1.5, -0.4, -2.2)                 # VDB grids are stored from the tank's min corner
    vol.materials.append(mat)
    mat.cycles.volume_step_rate = 1.0                 # (speed: default step for the parallel render)
    p = bpy.context.preferences.addons["cycles"].preferences; p.compute_device_type = "OPTIX"; p.get_devices()
    for dv in p.devices:
        dv.use = True
    w_, h_ = [int(v) for v in os.environ.get("IM_RES_PX", "1080x1920").split("x")]
    sc.render.resolution_x, sc.render.resolution_y = w_, h_
    sc.cycles.samples = int(os.environ.get("IM_SAMPLES", "40")); sc.cycles.use_denoising = True
    cam = sc.camera
    nf = int(round((secs + PRE) * fps))
    frames = list(range(int(round(t0 * fps)), int(round(t1 * fps))))
    for vf in frames[k::n]:
        t = vf / fps
        sim = vf + int(round(PRE * fps)) + 1
        f_this = os.path.join(cache, "noise", "fluid_noise_%04d.vdb" % sim)
        f_next = os.path.join(cache, "noise", "fluid_noise_%04d.vdb" % min(sim + 1, nf))
        while not (os.path.exists(f_next) and (sim < nf or os.path.exists(os.path.join(os.path.dirname(cache), "scene.blend")))):
            time.sleep(5)                              # wait until the bake has moved past this frame
        time.sleep(1)
        vol.filepath = f_this; vol.grids.load()

        def _sm(a, b):
            q = max(0.0, min(1.0, (t - a) / (b - a))); return q * q * (3 - 2 * q)
        cam.location = (0.06 * math.sin(t * 0.21), -2.35 - 0.95 * _sm(12, 21), 0.8 - 0.75 * _sm(0, 12) + 0.04 * math.sin(t * 0.3))
        sc.frame_set(1)
        sc.render.filepath = os.path.join(OUT, "f_%04d.png" % vf)
        bpy.ops.render.render(write_still=True)
    print("RENDERED")


if MODE == "vdbrender":
    vdb_render(os.path.abspath(a_[2]), float(a_[3]), float(a_[4]), int(a_[5]), int(a_[6]), float(a_[7]), int(a_[8]))
elif MODE == "bake":
    build_and_bake(float(a_[2]), int(a_[3]))
else:
    render(float(a_[2]), float(a_[3]), int(a_[4]), int(a_[5]))
