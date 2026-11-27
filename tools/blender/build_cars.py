# SEDDIK WAR RACE — génération des véhicules dans Blender (mode sans interface)
# Usage : blender -b -P tools/blender/build_cars.py -- <dossier_glb> <dossier_rendus> [hdri.hdr]
# Repère : avant de la voiture vers -Y, largeur sur X, hauteur sur Z (export glTF : avant = +Z, haut = +Y).
import bpy, bmesh, math, json, os, sys
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
OUT_GLB, OUT_PNG = args[0], args[1]
HDRI = args[2] if len(args) > 2 and os.path.exists(args[2]) else None
os.makedirs(OUT_GLB, exist_ok=True); os.makedirs(OUT_PNG, exist_ok=True)
CARS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cars.json')))

# ---------- matériaux ----------
def setin(node, keys, val):
    for k in keys:
        if k in node.inputs:
            node.inputs[k].default_value = val
            return True
    return False

MATS = {}
def mat(name, color, metal=0.0, rough=0.5, emit=None, coat=0.0, alpha=1.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    setin(b, ['Base Color'], (*color, 1)); setin(b, ['Metallic'], metal); setin(b, ['Roughness'], rough)
    if coat:
        setin(b, ['Coat Weight', 'Clearcoat'], coat); setin(b, ['Coat Roughness', 'Clearcoat Roughness'], 0.04)
    if emit:
        setin(b, ['Emission Color', 'Emission'], (*emit, 1)); setin(b, ['Emission Strength'], 4.0)
    if alpha < 1:
        setin(b, ['Alpha'], alpha)
        if hasattr(m, 'surface_render_method'): m.surface_render_method = 'BLENDED'
        if hasattr(m, 'blend_method'):
            try: m.blend_method = 'BLEND'
            except Exception: pass
    m.diffuse_color = (*color, alpha)
    MATS[name] = m
    return m

def all_mats():
    return dict(
        paint=mat('Paint', (0.85, 0.85, 0.85), 0.3, 0.32, coat=1.0),
        glass=mat('Glass', (0.02, 0.04, 0.05), 0.2, 0.03, alpha=0.6),
        chrome=mat('Chrome', (0.8, 0.82, 0.85), 1.0, 0.18),
        steel=mat('Steel', (0.45, 0.47, 0.5), 0.9, 0.35),
        dark=mat('Dark', (0.03, 0.03, 0.035), 0.3, 0.55),
        rubber=mat('Rubber', (0.02, 0.02, 0.02), 0.0, 0.88),
        head=mat('HeadLight', (1, 0.97, 0.88), 0.0, 0.1, emit=(1, 0.95, 0.8)),
        tail=mat('TailLight', (0.4, 0.0, 0.0), 0.0, 0.2, emit=(1, 0.08, 0.03)),
        glow=mat('Glow', (0.4, 0.8, 0.9), 0.0, 0.3, emit=(0.4, 0.85, 1.0)),
        red=mat('Caliper', (0.7, 0.08, 0.05), 0.3, 0.4),
        helmet=mat('Helmet', (0.95, 0.75, 0.15), 0.3, 0.3, coat=1.0),
    )

# ---------- outils de modélisation ----------
def link(ob):
    bpy.context.scene.collection.objects.link(ob); return ob

def mesh_obj(name, verts, faces, material):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new(name, me)); ob.data.materials.append(material)
    for p in me.polygons: p.use_smooth = True
    return ob

def loft(name, stations, material, K=24, n=4.0, subsurf=2):
    """stations : (y, demi_largeur, z_bas, z_haut). Section super-ellipse, lissée par subdivision."""
    verts, faces = [], []
    for (y, hw, zb, zt) in stations:
        zc, hz = (zb + zt) / 2, (zt - zb) / 2
        for k in range(K):
            a = 2 * math.pi * k / K; c, s = math.cos(a), math.sin(a)
            verts.append((hw * math.copysign(abs(c) ** (2 / n), c), y, zc + hz * math.copysign(abs(s) ** (2 / n), s)))
    S = len(stations)
    for i in range(S - 1):
        for k in range(K):
            faces.append((i * K + k, i * K + (k + 1) % K, (i + 1) * K + (k + 1) % K, (i + 1) * K + k))
    faces.append(tuple(range(K))[::-1]); faces.append(tuple(range((S - 1) * K, S * K)))
    ob = mesh_obj(name, verts, faces, material)
    if subsurf:
        m = ob.modifiers.new('Sub', 'SUBSURF'); m.levels = subsurf; m.render_levels = subsurf
    return ob

def box(name, size, loc, material, bevel=0.03, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.active_object; ob.name = name; ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(material)
    if bevel:
        m = ob.modifiers.new('Bev', 'BEVEL'); m.width = bevel; m.segments = 2
    return ob

def cyl(name, r, depth, loc, material, axis='X', verts=24, bevel=0.0):
    rot = {'X': (0, math.pi / 2, 0), 'Y': (math.pi / 2, 0, 0), 'Z': (0, 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    ob = bpy.context.active_object; ob.name = name; ob.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    if bevel:
        m = ob.modifiers.new('Bev', 'BEVEL'); m.width = bevel; m.segments = 3; m.limit_method = 'ANGLE'
    return ob

def tube(name, p1, p2, r, material):
    p1, p2 = Vector(p1), Vector(p2); d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=r, depth=d.length, location=(p1 + p2) / 2)
    ob = bpy.context.active_object; ob.name = name
    ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    ob.data.materials.append(material); bpy.ops.object.shade_smooth()
    return ob

def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    for o in objs:
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers):
            try: bpy.ops.object.modifier_apply(modifier=m.name)
            except Exception: pass
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join(); ob = bpy.context.active_object; ob.name = name
    return ob

# ---------- une voiture ----------
def build(type_, p, M):
    L, W, r = p['L'], p['W'], p['r']; h = L / 2; C = p['cab']
    Y = lambda z: -z  # coordonnée du jeu (avant = +z) vers Blender (avant = -y)
    bot, nose, hood, belt, deck, tail = p['bot'], p['nose'], p['hood'], p['belt'], p['deck'], p['tail']
    hw = W / 2
    st = [
        (Y(h), hw - 0.28, bot + 0.1, nose),
        (Y(h - 0.12), hw - 0.1, bot, nose + 0.12),
        (Y(h - 0.45), hw, bot, hood * 0.97),
        (Y(p['wf']), hw, bot, hood + (belt - hood) * 0.35),
        (Y(C['f'] + 0.1), hw, bot, belt),
        (Y((C['f'] + C['r']) / 2), hw, bot, belt + 0.01),
        (Y(C['r']), hw, bot, belt - 0.01),
        (Y(p['wr']), hw, bot, (belt + deck) / 2),
        (Y(-h + 0.4), hw - 0.03, bot, deck),
        (Y(-h + 0.1), hw - 0.12, bot + 0.05, (deck + tail) / 2),
        (Y(-h), hw - 0.26, bot + 0.12, tail),
    ]
    body = loft('Body', st, M['paint'], K=28, n=4.5)
    # passages de roues (booléen après lissage)
    for wz in (p['wf'], p['wr']):
        cut = cyl('Cut', r + 0.11, W + 1, (0, Y(wz), r), M['dark'], 'X', 40)
        bo = body.modifiers.new('Arch', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = cut
        cut.hide_render = True; cut.hide_viewport = True
    # élargisseurs d'ailes (masquent la découpe des passages de roues)
    flares = []
    for wz in (p['wf'], p['wr']):
        for sd in (-1, 1):
            bpy.ops.mesh.primitive_torus_add(major_radius=r + 0.13, minor_radius=0.075, major_segments=32, minor_segments=8,
                                             location=(sd * (hw - 0.02), Y(wz), r), rotation=(0, math.pi / 2, 0))
            t = bpy.context.active_object; t.name = 'Flare'; t.scale = (1, 1, 1.6)
            bm = bmesh.new(); bm.from_mesh(t.data)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x > 0.01], context='VERTS')  # garder la moitié haute (x local -> -z monde)
            bm.to_mesh(t.data); bm.free(); t.data.materials.append(M['dark']); bpy.ops.object.shade_smooth()
            flares.append(t)
    # habitacle vitré et toit
    cw = C['w'] / 2; zt = C['top']
    gst = [(Y(C['f']), cw - 0.04, belt - 0.06, belt + 0.02), (Y(C['f'] - C['ws'] * 0.5), cw - 0.06, belt - 0.06, (belt + zt) / 2 + 0.02),
           (Y(C['f'] - C['ws']), cw - 0.1, belt - 0.06, zt), (Y(C['r'] + C['rs']), cw - 0.1, belt - 0.06, zt),
           (Y(C['r'] + C['rs'] * 0.4), cw - 0.06, belt - 0.06, (belt + zt) / 2 + 0.05), (Y(C['r']), cw - 0.04, belt - 0.06, belt + 0.02)]
    glass = loft('Glass', gst, M['glass'], K=24, n=5, subsurf=1)
    rf, rr = C['f'] - C['ws'], C['r'] + C['rs']
    roof = loft('Roof', [(Y(rf + 0.06), cw - 0.12, zt - 0.06, zt + 0.02), (Y(rf), cw - 0.07, zt - 0.08, zt + 0.05), (Y(rr), cw - 0.07, zt - 0.08, zt + 0.05), (Y(rr - 0.06), cw - 0.12, zt - 0.06, zt + 0.02)], M['paint'], K=20, n=6, subsurf=1)
    parts_paint = [body, roof]
    for sd in (-1, 1):
        parts_paint.append(box('Mirror', (0.1, 0.16, 0.09), (sd * (hw + 0.02), Y(C['f'] - 0.1), belt - 0.01), M['paint'], 0.02))
    if p.get('scoop'): parts_paint.append(box('Scoop', (0.7, 1.0, 0.18), (0, Y(p['wf'] - 0.3), hood + 0.1), M['paint'], 0.05))
    if p.get('fins'):
        for sd in (-1, 1): parts_paint.append(box('Fin', (0.08, 1.1, 0.5), (sd * 0.42, Y(-h + 0.7), deck + 0.2), M['paint'], 0.02))
    steel, dark, head, tail_, glow = [], [], [], [], []
    # bélier avant, pare-chocs, protections latérales boulonnées
    steel.append(box('Ram', (W + 0.25, 0.24, 0.3), (0, Y(h + 0.12), bot + 0.2), M['steel'], 0.04))
    for i in range(-2, 3): steel.append(tube('Spike', (i * 0.4, Y(h + 0.2), bot + 0.12), (i * 0.4, Y(h + 0.32), bot + 0.62), 0.045, M['chrome']))
    steel.append(box('RearBar', (W + 0.1, 0.22, 0.26), (0, Y(-h - 0.08), bot + 0.2), M['steel'], 0.04))
    for sd in (-1, 1):
        steel.append(box('Plate', (0.06, L * 0.42, 0.26), (sd * (hw + 0.06), Y((p['wf'] + p['wr']) / 2), bot + 0.24), M['steel'], 0.015))
        for k in range(-2, 3): dark.append(cyl('Bolt', 0.035, 0.05, (sd * (hw + 0.1), Y((p['wf'] + p['wr']) / 2 + k * 0.4), bot + 0.24), M['dark'], 'X', 8))
    # arceau tubulaire
    for sd in (-1, 1):
        x = sd * (cw + 0.03)
        steel.append(tube('Cage', (x, Y(rf), zt + 0.12), (x, Y(rr), zt + 0.12), 0.04, M['steel']))
        steel.append(tube('Cage', (x, Y(rf), zt + 0.12), (x, Y(C['f']), belt + 0.05), 0.04, M['steel']))
    steel.append(tube('Cage', (-cw, Y(rf), zt + 0.12), (cw, Y(rf), zt + 0.12), 0.04, M['steel']))
    # optiques et échappements
    for sd in (-1, 1):
        head.append(box('Head', (0.36, 0.06, 0.12), (sd * (hw - 0.4), Y(h - 0.01), nose + 0.04), M['head'], 0.02))
        tail_.append(box('Tail', (0.42, 0.06, 0.1), (sd * (hw - 0.38), Y(-h + 0.01), tail - 0.03), M['tail'], 0.02))
        dark.append(cyl('Exhaust', 0.075, 0.36, (sd * 0.55, Y(-h - 0.12), bot + 0.08), M['chrome'], 'Y', 14))
    dark.append(box('Grille', (W * 0.6, 0.05, 0.16), (0, Y(h + 0.02), nose - 0.08), M['dark'], 0.02))
    if p.get('spoiler') == 'lip': dark.append(box('Lip', (W - 0.1, 0.36, 0.05), (0, Y(-h + 0.25), deck + 0.07), M['dark'], 0.015))
    if p.get('spoiler') in ('wing', 'big'):
        ww = W + 0.2 if p['spoiler'] == 'big' else W - 0.05; hy = deck + (0.55 if p['spoiler'] == 'big' else 0.38)
        dark.append(box('Wing', (ww, 0.5, 0.05), (0, Y(-h + 0.28), hy), M['dark'], 0.02))
        for sd in (-1, 1):
            dark.append(box('Strut', (0.05, 0.18, hy - deck), (sd * 0.65, Y(-h + 0.3), (hy + deck) / 2), M['dark'], 0.01))
            dark.append(box('End', (0.04, 0.6, 0.3), (sd * ww / 2, Y(-h + 0.28), hy + 0.05), M['dark'], 0.01))
    if p.get('armor'):
        for sd in (-1, 1):
            steel.append(box('Shield', (0.05, (C['f'] - C['r']) * 0.55, zt - belt - 0.14), (sd * (cw + 0.04), Y((C['f'] + C['r']) / 2 - 0.1), (belt + zt) / 2), M['steel'], 0.01))
        steel.append(box('Plow', (W + 0.35, 0.12, 0.55), (0, Y(h + 0.38), bot + 0.35), M['steel'], 0.03, rot=(0.45, 0, 0)))
    if p.get('rally'):
        for i in range(4): head.append(cyl('Spot', 0.1, 0.08, ((i - 1.5) * 0.32, Y(rf + 0.1), zt + 0.3), M['head'], 'Y', 16))
        dark.append(box('Bar', (1.4, 0.2, 0.08), (0, Y(rf + 0.05), zt + 0.2), M['dark'], 0.01))
        dark.append(cyl('Spare', 0.42, 0.24, (0, Y(-h - 0.15), deck + 0.05), M['rubber'], 'Y', 28, 0.05))
    if p.get('turbine'): dark.append(cyl('Turbine', 0.35, 0.85, (0, Y((rf + rr) / 2), zt + 0.33), M['dark'], 'Y', 24, 0.03))
    if p.get('glow'):
        for sd in (-1, 1): glow.append(box('Glow', (0.04, L * 0.75, 0.05), (sd * (hw + 0.13), 0, bot + 0.42), M['glow'], 0))
    # pilote
    dark.append(box('Seat', (0.42, 0.5, 0.5), (0.36, Y((C['f'] + C['r']) / 2 - 0.15), belt), M['dark'], 0.05))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.19, location=(0.36, Y((C['f'] + C['r']) / 2 - 0.05), belt + 0.32), segments=20, ring_count=12)
    helm = bpy.context.active_object; helm.name = 'Helmet'; helm.data.materials.append(M['helmet']); bpy.ops.object.shade_smooth()
    # assemblage par matériau (peu d'appels de dessin dans le jeu)
    dark += flares
    objs = [join(parts_paint, 'Paint_Body'), glass, join(steel, 'Steel_Parts'), join(dark, 'Dark_Parts'), join(head, 'HeadLights'), join(tail_, 'TailLights'), helm]
    if glow: objs.append(join(glow, 'GlowStrips'))
    # roues : pneu arrondi, jante à branches, disque ; origine au centre de la roue
    for tag, sx, wz in (('FL', 1, p['wf']), ('FR', -1, p['wf']), ('RL', 1, p['wr']), ('RR', -1, p['wr'])):
        cx, cy = sx * (hw - 0.12), Y(wz)
        tire = cyl('Tire', r, 0.34, (cx, cy, r), M['rubber'], 'X', 32, 0.07)
        rim = cyl('Rim', r * 0.6, 0.3, (cx, cy, r), M['chrome'] if type_ not in ('proto', 'phoenix') else M['dark'], 'X', 24)
        spokes = [rim]
        for k in range(6):
            a = k / 6 * 2 * math.pi
            spokes.append(box('Spoke', (0.3, 0.07, r * 0.5), (cx, cy + math.sin(a) * r * 0.3, r + math.cos(a) * r * 0.3), M['chrome'] if type_ not in ('proto', 'phoenix') else M['dark'], 0, rot=(a, 0, 0)))
        disc = cyl('Disc', r * 0.45, 0.04, (cx - sx * 0.08, cy, r), M['steel'], 'X', 24)
        wheel = join([tire] + spokes + [disc], 'Wheel_' + tag)
        bpy.ops.object.select_all(action='DESELECT'); wheel.select_set(True); bpy.context.view_layer.objects.active = wheel
        bpy.context.scene.cursor.location = (cx, cy, r); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        objs.append(wheel)
        objs.append(box('Caliper_' + tag, (0.1, 0.16, 0.22), (cx - sx * 0.14, cy + 0.06, r + r * 0.3), M['red'], 0.02))
    # appliquer les modificateurs restants
    for o in objs:
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers):
            try: bpy.ops.object.modifier_apply(modifier=m.name)
            except Exception as e: print('modifier', o.name, m.name, e)
    for o in list(bpy.context.scene.objects):
        if o.name.startswith('Cut'): bpy.data.objects.remove(o, do_unlink=True)
    return objs

def clear():
    for o in list(bpy.context.scene.objects): bpy.data.objects.remove(o, do_unlink=True)

def setup_render():
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.device = 'CPU'
    try: sc.cycles.use_denoising = True
    except Exception: pass
    sc.render.resolution_x, sc.render.resolution_y = 960, 540; sc.render.film_transparent = False
    for vt in ('AgX', 'Filmic'):
        try:
            sc.view_settings.view_transform = vt; break
        except Exception: pass
    world = bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True; nt = world.node_tree
    bg = nt.nodes.get('Background')
    if HDRI:
        env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(HDRI); nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    else:
        bg.inputs['Color'].default_value = (0.5, 0.45, 0.4, 1)
    bg.inputs['Strength'].default_value = 1.0

def render(type_, objs):
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0)); fl = bpy.context.active_object; fl.name = 'Floor'
    fl.data.materials.append(mat('Floor', (0.18, 0.18, 0.19), 0.0, 0.6))
    cam_data = bpy.data.cameras.new('Cam'); cam_data.lens = 50; cam = link(bpy.data.objects.new('Cam', cam_data))
    cam.location = (5.2, -6.0, 2.3); d = Vector((0, 0, 0.75)) - cam.location; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = 3.0; sl = link(bpy.data.objects.new('Sun', sun)); sl.rotation_euler = (0.9, 0.2, 0.8)
    bpy.context.scene.render.filepath = os.path.join(OUT_PNG, type_ + '.png'); bpy.ops.render.render(write_still=True)
    for n in ('Floor', 'Cam', 'Sun'):
        o = bpy.data.objects.get(n)
        if o: bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
setup_render()
for type_, p in CARS.items():
    clear(); M = all_mats()
    objs = build(type_, p, M)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_GLB, type_ + '.glb'), export_format='GLB', use_selection=True, export_apply=True)
    tris = sum(len(o.data.polygons) for o in objs if o.type == 'MESH')
    print(f'VOITURE {type_}: {len(objs)} objets, {tris} faces')
    render(type_, objs)
print('TERMINE')
