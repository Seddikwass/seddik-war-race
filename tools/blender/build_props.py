# SEDDIK WAR RACE — décors modélisés dans Blender (mode sans interface)
# Usage : blender -b -P tools/blender/build_props.py -- <dossier_glb> <dossier_rendus> [hdri.hdr]
# Les matériaux nommés Concrete / RustyMetal reçoivent les textures photo Poly Haven dans le jeu (UV projetées à l'échelle du monde).
import bpy, bmesh, math, os, sys
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
OUT_GLB, OUT_PNG = args[0], args[1]
HDRI = args[2] if len(args) > 2 and os.path.exists(args[2]) else None
os.makedirs(OUT_GLB, exist_ok=True); os.makedirs(OUT_PNG, exist_ok=True)

def setin(node, keys, val):
    for k in keys:
        if k in node.inputs:
            node.inputs[k].default_value = val; return True
    return False

MATS = {}
def mat(name, color, metal=0.0, rough=0.6, emit=None, alpha=1.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes.get('Principled BSDF')
    setin(b, ['Base Color'], (*color, 1)); setin(b, ['Metallic'], metal); setin(b, ['Roughness'], rough)
    if emit: setin(b, ['Emission Color', 'Emission'], (*emit, 1)); setin(b, ['Emission Strength'], 3.0)
    if alpha < 1:
        setin(b, ['Alpha'], alpha)
        if hasattr(m, 'surface_render_method'): m.surface_render_method = 'BLENDED'
    m.diffuse_color = (*color, alpha); MATS[name] = m; return m

def M():
    return dict(
        conc=mat('Concrete', (0.62, 0.6, 0.57), 0, 0.85),
        rust=mat('RustyMetal', (0.42, 0.3, 0.22), 0.6, 0.6),
        steel=mat('PaintedSteel', (0.16, 0.17, 0.18), 0.6, 0.45),
        yellow=mat('SafetyYellow', (0.85, 0.62, 0.08), 0.3, 0.5),
        red=mat('SafetyRed', (0.6, 0.1, 0.06), 0.3, 0.5),
        white=mat('TankPaint', (0.82, 0.82, 0.8), 0.3, 0.45),
        cont=mat('ContainerPaint', (0.9, 0.9, 0.9), 0.4, 0.55),
        win=mat('Window', (0.05, 0.07, 0.08), 0.8, 0.1),
        lit=mat('WindowLit', (1, 0.85, 0.55), 0, 0.3, emit=(1, 0.8, 0.5)),
        lamp=mat('Lamp', (1, 0.97, 0.9), 0, 0.2, emit=(1, 0.95, 0.85)),
        dark=mat('Dark', (0.04, 0.04, 0.045), 0.3, 0.6),
    )

def box(size, loc, material, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.active_object; ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); ob.data.materials.append(material)
    if bevel:
        m = ob.modifiers.new('Bev', 'BEVEL'); m.width = bevel; m.segments = 2
    return ob

def cyl(r, depth, loc, material, axis='Z', verts=24, r2=None):
    rot = {'X': (0, math.pi / 2, 0), 'Y': (math.pi / 2, 0, 0), 'Z': (0, 0, 0)}[axis]
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot)
    ob = bpy.context.active_object; ob.data.materials.append(material); bpy.ops.object.shade_smooth(); return ob

def tube(p1, p2, r, material, verts=8):
    p1, p2 = Vector(p1), Vector(p2); d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(p1 + p2) / 2)
    ob = bpy.context.active_object; ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized()); ob.data.materials.append(material)
    return ob

def finish(objs, name, uv=2.0):
    """Applique les modificateurs, projette des UV à l'échelle du monde, fusionne en un objet."""
    for o in objs:
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        for m in list(o.modifiers):
            try: bpy.ops.object.modifier_apply(modifier=m.name)
            except Exception as e: print('mod', e)
        try:
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.cube_project(cube_size=uv); bpy.ops.object.mode_set(mode='OBJECT')
        except Exception as e:
            print('uv', e)
            try: bpy.ops.object.mode_set(mode='OBJECT')
            except Exception: pass
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join()
    ob = bpy.context.active_object; ob.name = name
    bpy.context.scene.cursor.location = (0, 0, 0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return ob

# ---------- décors ----------
def watchtower(m):
    o = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            o.append(tube((sx * 2.2, sy * 2.2, 0), (sx * 1.7, sy * 1.7, 13.5), 0.18, m['steel']))
    for z0 in (2, 6, 10):
        for (a, b) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            o.append(tube((a[0] * 2.05, a[1] * 2.05, z0), (b[0] * 1.85, b[1] * 1.85, z0 + 3.5), 0.07, m['steel']))
    o.append(box((6.2, 6.2, 0.4), (0, 0, 13.7), m['conc'], 0.05))
    o.append(box((5, 5, 0.9), (0, 0, 14.35), m['conc'], 0.03))
    o.append(box((5.06, 5.06, 1.1), (0, 0, 15.35), m['win']))
    for sx in (-1, 1):
        for k in range(-2, 3):
            o.append(box((0.12, 0.12, 1.1), (sx * 2.5, k * 1.1, 15.35), m['steel']))
            o.append(box((0.12, 0.12, 1.1), (k * 1.1, sx * 2.5, 15.35), m['steel']))
    o.append(box((5, 5, 0.6), (0, 0, 16.2), m['conc'], 0.03))
    o.append(box((6.8, 6.8, 0.25), (0, 0, 16.65), m['steel'], 0.03))
    for k in range(12):
        a = k / 12 * 2 * math.pi; o.append(tube((math.cos(a) * 3.0, math.sin(a) * 3.0, 13.9), (math.cos(a) * 3.0, math.sin(a) * 3.0, 14.9), 0.04, m['yellow'], 6))
    o.append(cyl(0.45, 0.8, (2.4, 2.4, 17.2), m['steel'], 'Y', 16)); o.append(cyl(0.38, 0.05, (2.4, 1.98, 17.2), m['lamp'], 'Y', 16))
    for sx in (-0.3, 0.3): o.append(tube((sx + 2.6, -2.6, 0), (sx + 2.0, -2.0, 13.6), 0.04, m['steel'], 6))
    for z in range(1, 27): o.append(tube((2.3 - z * 0.023, -2.6 + z * 0.023, z * 0.5), (2.9 - z * 0.023, -2.6 + z * 0.023, z * 0.5), 0.025, m['steel'], 6))
    return finish(o, 'watchtower')

def prison_block(m, W=30, D=14, H=12, floors=3, name='prison_block'):
    o = [box((W, D, H), (0, 0, H / 2), m['conc'], 0.05)]
    o.append(box((W + 0.6, D + 0.6, 0.8), (0, 0, H + 0.4), m['conc'], 0.05))
    fh = H / floors
    for f in range(floors):
        z = fh * f + fh * 0.6
        for i in range(int(W / 3)):
            x = -W / 2 + 1.5 + i * 3
            for sy in (-1, 1):
                lit = (i * 7 + f * 3) % 5 == 0
                o.append(box((1.4, 0.2, 1.2), (x, sy * (D / 2 + 0.02), z), m['lit'] if lit else m['win']))
                for b in (-0.45, -0.15, 0.15, 0.45): o.append(box((0.06, 0.12, 1.25), (x + b, sy * (D / 2 + 0.12), z), m['steel']))
                o.append(box((1.7, 0.35, 0.15), (x, sy * (D / 2 + 0.15), z - 0.7), m['conc']))
    for k in range(3):
        o.append(box((2.2, 1.6, 1.4), (-W / 2 + 5 + k * 8, 2, H + 1.5), m['steel'], 0.05))
        o.append(cyl(0.6, 0.15, (-W / 2 + 5 + k * 8, 2, H + 2.25), m['dark'], 'Z', 16))
    o.append(cyl(2.2, 3.5, (W / 2 - 4, -2, H + 2.6), m['rust'], 'Z', 20))
    for z in (2, H - 1): o.append(tube((-W / 2, -D / 2 - 0.4, z), (W / 2, -D / 2 - 0.4, z), 0.18, m['rust']))
    o.append(box((3, 0.4, 3.2), (0, D / 2 + 0.1, 1.6), m['steel'], 0.04))
    o.append(box((3.6, 1.2, 0.2), (0, D / 2 + 0.6, 3.4), m['conc']))
    o.append(box((W * 0.6, 0.06, 0.9), (0, -D / 2 - 0.05, H - 0.7), m['yellow']))
    return finish(o, name, 2.5)

def container(m):
    L, Wd, H = 12.2, 2.44, 2.6
    o = [box((L, Wd, H), (0, 0, H / 2), m['cont'], 0.03)]
    for i in range(int(L / 0.36)):
        x = -L / 2 + 0.3 + i * 0.36
        for sy in (-1, 1): o.append(box((0.12, 0.05, H - 0.3), (x, sy * (Wd / 2 + 0.02), H / 2), m['cont']))
    for z in (0.08, H - 0.08):
        for sy in (-1, 1): o.append(box((L, 0.12, 0.16), (0, sy * (Wd / 2 + 0.03), z), m['cont']))
    for b in (-0.7, -0.25, 0.25, 0.7): o.append(box((0.05, 0.06, H - 0.4), (L / 2 + 0.03, b, H / 2), m['cont']))
    return finish(o, 'container', 3.0)

def fuel_tank(m, R=8, H=12):
    o = [cyl(R, H, (0, 0, H / 2), m['white'], 'Z', 48)]
    o.append(cyl(R * 1.01, 0.3, (0, 0, H), m['steel'], 'Z', 48, R * 0.6))
    for z in (H * 0.25, H * 0.5, H * 0.75): o.append(cyl(R * 1.008, 0.12, (0, 0, z), m['steel'], 'Z', 48))
    o.append(cyl(R * 1.005, 1.2, (0, 0, H * 0.82), m['red'], 'Z', 48))
    steps = 40
    for s in range(steps):
        a = s / steps * math.pi * 1.6; z = s / steps * H
        x, y = math.cos(a) * (R + 0.6), math.sin(a) * (R + 0.6)
        o.append(box((0.9, 0.35, 0.08), (x, y, z + 0.3), m['rust'], rot=(0, 0, a + math.pi / 2)))
        if s % 4 == 0: o.append(tube((x * 1.06, y * 1.06, z), (x * 1.06, y * 1.06, z + 1.4), 0.03, m['yellow'], 6))
    for k in range(24):
        a = k / 24 * 2 * math.pi; o.append(tube((math.cos(a) * R * 0.97, math.sin(a) * R * 0.97, H), (math.cos(a) * R * 0.97, math.sin(a) * R * 0.97, H + 1.1), 0.03, m['yellow'], 6))
    o.append(tube((R + 0.2, 0, 0.8), (R + 6, 0, 0.8), 0.35, m['rust'], 14))
    o.append(cyl(0.6, 1.2, (R + 6, 0, 0.6), m['rust'], 'Z', 14))
    return finish(o, 'fuel_tank', 3.0)

def crane(m):
    o = []
    for sx in (-6, 6):
        for sy in (-5, 5):
            o.append(box((1.0, 1.0, 30), (sx, sy, 15), m['yellow'], 0.05))
        for z in range(3, 29, 6):
            o.append(tube((sx, -5, z), (sx, 5, z + 5), 0.12, m['yellow'])); o.append(box((0.5, 10, 0.5), (sx, 0, z), m['yellow']))
    for sy in (-5, 5): o.append(box((13, 0.8, 0.8), (0, sy, 2.5), m['yellow'], 0.04))
    o.append(box((70, 3, 2.4), (20, 0, 31.2), m['yellow'], 0.06))
    for x in range(-14, 55, 4): o.append(tube((x, -1.4, 30), (x + 4, 1.4, 32.4), 0.08, m['steel'], 6))
    o.append(box((4, 4, 3), (10, 0, 28.5), m['steel'], 0.05)); o.append(box((3.6, 0.1, 1.6), (10, -2.02, 28.8), m['win']))
    o.append(box((3, 3.2, 1.2), (30, 0, 29.2), m['steel'], 0.04))
    for dx in (-0.6, 0.6): o.append(tube((30 + dx, 0, 28.6), (30 + dx, 0, 16), 0.04, m['dark'], 6))
    o.append(box((3, 2.5, 0.6), (30, 0, 15.7), m['red'], 0.04))
    for sx in (-6, 6):
        for sy in (-5, 5): o.append(box((1.6, 1.2, 0.9), (sx, sy, 0.45), m['red'], 0.04))
    return finish(o, 'crane', 3.0)

def setup_render():
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    for vt in ('AgX', 'Filmic'):
        try: sc.view_settings.view_transform = vt; break
        except Exception: pass
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes.get('Background')
    if HDRI:
        env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(HDRI); nt.links.new(env.outputs['Color'], bg.inputs['Color'])

def render(name, ob, dist):
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0)); fl = bpy.context.active_object; fl.data.materials.append(mat('Floor', (0.2, 0.19, 0.18), 0, 0.8))
    cd = bpy.data.cameras.new('Cam'); cd.lens = 35; cam = bpy.data.objects.new('Cam', cd); bpy.context.scene.collection.objects.link(cam)
    h = max(ob.dimensions.z, 2)
    cam.location = (dist * 0.8, -dist, h * 0.7 + 2); d = Vector((0, 0, h * 0.4)) - cam.location; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 3; sl = bpy.data.objects.new('Sun', sd); bpy.context.scene.collection.objects.link(sl); sl.rotation_euler = (0.9, 0.2, 0.8)
    bpy.context.scene.render.filepath = os.path.join(OUT_PNG, 'prop_' + name + '.png'); bpy.ops.render.render(write_still=True)
    for o in (fl, cam, sl): bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
setup_render()
PROPS = [('watchtower', watchtower, 26), ('prison_block', prison_block, 45), ('barracks', lambda m: prison_block(m, 16, 10, 7, 2, 'barracks'), 30),
         ('container', container, 18), ('fuel_tank', fuel_tank, 30), ('crane', crane, 80)]
for name, fn, dist in PROPS:
    for o in list(bpy.context.scene.objects): bpy.data.objects.remove(o, do_unlink=True)
    m = M(); ob = fn(m)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_GLB, name + '.glb'), export_format='GLB', use_selection=True, export_apply=True)
    print(f'DECOR {name}: {len(ob.data.polygons)} faces, {round(ob.dimensions.x,1)}x{round(ob.dimensions.y,1)}x{round(ob.dimensions.z,1)} m')
    render(name, ob, dist)
print('TERMINE DECORS')
