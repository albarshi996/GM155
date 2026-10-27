# -*- coding: utf-8 -*-
"""
blender_build.py — يبني مشهد مخازن أبوهادي 155 داخل Blender بخامات واقعية
(زجاج شفّاف، إضاءة باعثة، معادن للرفوف) + شمس وسماء فيزيائية + 16 كاميرا مطابقة للعارض.

التشغيل في Blender:
  1) افتح Blender → تبويب Scripting → Open → اختر هذا الملف → Run Script (Alt+P)
     (أو شغّله بلا واجهة:  blender --background --python blender_build.py --python-expr "render_all()")
  2) يبني المشهد كاملًا ويضيف الكاميرات View01..View16.
  3) للإخراج: نفّذ في وحدة Python:  render_all()
     تُحفظ اللقطات في مجلد ../renders_blender بجوار النموذج.
ملاحظة: إن نقلت الملفات، عدّل JSON_PATH أدناه إلى مسار site_scene.json.
"""
import bpy, bmesh, json, os, math, mathutils

JSON_PATH = r"C:\Users\DELL\Desktop\العمليات اليومية\كوديكس -كلود-البرشي\خطة_Claude_المدير_العام_24-10-2026\مخرجات_Claude\3D\site_scene.json"
if not os.path.exists(JSON_PATH):
    alt = bpy.path.abspath("//site_scene.json")
    if os.path.exists(alt): JSON_PATH = alt

# 16 camera presets (مطابقة للعارض): [name, cam[X,H,Y], tgt[X,H,Y], roof_on]
PRESETS = [
 ("View01_overview",[232,360,-36],[186,0,116],True),
 ("View02_gate",[62,32,-24],[54,6,74],True),
 ("View03_facades",[36,42,-4],[210,6,52],False),
 ("View04_inside_E5",[215,3.0,167.5],[308,1.8,167.5],True),
 ("View05_E5",[236,18,122],[270,4,165],False),
 ("View06_longrow",[250,30,34],[318,5,104],False),
 ("View07_support",[374,56,132],[332,5,180],True),
 ("View08_flow",[190,215,-120],[186,0,108],False),
 ("View09_families",[162,30,34],[222,4,104],False),
 ("View10_inside_E1",[261,3.0,130],[364,1.8,130],True),
 ("View11_asbuilt_proposed",[300,22,28],[316,4,72],False),
 ("View12_hero_E5",[246,46,112],[300,4,167],False),
 ("View13_cold",[106,62,24],[140,2,104],False),
 ("View14_docks",[140,20,30],[140,3,70],False),
 ("View15_ramp",[300,16,30],[314,3,64],True),
 ("View16_admin",[46,18,116],[42,4,158],False),
 ("View17_dockflow",[305,8,119],[256,2.2,150],True),   # E-5 south dock — truck→platform→forklift→door flow
]

def reset_scene():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    for c in list(bpy.data.collections): bpy.data.collections.remove(c)
    for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for b in list(blk):
            if b.users == 0: blk.remove(b)

def coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c)
    return c

def sin(b, names, val):
    for n in names:
        if n in b.inputs:
            try: b.inputs[n].default_value = val; return True
            except Exception: pass
    return False

# ---- richer procedural texture helpers (world-space, consistent real-world scale) ----
def _geo(nt): return nt.nodes.new('ShaderNodeNewGeometry')
def _noisetex(m, scale, detail=6):
    nt=m.node_tree; nz=nt.nodes.new('ShaderNodeTexNoise')
    try: nz.inputs['Scale'].default_value=scale
    except Exception: pass
    try: nz.inputs['Detail'].default_value=detail
    except Exception: pass
    try: nt.links.new(_geo(nt).outputs['Position'], nz.inputs['Vector'])
    except Exception: pass
    return nz
def _wavetex(m, scale, profile='SAW'):
    nt=m.node_tree; wv=nt.nodes.new('ShaderNodeTexWave')
    try: wv.inputs['Scale'].default_value=scale
    except Exception: pass
    try: wv.wave_profile=profile
    except Exception: pass
    try: nt.links.new(_geo(nt).outputs['Position'], wv.inputs['Vector'])
    except Exception: pass
    return wv
def _bump(m, bsdf, tex, strength):
    nt=m.node_tree; bump=nt.nodes.new('ShaderNodeBump')
    try: bump.inputs['Strength'].default_value=strength
    except Exception: pass
    try:
        nt.links.new(tex.outputs['Fac'], bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    except Exception: pass
def _colvar(m, bsdf, base, scale, amt):
    nt=m.node_tree; nz=_noisetex(m, scale, 4)
    rmp=nt.nodes.new('ShaderNodeValToRGB'); r,g,b=base; f=1-amt; f2=1+amt
    try:
        rmp.color_ramp.elements[0].color=(max(0,r*f),max(0,g*f),max(0,b*f),1)
        rmp.color_ramp.elements[1].color=(min(1,r*f2),min(1,g*f2),min(1,b*f2),1)
    except Exception: pass
    try:
        nt.links.new(nz.outputs['Fac'], rmp.inputs['Fac'])
        nt.links.new(rmp.outputs['Color'], bsdf.inputs['Base Color'])
    except Exception: pass
def _roughvar(m, bsdf, lo, hi, scale):
    nt=m.node_tree; nz=_noisetex(m, scale, 4)
    mr=nt.nodes.new('ShaderNodeMapRange')
    try: mr.inputs['To Min'].default_value=lo; mr.inputs['To Max'].default_value=hi
    except Exception: pass
    try:
        nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
        if 'Roughness' in bsdf.inputs: nt.links.new(mr.outputs['Result'], bsdf.inputs['Roughness'])
    except Exception: pass

# ---- Poly Haven CC0 PBR (world-space box projection; for Cycles stills) ----
PH = bool(os.environ.get("PH"))
_PH_TEX = os.path.join(os.path.dirname(JSON_PATH), "hq", "assets", "textures")
_PH_HDR = os.path.join(os.path.dirname(JSON_PATH), "hq", "assets", "hdri")
PH_ROLE = {"floor":"floor","zonefloor":"floor","concrete":"floor","apron":"floor",
           "wall":"wall","building":"wall","office":"wall","cold":"wall",
           "rack_up":"rackmetal","rack_bm":"rackmetal",
           "roof":"roofmetal","roof2":"roofmetal",
           "road":"asphalt","ground":"asphalt","yard":"asphalt"}
PH_TILE = {"floor":3.0,"wall":3.0,"rackmetal":1.6,"roofmetal":2.4,"asphalt":6.0}
def _find_tex(role, mapname):
    for ext in ("jpg","png","exr"):
        p=os.path.join(_PH_TEX, f"{role}_{mapname}.{ext}")
        if os.path.exists(p): return p
    return None
def _find_hdri():
    for ext in ("hdr","exr"):
        p=os.path.join(_PH_HDR, f"hdri.{ext}")
        if os.path.exists(p): return p
    return None
def pbr_ph(m, bsdf, btype):
    """خامة PBR من خرائط Poly Haven، إسقاط صندوقي بإحداثيات عالمية → تبليط بمقياس واقعي بلا UV."""
    role=PH_ROLE[btype]; tile=PH_TILE.get(role,3.0); nt=m.node_tree
    pos=nt.nodes.new('ShaderNodeNewGeometry')
    mp=nt.nodes.new('ShaderNodeMapping')
    try: mp.inputs['Scale'].default_value=(1.0/tile,1.0/tile,1.0/tile)
    except Exception: pass
    nt.links.new(pos.outputs['Position'], mp.inputs['Vector'])
    def img(mapname, noncolor):
        p=_find_tex(role,mapname)
        if not p: return None
        try: im=bpy.data.images.load(p, check_existing=True)
        except Exception: return None
        t=nt.nodes.new('ShaderNodeTexImage'); t.image=im
        try: t.projection='BOX'; t.projection_blend=0.3
        except Exception: pass
        if noncolor:
            try: im.colorspace_settings.name='Non-Color'
            except Exception: pass
        nt.links.new(mp.outputs['Vector'], t.inputs['Vector']); return t
    d=img('Diffuse',False)
    if d: nt.links.new(d.outputs['Color'], bsdf.inputs['Base Color'])
    a=img('arm',True)
    if a:
        sep=nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(a.outputs['Color'], sep.inputs['Color'])
        if role=='floor':                       # إيبوكسي: خشونة منخفضة + طلاء لامع (محاكاة موثّقة)
            mr=nt.nodes.new('ShaderNodeMapRange')
            try: mr.inputs['To Min'].default_value=0.14; mr.inputs['To Max'].default_value=0.40
            except Exception: pass
            nt.links.new(sep.outputs['Green'], mr.inputs['Value'])
            if 'Roughness' in bsdf.inputs: nt.links.new(mr.outputs['Result'], bsdf.inputs['Roughness'])
            sin(bsdf, ["Coat Weight","Clearcoat"], 0.22)
        elif 'Roughness' in bsdf.inputs:
            nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    if role in ('rackmetal','roofmetal'): sin(bsdf, ["Metallic"], 0.7)
    n=img('nor_gl',True)
    if n:
        nm=nt.nodes.new('ShaderNodeNormalMap')
        try: nm.inputs['Strength'].default_value=0.75
        except Exception: pass
        nt.links.new(n.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    return True

_matcache = {}
def mat_for(btype, col):
    key = (btype, tuple(round(c,3) for c in col))
    if key in _matcache: return _matcache[key]
    m = bpy.data.materials.new(f"m_{btype}"); m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    r,g,bl = col
    sin(bsdf, ["Base Color"], (r,g,bl,1.0))
    if PH and btype in PH_ROLE and _find_tex(PH_ROLE[btype], 'Diffuse'):
        pbr_ph(m, bsdf, btype)
    elif btype == "glass":
        sin(bsdf, ["Transmission Weight","Transmission"], 0.9)
        sin(bsdf, ["Roughness"], 0.05); sin(bsdf, ["IOR"], 1.45)
        m.use_screen_refraction = True
    elif btype == "light":
        sin(bsdf, ["Base Color"], (0.1,0.1,0.1,1.0))
        sin(bsdf, ["Emission Color","Emission"], (1.0,0.95,0.82,1.0))
        sin(bsdf, ["Emission Strength"], 42.0)
    elif btype in ("rack_up","rack_bm"):
        sin(bsdf, ["Metallic"], 0.85); sin(bsdf, ["Roughness"], 0.4)
    elif btype == "roof":                                       # blue standing-seam metal
        sin(bsdf, ["Metallic"], 0.5); sin(bsdf, ["Roughness"], 0.42)
        _bump(m, bsdf, _wavetex(m, 2.2, 'SAW'), 0.25)           # seam ribs
        _colvar(m, bsdf, col, 3.0, 0.05)
    elif btype in ("load", "pallet"):                           # shrink-wrapped pallet of cartons
        sin(bsdf, ["Roughness"], 0.62); _colvar(m, bsdf, col, 7.0, 0.13)
        _roughvar(m, bsdf, 0.42, 0.82, 22.0)                    # uneven stretch-wrap sheen
        _bump(m, bsdf, _wavetex(m, 9.0, 'SAW'), 0.09)           # carton stacking seams
        sin(bsdf, ["Specular IOR Level","Specular"], 0.55)      # plastic-wrap highlight
        sin(bsdf, ["Coat Weight","Clearcoat"], 0.28); sin(bsdf, ["Coat Roughness","Clearcoat Roughness"], 0.3)
    elif btype in ("floor", "zonefloor", "concrete", "apron"):  # polished concrete / epoxy (R12) — semi-gloss, reflects racks & lights
        _colvar(m, bsdf, col, 3.5, 0.06); _roughvar(m, bsdf, 0.30, 0.5, 8.0); _bump(m, bsdf, _noisetex(m, 10.0), 0.05)
        sin(bsdf, ["Specular IOR Level","Specular"], 0.6)
    elif btype in ("road", "ground", "yard"):                   # asphalt
        _colvar(m, bsdf, col, 5.0, 0.10); _roughvar(m, bsdf, 0.85, 0.96, 12.0); _bump(m, bsdf, _noisetex(m, 28.0, 8), 0.10)
    elif btype in ("truck","car","gate","cctv","gen","col"):
        sin(bsdf, ["Metallic"], 0.3); sin(bsdf, ["Roughness"], 0.45)
    elif btype == "tree":
        sin(bsdf, ["Roughness"], 0.92); _bump(m, bsdf, _noisetex(m, 14.0, 8), 0.30)
    elif btype in ("wall","building","office","cold","canopy","fence","sand"):  # plaster / cladding / sand
        sin(bsdf, ["Roughness"], 0.85); _colvar(m, bsdf, col, 1.6, 0.04)
    else:
        sin(bsdf, ["Roughness"], 0.85)
    # micro-bevel: round every edge a touch so it catches light (Cycles) — biggest single realism win
    if btype not in ("light",):
        try:
            bev = m.node_tree.nodes.new("ShaderNodeBevel"); bev.samples = 4
            bev.inputs["Radius"].default_value = 0.02
            nin = bsdf.inputs["Normal"]
            if nin.is_linked:                      # a bump already drives Normal → chain bump into the bevel
                m.node_tree.links.new(nin.links[0].from_socket, bev.inputs["Normal"])
            m.node_tree.links.new(bev.outputs["Normal"], nin)
        except Exception: pass
    _matcache[key] = m
    return m

def build():
    reset_scene()
    data = json.load(open(JSON_PATH, encoding="utf-8"))
    boxes = data["boxes"]
    main_c, roof_c, prop_c = coll("Main"), coll("Roofs"), coll("Proposed")
    # shared geometry
    cube = bpy.data.meshes.new("unit_cube"); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(cube); bm.free(); cube.materials.append(None)
    cyl = bpy.data.meshes.new("unit_cyl"); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=28, radius1=0.5, radius2=0.5, depth=1.0); bm.to_mesh(cyl); bm.free(); cyl.materials.append(None)
    sph = bpy.data.meshes.new("unit_sph"); bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5); bm.to_mesh(sph); bm.free(); sph.materials.append(None)
    # horizon ground plane (sandy desert context — distant views no longer sit on a black void)
    gp = bpy.data.objects.new("horizon", cube); gp.location=(190,118,-0.4); gp.scale=(7000,7000,0.2)
    main_c.objects.link(gp)
    gp.material_slots[0].link='OBJECT'; gp.material_slots[0].material=mat_for('sand',(0.62,0.58,0.49))
    n = 0
    for b in boxes:
        bt = b["type"]
        if bt == "label": continue                     # anchors only (2D labels), skip in 3D
        px,py,pz = b["position_m"]; sx,sy,sz = b["dimensions_m"]; col = b["color"]
        me = cyl if bt == "cylinder" else (sph if (bt=="tree" and sx>1.3 and sy>1.3 and abs(sx-sy)<1.5) else cube)
        ob = bpy.data.objects.new(b["id"], me)
        ob["elementId"] = b["id"]      # authoritative join key → glTF node extras (survives name .001 collisions)
        ob.location = (px + sx/2.0, py + sy/2.0, pz + sz/2.0)
        ob.scale = (sx, sy, sz)
        rot = b.get("rotation", 0)
        if rot: ob.rotation_euler = (0.0, 0.0, math.radians(rot))
        tgt = roof_c if bt == "roof" else (prop_c if b.get("state") == "proposed" else main_c)
        tgt.objects.link(ob)
        ob.material_slots[0].link = 'OBJECT'
        ob.material_slots[0].material = mat_for(bt, col)
        n += 1
    # --- sun + physical sky ---
    scn = bpy.context.scene
    w = bpy.data.worlds.new("Sky"); scn.world = w; w.use_nodes = True
    nt = w.node_tree
    for nd in list(nt.nodes): nt.nodes.remove(nd)
    sky = None
    bg = nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    _hdri = _find_hdri() if PH else None
    if _hdri:                                   # إضاءة بيئية واقعية من HDRI (Poly Haven CC0)
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        try: env.image = bpy.data.images.load(_hdri, check_existing=True)
        except Exception: pass
        bg.inputs["Strength"].default_value = 1.0
        nt.links.new(env.outputs[0], bg.inputs[0])
    else:
        sky = nt.nodes.new("ShaderNodeTexSky")
        try: sky.sky_type = 'NISHITA'; sky.sun_elevation = math.radians(52); sky.sun_rotation = math.radians(40)
        except Exception: pass
        bg.inputs["Strength"].default_value = 0.36
        nt.links.new(sky.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    if os.environ.get("VOL"):   # faint atmospheric haze → visible light beams (interior hero shots)
        vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Density"].default_value = 0.0025
        try: vs.inputs["Anisotropy"].default_value = 0.35
        except Exception: pass
        nt.links.new(vs.outputs[0], out.inputs[1])
    sd = bpy.data.lights.new("Sun", 'SUN'); sd.energy = 3.0; sd.color = (1.0, 0.95, 0.86)
    try: sd.angle = math.radians(1.5)
    except Exception: pass
    so = bpy.data.objects.new("Sun", sd); scn.collection.objects.link(so)
    _sea = os.environ.get("SUN_EA")   # geo-accurate sun study: "elevation,azimuth" (az from true north, cw) — Benghazi 32.20°N
    if _sea:
        _E,_A = [float(x) for x in _sea.split(",")]
        Er,Ar = math.radians(_E), math.radians(_A)
        try: sky.sun_elevation = Er; sky.sun_rotation = math.radians((90.0-_A)%360)
        except Exception: pass
        sd.energy = 4.2 if _E>55 else (3.0 if _E>25 else 2.0)
        toSun = mathutils.Vector((math.cos(Er)*math.sin(Ar), math.cos(Er)*math.cos(Ar), math.sin(Er)))
        so.rotation_euler = (-toSun).to_track_quat('-Z','Y').to_euler()   # lamp −Z points along light travel
    else:
        so.rotation_euler = (math.radians(55), 0.0, math.radians(40))
    # --- cameras ---
    cams = []
    for nm, cam, tg, rf in PRESETS:
        cd = bpy.data.cameras.new(nm); cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(50); cd.clip_end = 6000
        co = bpy.data.objects.new(nm, cd); scn.collection.objects.link(co)
        loc = mathutils.Vector((cam[0], cam[2], cam[1])); look = mathutils.Vector((tg[0], tg[2], tg[1]))
        co.location = loc
        co.rotation_euler = (look - loc).to_track_quat('-Z', 'Y').to_euler()
        co["roof_on"] = rf; cams.append(co)
    # interior aisle camera per dry warehouse (walkthrough "من الداخل") — auto from the warehouse list
    for w in (data.get("meta", {}).get("warehouses") or []):
        if w.get("name") == "E-F": continue
        wx, wy, ww, wl = w["x"], w["y"], w["w"], w["l"]; ay = wy + wl/2.0
        nm = "In_" + w["name"]
        cd = bpy.data.cameras.new(nm); cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(56); cd.clip_end = 6000
        co = bpy.data.objects.new(nm, cd); scn.collection.objects.link(co)
        loc = mathutils.Vector((wx + 3.0, ay, 3.0)); look = mathutils.Vector((wx + ww - 4.0, ay, 1.8))
        co.location = loc; co.rotation_euler = (look - loc).to_track_quat('-Z', 'Y').to_euler()
        cd.dof.use_dof = True; cd.dof.focus_distance = 13.0; cd.dof.aperture_fstop = 4.5   # cinematic aisle depth
        co["roof_on"] = True; cams.append(co)    # roof ON → lit by high-bay lights (real warehouse mood, not open sky)
    # interior camera for the cold complex E-F — stand INSIDE a −20°C freezer room (CS-7, 16×20 m),
    # in a forklift aisle between two pallet-rack rows, look north down the frozen pallets to the back
    # wall. Enclosed by 4.5 m racks + walls so little sky shows. Anchored to the real room box.
    cs7 = next((b for b in (data.get("boxes") or []) if b.get("id") == "CS-7_fl"), None)
    if cs7:
        px, py, _pz = cs7["position_m"]; dw, dl, _dh = cs7["dimensions_m"]
        ax = px + 3.2  # centre of the aisle between the 1st and 2nd rack blocks (uprights ~0.9 m wide, 3 m aisle)
        cd = bpy.data.cameras.new("In_E-F"); cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(46); cd.clip_end = 6000
        co = bpy.data.objects.new("In_E-F", cd); scn.collection.objects.link(co)
        loc = mathutils.Vector((ax, py + 1.8, 1.7)); look = mathutils.Vector((ax, py + dl - 4.0, 1.35))
        co.location = loc; co.rotation_euler = (look - loc).to_track_quat('-Z', 'Y').to_euler()
        co["roof_on"] = False; cams.append(co)
    scn.camera = cams[0]
    # --- render settings ---
    scn.render.resolution_x = 1920; scn.render.resolution_y = 1080
    for eng in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE','CYCLES'):
        try: scn.render.engine = eng; break
        except Exception: continue
    try: scn.eevee.use_raytracing = True
    except Exception: pass
    # tone / exposure — المشهد فاتح الخامات فنخفض التعريض لمنع الإبهار
    try: scn.view_settings.view_transform = 'AgX'
    except Exception: pass
    try: scn.view_settings.exposure = -0.7
    except Exception: pass
    try: scn.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass
    # compositor: subtle bloom/glare on bright sources (fixtures, sky) for depth & realism
    try:
        scn.use_nodes = True; ct = scn.node_tree
        for nd in list(ct.nodes): ct.nodes.remove(nd)
        rl = ct.nodes.new("CompositorNodeRLayers"); gl = ct.nodes.new("CompositorNodeGlare")
        gl.glare_type = 'FOG_GLOW'; gl.quality = 'MEDIUM'; gl.threshold = 1.15; gl.size = 6; gl.mix = -0.1
        cp = ct.nodes.new("CompositorNodeComposite")
        ct.links.new(rl.outputs[0], gl.inputs[0]); ct.links.new(gl.outputs[0], cp.inputs[0])
    except Exception: pass
    print(f"[Abuhadi155] built {n} objects · engine={scn.render.engine} · cameras={len(cams)}")
    print("[Abuhadi155] نفّذ render_all() للإخراج (16 لقطة) إلى ../renders_blender")
    return cams

def render_all(outdir=None, only=None):
    if outdir is None:
        outdir = os.environ.get("RENDER_OUT") or os.path.normpath(os.path.join(os.path.dirname(JSON_PATH), "..", "renders_blender"))
    os.makedirs(outdir, exist_ok=True)
    scn = bpy.context.scene
    roofs = bpy.data.collections.get("Roofs")
    cams = sorted([o for o in scn.objects if o.type == 'CAMERA'], key=lambda o: o.name)
    if only:
        cams = [c for c in cams if any(k.lower() in c.name.lower() for k in only)]
    for co in cams:
        if roofs: roofs.hide_render = not bool(co.get("roof_on", True))
        # per-shot exposure: interiors are lamp-lit & enclosed (bright/moody); exteriors are open daylight (darker, no blow-out)
        try: scn.view_settings.exposure = 0.5 if (co.name.startswith("In_") or "inside" in co.name.lower()) else -1.5
        except Exception: pass
        scn.camera = co
        scn.render.filepath = os.path.join(outdir, co.name + ".png")
        bpy.ops.render.render(write_still=True)
        print("rendered", co.name, "->", scn.render.filepath)
    print("[Abuhadi155] تم — اللقطات في:", outdir)

def export_glb(outdir=None, prefix=None, suffix=""):
    """صدّر GLB للويب: ملف «قائم» (Main+Roofs) وملف «مقترح» (Proposed) منفصلين، مع حفظ
    اسم كل عقدة = id وخاصية elementId في extras. prefix يقصر التصدير على مجموعة (مثل E-5)."""
    try: bpy.ops.preferences.addon_enable(module='io_scene_gltf2')
    except Exception: pass
    if outdir is None:
        outdir = os.path.join(os.path.dirname(JSON_PATH), "hq", "models")
    os.makedirs(outdir, exist_ok=True)
    def incoll(o, names): return bool(o.users_collection) and o.users_collection[0].name in names
    def match(o):
        if o.type != 'MESH' or o.name == 'horizon': return False
        if not prefix: return True
        eid = str(o.get('elementId') or o.name)
        return any(eid.startswith(p) for p in prefix.split(","))
    built = [o for o in bpy.data.objects if match(o) and incoll(o, ('Main','Roofs'))]
    prop  = [o for o in bpy.data.objects if match(o) and incoll(o, ('Proposed',))]
    def do_export(objs, fname):
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        if objs: bpy.context.view_layer.objects.active = objs[0]
        fp = os.path.join(outdir, fname)
        bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', use_selection=True,
            export_extras=True, export_apply=False, export_yup=True,
            export_cameras=False, export_lights=False, export_materials='EXPORT')
        sz = os.path.getsize(fp) if os.path.exists(fp) else 0
        print(f"[glb] {fname}: {len(objs)} objects, {sz} bytes -> {fp}")
        return fp, len(objs)
    do_export(built, f"site_built{suffix}.glb")
    do_export(prop,  f"site_proposed{suffix}.glb")
    print(f"[glb] DONE built={len(built)} proposed={len(prop)} prefix={prefix!r}")

if __name__ == "__main__":
    import sys
    build()
    # وسائط بعد "--": "glb [prefix=E-5]" للتصدير، أو أسماء مشاهد/"all" للإخراج (يُجبر Cycles بلا واجهة)
    _argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    _flags0 = [a.lower() for a in _argv]
    if "glb" in _flags0 or "export" in _flags0:
        _pref = next((a.split("=",1)[1] for a in _argv if a.startswith("prefix=")), None)
        _suf0 = next((a.split("=",1)[1] for a in _argv if a.startswith("suffix=")), None)
        _suf  = ("_"+_suf0) if _suf0 else (("_"+(_pref or "").replace("-","").replace(",","").replace(" ","")) if _pref else "")
        export_glb(prefix=_pref, suffix=_suf)
    elif _argv:
        _scn = bpy.context.scene
        _flags = [a.lower() for a in _argv]
        if "cycles" in _flags:                                  # اطلب Cycles صراحةً للجودة القصوى
            try:
                _scn.render.engine = 'CYCLES'; _scn.cycles.samples = 110
                _scn.cycles.use_denoising = True
                _scn.render.use_persistent_data = True           # ابنِ هيكل التسريع مرة واحدة لكل الإطارات
            except Exception: pass
            try:                                                 # فعّل GPU إن توفّر
                prefs = bpy.context.preferences.addons['cycles'].preferences
                prefs.get_devices()
                for ctype in ('OPTIX','CUDA','HIP','ONEAPI','METAL'):
                    try:
                        prefs.compute_device_type = ctype
                        if any(d.type == ctype for d in prefs.devices):
                            for d in prefs.devices: d.use = (d.type in (ctype, 'CPU'))
                            _scn.cycles.device = 'GPU'; break
                    except Exception: pass
            except Exception: pass
        # غير ذلك يبقى EEVEE Next (محرّك البناء الافتراضي)
        _names = [a for a in _argv if a.lower() not in ("cycles", "all", "eevee")]
        render_all(only=(_names or None))
    # داخل واجهة Blender: شغّل السكربت ثم نفّذ render_all() في وحدة Python
