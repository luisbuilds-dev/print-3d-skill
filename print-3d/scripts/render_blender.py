"""Se ejecuta DENTRO de Blender:  blender -b -P render_blender.py -- salida_dir color_hex pieza1.stl [pieza2.stl ...]
Hace 4 renders bonitos (portada 3/4, frente, planta, trasera) de las piezas juntas, fondo de estudio oscuro."""
import sys, math, bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
out, color, stls = args[0], args[1], args[2:]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

objs = []
for s in stls:
    bpy.ops.wm.stl_import(filepath=s)
    objs += list(bpy.context.selected_objects)

# separar varias piezas en X y centrar todo
x = 0.0
for o in objs:
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    w = max(v.x for v in bb) - min(v.x for v in bb)
    o.location.x += x - min(v.x for v in bb)
    x += w + 10
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
centro = (mn + mx) / 2
for o in objs:
    o.location -= Vector((centro.x, centro.y, mn.z))
tam = max((mx - mn).x, (mx - mn).y, (mx - mn).z)

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)) + (1,)

mat = bpy.data.materials.new("pla")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = hex_rgb(color)
bsdf.inputs["Roughness"].default_value = 0.45
for o in objs:
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = False

# suelo infinito (curva de estudio) oscuro
bpy.ops.mesh.primitive_plane_add(size=tam * 40, location=(0, 0, 0))
suelo = bpy.context.object
ms = bpy.data.materials.new("suelo")
ms.use_nodes = True
ms.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = hex_rgb("#1a1a1a")
ms.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
suelo.data.materials.append(ms)

w = bpy.data.worlds.new("w")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = hex_rgb("#0b0b0b")
w.node_tree.nodes["Background"].inputs[1].default_value = 0.4

def luz(nombre, loc, energia, tamano):
    d = bpy.data.lights.new(nombre, "AREA")
    d.energy, d.size = energia, tamano
    l = bpy.data.objects.new(nombre, d)
    sc.collection.objects.link(l)
    l.location = loc
    l.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

k = tam / 100
luz("key", (-1.2 * tam, -1.0 * tam, 1.4 * tam), 9e4 * k * k, tam)
luz("fill", (1.4 * tam, -0.6 * tam, 0.7 * tam), 2.5e4 * k * k, tam)
luz("rim", (0.3 * tam, 1.5 * tam, 1.0 * tam), 5e4 * k * k, tam * 0.6)

cam_d = bpy.data.cameras.new("cam")
cam_d.lens = 70
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam

sc.render.engine = "CYCLES"
sc.cycles.samples = 96
sc.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
    sc.cycles.device = "GPU"
except Exception:
    pass
sc.render.resolution_x, sc.render.resolution_y = 1600, 1200
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Punchy"
except Exception:
    pass
sc.view_settings.exposure = 0.9
sc.render.film_transparent = False

alto = (mx - mn).z
objetivo = Vector((0, 0, alto * 0.4))
vistas = {"1_portada": (-35, 30), "2_frente": (0, 12), "3_planta": (0, 85), "4_trasera": (150, 35)}
for nombre, (azim, elev) in vistas.items():
    d = tam * 2.1
    a, e = math.radians(azim - 90), math.radians(elev)
    cam.location = objetivo + Vector((d * math.cos(e) * math.cos(a), d * math.cos(e) * math.sin(a), d * math.sin(e)))
    cam.rotation_euler = (objetivo - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{out}/{nombre}.png"
    bpy.ops.render.render(write_still=True)
    print("RENDER", sc.render.filepath)
