# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d==0.13.*", "trimesh", "rtree", "matplotlib", "numpy", "fast-simplification", "mapbox-earcut", "shapely", "networkx", "lxml"]
# ///
"""cad.py — builds, validates and previews parts for the printer in the user profile. Exports STL (+ 3MF/STEP if the profile asks).

  uv run cad.py build modelo.py [--detalle x,y,z,r] [--sin-vista] [--material PLA]
  uv run cad.py check pieza.stl [--detalle x,y,z,r] [--sin-vista] [--material PLA]
  uv run cad.py medir pieza.stl x=94 z=3 ...      (secciones exactas: contorno, huecos, área)

El modelo (.py) hace `from lib3d import *` y define:
  resultado = Part                       -> <NOMBRE>.stl
  resultado = {"nombre": Part, ...}      -> un STL por pieza (SALIDA="separadas", por defecto)
                                            o todas juntas en <NOMBRE>.stl (SALIDA="placa") o ambas ("ambas")
  NOMBRE    = "mi_pieza"                 (opcional; por defecto el nombre del .py)
  ENSAMBLE  = {"a": Part, "b": Part}     (opcional; piezas en posición montada -> comprueba choques y holguras)
  DETALLE   = (x, y, z, r)               (opcional; zona a ampliar en la vista, en coordenadas de impresión)

Salida: los STL junto al .py; la vista PNG en %TEMP%/impresion-3d/; un informe corto por consola.
Código de salida 0 = ok, 1 = error de modelo, 2 = el STL tiene problemas graves.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import runpy
import sys
import tempfile
import time
import traceback
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import printer_profile  # noqa: E402
PERFIL = printer_profile.load()
REG = PERFIL["reglas"]
VISTAS = Path(tempfile.gettempdir()) / "impresion-3d"


def log(msg: str) -> None:
    print(msg, flush=True)


# ------------------------------------------------------------------------- análisis de malla
def analizar(mesh, nombre: str, material: str) -> tuple[dict, list[str], bool]:
    import numpy as np
    avisos: list[str] = []
    grave = False
    bb_min, bb_max = mesh.bounds
    size = bb_max - bb_min
    info = {"pieza": nombre, "medidas_mm": [round(float(v), 2) for v in size],
            "caras": int(len(mesh.faces))}

    # 1. malla cerrada y un solo cuerpo
    if not mesh.is_watertight:
        avisos.append("GRAVE: la malla no es cerrada (watertight) -> el laminador puede fallar")
        grave = True
    if not mesh.is_winding_consistent:
        avisos.append("GRAVE: normales incoherentes")
        grave = True
    cuerpos = mesh.body_count
    info["cuerpos"] = int(cuerpos)

    # 2. cabe en la cama
    mg = 2 * PERFIL["margen_cama_mm"]
    cama = np.array(PERFIL["cama_mm"], float) - [mg, mg, 0]
    if np.any(size > cama + 1e-6):
        rot = sorted(size[:2]) <= sorted(cama[:2]) and size[2] <= cama[2]
        avisos.append(f"GRAVE: no cabe en la cama {PERFIL['cama_mm']}" + (" (cabe girándola en Z)" if rot else ""))
        grave = grave or not rot
    if abs(bb_min[2]) > 0.01:
        avisos.append(f"la pieza no apoya en z=0 (z min = {bb_min[2]:.2f}); usa apoyar()")

    # 3. volumen y filamento
    vol = float(mesh.volume) / 1000.0  # cm3
    area = float(mesh.area) / 100.0     # cm2
    dens = PERFIL["densidad_g_cm3"].get(material, 1.24)
    concha = min(vol, area * 0.12)       # ~1.2 mm de paredes/techos
    g15 = (concha + max(vol - concha, 0) * 0.15) * dens
    info["volumen_cm3"] = round(vol, 2)
    info["filamento_g"] = {"aprox_15%_relleno": round(g15, 1), "macizo": round(vol * dens, 1)}

    n = mesh.face_normals
    tri_z = mesh.triangles[:, :, 2]
    fa = mesh.area_faces

    # 4. apoyo en la cama
    en_cama = (n[:, 2] < -0.99) & (tri_z.max(axis=1) < bb_min[2] + 0.05)
    contacto = float(fa[en_cama].sum())
    info["contacto_cama_mm2"] = round(contacto, 1)
    base_min = max(min(size[0], size[1]), 1e-6)
    if contacto < 30:
        avisos.append(f"poco apoyo en la cama ({contacto:.0f} mm²): añade borde (brim) o cambia la orientación")
    elif size[2] / base_min > 5 and size[2] > 30:
        avisos.append(f"pieza alta y estrecha (alto/base = {size[2] / base_min:.1f}): usa brim de 5 mm")

    # 5. voladizos (caras que miran hacia abajo más de lo permitido, fuera de la cama)
    lim = -math.sin(math.radians(REG["voladizo_max_grados"])) - 0.02
    colg = (n[:, 2] < lim) & ~en_cama
    info["voladizo_mm2"] = round(float(fa[colg].sum()), 1)
    zonas = []
    if colg.any():
        import trimesh
        idx = np.nonzero(colg)[0]
        sub_adj = mesh.face_adjacency[np.all(colg[mesh.face_adjacency], axis=1)]
        comps = trimesh.graph.connected_components(sub_adj, nodes=idx, min_len=1)
        for comp in comps:
            comp = np.asarray(comp)
            a = float(fa[comp].sum())
            if a < 2.0:
                continue
            pts = mesh.triangles[comp].reshape(-1, 3)
            lo, hi = pts.min(axis=0), pts.max(axis=0)
            horiz = bool(np.all(n[comp, 2] < -0.97))
            alto = float(lo[2] - bb_min[2])
            zonas.append({"area_mm2": round(a, 1), "z_mm": round(alto, 2),
                          "x": [round(float(lo[0]), 1), round(float(hi[0]), 1)],
                          "y": [round(float(lo[1]), 1), round(float(hi[1]), 1)],
                          "tipo": "techo plano" if horiz else "pendiente > 45°"})
        zonas.sort(key=lambda z: -z["area_mm2"])
        info["zonas_colgantes"] = zonas[:4]
        if zonas:
            avisos.append(f"{len(zonas)} zona(s) colgante(s) ({info['voladizo_mm2']} mm²): revisa si son puentes "
                          f"(apoyados a ambos lados, <= {REG['puente_max_mm']} mm) o necesitan soporte/rediseño")

    # 6. grosor de pared (rayos hacia dentro desde puntos de la superficie)
    try:
        import trimesh
        cnt = 3000 if len(mesh.faces) < 200_000 else 1500
        pts, fidx = trimesh.sample.sample_surface_even(mesh, cnt, seed=1)
        dirs = -n[fidx]
        locs, ray_i, _ = mesh.ray.intersects_location(pts + dirs * 1e-3, dirs, multiple_hits=False)
        if len(ray_i):
            d = np.full(len(pts), np.inf)
            d[ray_i] = np.linalg.norm(locs - pts[ray_i], axis=1)
            d = d[np.isfinite(d) & (d > 0.02)]
            if len(d):
                finos = d < REG["pared_min_mm"] - 0.02
                info["pared_mm"] = {"min": round(float(d.min()), 2), "p5": round(float(np.percentile(d, 5)), 2),
                                    "pct_bajo_minimo": round(100 * float(finos.mean()), 1)}
                if finos.mean() > 0.01:
                    avisos.append(f"paredes finas: {100 * finos.mean():.1f}% de la superficie con < "
                                  f"{REG['pared_min_mm']} mm (mín {d.min():.2f} mm) -> no saldrán o serán frágiles")
    except Exception as e:  # el análisis de pared nunca debe tumbar la exportación
        info["pared_mm"] = f"no medido ({type(e).__name__})"
    return info, avisos, grave


# ------------------------------------------------------------------------------- vista PNG
def vista(meshes: dict, ruta: Path, detalle=None) -> None:
    """Una sola imagen 2×3: iso, frente, lateral, planta, desde abajo y detalle (o iso trasera).
    Proyección propia con ocultación por profundidad: rápida y con ejes en mm reales."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.collections import PolyCollection

    lim = -math.sin(math.radians(REG["voladizo_max_grados"])) - 0.02
    paleta = [np.array(c) for c in ([0.35, 0.55, 0.85], [0.95, 0.65, 0.2], [0.45, 0.75, 0.45], [0.7, 0.5, 0.85])]
    luz = np.array([0.35, -0.55, 0.75]); luz /= np.linalg.norm(luz)

    def reducir(m):
        if len(m.faces) > 30_000:
            try:
                return m.simplify_quadric_decimation(face_count=30_000)
            except Exception:
                pass
        return m

    def recortar(m, c):
        cx, cy, cz, r = c
        out = m
        for eje in range(3):
            for s in (1, -1):
                nrm = np.zeros(3); nrm[eje] = s
                org = np.array([cx, cy, cz], float); org[eje] -= s * r
                try:
                    out = out.slice_plane(org, nrm, cap=True)
                except Exception:
                    out = out.slice_plane(org, nrm, cap=False)
                if out is None or len(out.faces) == 0:
                    return None
        return out

    def camara(elev, azim):
        el, az = math.radians(elev), math.radians(azim)
        d = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
        if abs(d[2]) > 0.999:
            u = np.array([1.0, 0.0, 0.0])
        else:
            u = np.cross([0, 0, 1], d); u /= np.linalg.norm(u)
        return d, u, np.cross(d, u)

    def pintar(ax, grupo, elev, azim, ejes, titulo):
        d, u, v = camara(elev, azim)
        polys, cols, prof = [], [], []
        for i, m in enumerate(grupo):
            if m is None:
                continue
            nn = m.face_normals
            vis = nn @ d > 1e-6
            tri = m.triangles[vis]
            n2 = nn[vis]
            sh = 0.35 + 0.65 * np.clip(n2 @ luz, 0, 1)
            c = np.outer(sh, paleta[i % len(paleta)])
            en_cama = tri[:, :, 2].max(axis=1) < zcama + 0.05
            c[(n2[:, 2] < lim) & ~en_cama] = [0.9, 0.15, 0.15]
            polys.append(np.stack([tri @ u, tri @ v], axis=-1))
            cols.append(c)
            prof.append(tri.mean(axis=1) @ d)
        ax.set_title(titulo, fontsize=9)
        if not polys:
            ax.set_axis_off(); return
        P = np.concatenate(polys); C = np.concatenate(cols); Z = np.concatenate(prof)
        o = np.argsort(Z)
        ax.add_collection(PolyCollection(P[o], facecolors=np.clip(C[o], 0, 1), edgecolors=np.clip(C[o], 0, 1),
                                         linewidths=0.15))
        lo, hi = P.reshape(-1, 2).min(0), P.reshape(-1, 2).max(0)
        pad = max((hi - lo).max() * 0.03, 0.5)
        ax.set_xlim(lo[0] - pad, hi[0] + pad); ax.set_ylim(lo[1] - pad, hi[1] + pad)
        ax.set_aspect("equal")
        if ejes:
            ax.tick_params(labelsize=6, length=2, pad=1)
            ax.set_xlabel(ejes[0], fontsize=7, labelpad=0); ax.set_ylabel(ejes[1], fontsize=7, labelpad=0)
            ax.grid(alpha=0.25, linewidth=0.5)
        else:
            ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)

    zcama = min(float(m.bounds[0][2]) for m in meshes.values())
    todos = [reducir(m) for m in meshes.values()]
    # piezas separadas que se pisan en XY: solo para la imagen, ponlas en fila a lo largo de X
    bxs = [m.bounds for m in todos]
    pisan = any(not (a[1][0] < b[0][0] or b[1][0] < a[0][0] or a[1][1] < b[0][1] or b[1][1] < a[0][1])
                for i, a in enumerate(bxs) for b in bxs[i + 1:])
    if pisan and not detalle:
        x = 0.0
        fila = []
        for m in todos:
            q = m.copy()
            q.apply_translation([x - q.bounds[0][0], 0, 0])
            x = q.bounds[1][0] + 10
            fila.append(q)
        todos = fila
    paneles = [("Isométrica", 30, -60, None, todos),
               ("Frente (XZ)", 0, -90, ("X", "Z"), todos),
               ("Lateral (YZ)", 0, 0, ("Y", "Z"), todos),
               ("Planta (XY)", 90, -90, ("X", "Y"), todos),
               ("Desde abajo (voladizos en rojo)", -35, -60, None, todos)]
    if detalle:
        det = [recortar(m, detalle) for m in meshes.values()]
        paneles.append((f"Detalle ±{detalle[3]:g} mm en ({detalle[0]:g}, {detalle[1]:g}, {detalle[2]:g})",
                        30, -60, None, [reducir(m) if m is not None else None for m in det]))
    else:
        paneles.append(("Isométrica trasera", 30, 120, None, todos))

    fig, axs = plt.subplots(2, 3, figsize=(13, 7.2), dpi=90)
    for ax, (titulo, el, az, ejes, grupo) in zip(axs.flat, paneles):
        pintar(ax, grupo, el, az, ejes, titulo)
    fig.suptitle("rojo = voladizo > 45° · medidas en mm", fontsize=8)
    fig.tight_layout()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta)
    plt.close(fig)


# ------------------------------------------------------------------------------- ensamble
def revisar_ensamble(ens: dict) -> list[str]:
    nombres = list(ens)
    out = []
    for i in range(len(nombres)):
        for j in range(i + 1, len(nombres)):
            a, b = ens[nombres[i]], ens[nombres[j]]
            try:
                inter = a & b
                v = float(getattr(inter, "volume", 0) or 0)
            except Exception:
                v = 0.0
            try:
                dist = float(a.distance_to(b))
            except Exception:
                dist = float("nan")
            if v > 1e-3:
                out.append(f"CHOQUE {nombres[i]}↔{nombres[j]}: se solapan {v:.3f} mm³ -> no encajan")
            else:
                nota = " (se tocan cara con cara: normal en hombros/topes; holguras laterales -> míralas en el modelo)" \
                    if dist < 1e-3 else ""
                out.append(f"ok {nombres[i]}↔{nombres[j]}: sin solape, separación mínima {dist:.3f} mm{nota}")
    return out


# ------------------------------------------------------------------------------- medir
def medir(mesh, cortes: list[str]) -> None:
    """Corta la malla con planos (p.ej. x=94, z=3) y da medidas de cada sección: contorno, huecos y área.
    Es la forma barata y exacta de comprobar cotas, holguras y profundidades sin mirar imágenes."""
    import numpy as np
    ejes = {"x": 0, "y": 1, "z": 2}
    nombres_uv = {0: ("Y", "Z"), 1: ("X", "Z"), 2: ("X", "Y")}
    for c in cortes:
        k, val = c.split("=")
        e = ejes[k.strip().lower()]
        val = float(val)
        nrm = np.zeros(3); nrm[e] = 1
        org = np.zeros(3); org[e] = val
        s = mesh.section(plane_origin=org, plane_normal=nrm)
        if s is None:
            log(f"{k}={val:g}: no corta la pieza")
            continue
        otros = [i for i in range(3) if i != e]
        verts = s.vertices[:, otros]
        import trimesh
        p2 = trimesh.path.Path2D(entities=s.entities, vertices=verts)
        u, v = nombres_uv[e]
        for poly in sorted(p2.polygons_full, key=lambda q: q.bounds[0]):
            b = poly.bounds
            huecos = []
            for h in poly.interiors:
                hb = h.bounds
                huecos.append(f"{hb[2] - hb[0]:.3f}×{hb[3] - hb[1]:.3f} en {u}[{hb[0]:.2f},{hb[2]:.2f}] {v}[{hb[1]:.2f},{hb[3]:.2f}]")
            log(f"{k}={val:g}: contorno {b[2] - b[0]:.3f}×{b[3] - b[1]:.3f} ({u}×{v}) en {u}[{b[0]:.2f},{b[2]:.2f}] "
                f"{v}[{b[1]:.2f},{b[3]:.2f}] área {poly.area:.2f} mm²" + (f" | huecos: {'; '.join(huecos)}" if huecos else ""))


# ----------------------------------------------------------------------------------- main
def cargar_stl(ruta: Path):
    import trimesh
    m = trimesh.load_mesh(ruta, force="mesh")
    return m


def informe(resultados: list[tuple[dict, list[str]]], extra: list[str], png: Path | None, t0: float) -> None:
    for info, avisos in resultados:
        log(json.dumps(info, ensure_ascii=False))
        for a in avisos:
            log(f"  ! {a}")
    for e in extra:
        log(f"  ensamble: {e}")
    if png:
        log(f"VISTA: {png}")
    log(f"({time.time() - t0:.1f} s)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["build", "check", "medir"])
    ap.add_argument("archivo")
    ap.add_argument("cortes", nargs="*", help="solo en medir: x=94 z=3 ...")
    ap.add_argument("--detalle", help="x,y,z,r zona a ampliar")
    ap.add_argument("--sin-vista", action="store_true")
    ap.add_argument("--material", default=PERFIL["material_por_defecto"])
    ap.add_argument("--tolerancia", type=float, default=0.01, help="desviación máx. de la malla STL (mm)")
    args = ap.parse_args()
    t0 = time.time()
    ruta = Path(args.archivo).resolve()
    detalle = tuple(float(v) for v in args.detalle.split(",")) if args.detalle else None
    import trimesh

    if args.modo == "medir":
        m = cargar_stl(ruta)
        log(f"{ruta.name}: límites {m.bounds.round(3).tolist()}")
        medir(m, args.cortes)
        return 0

    if args.modo == "check":
        m = cargar_stl(ruta)
        info, av, grave = analizar(m, ruta.name, args.material)
        png = None
        if not args.sin_vista:
            png = VISTAS / f"{ruta.stem}_vista.png"
            vista({ruta.stem: m}, png, detalle)
        informe([(info, av)], [], png, t0)
        return 2 if grave else 0

    # build
    from build123d import export_stl, Compound
    os.chdir(ruta.parent)
    try:
        ns = runpy.run_path(str(ruta), run_name="__modelo__")
    except Exception:
        tb = traceback.format_exc().strip().splitlines()
        log("ERROR en el modelo (últimas líneas):")
        log("\n".join(tb[-8:]))
        return 1
    if "resultado" not in ns:
        log("ERROR: el modelo no define `resultado`")
        return 1
    nombre = ns.get("NOMBRE", ruta.stem)
    res = ns["resultado"]
    piezas = res if isinstance(res, dict) else {nombre: res}
    salida = ns.get("SALIDA", "separadas") if isinstance(res, dict) else "separadas"
    detalle = detalle or ns.get("DETALLE")

    archivos: dict[str, Path] = {}
    if salida in ("separadas", "ambas"):
        for k, p in piezas.items():
            archivos[k if len(piezas) > 1 else nombre] = ruta.parent / f"{nombre}{'_' + k if len(piezas) > 1 else ''}.stl"
    if salida in ("placa", "ambas") and len(piezas) > 1:
        archivos["__placa__"] = ruta.parent / f"{nombre}.stl"

    resultados, mallas = [], {}
    grave_total = False
    for k, destino in archivos.items():
        forma = Compound(list(piezas.values())) if k == "__placa__" else piezas[k]
        # OCC no admite rutas con acentos/ñ en Windows: exporta a un nombre ASCII temporal y mueve
        tmp = Path(tempfile.gettempdir()) / f"impresion3d_{os.getpid()}_{len(resultados)}.stl"
        try:
            ok = export_stl(forma, str(tmp), tolerance=args.tolerancia, angular_tolerance=0.1)
        except Exception as e:
            log(f"ERROR exportando {k}: {e}")
            return 1
        if ok is False or not tmp.exists():
            log(f"ERROR: export_stl falló para {k}")
            return 1
        os.replace(tmp, destino)
        m = cargar_stl(destino)
        formatos = [f.lower() for f in PERFIL.get("formatos", ["stl"])]
        if "step" in formatos:  # exact CAD solid, for users who edit in Fusion/FreeCAD/Onshape
            from build123d import export_step
            tmp_s = tmp.with_suffix(".step")
            try:
                export_step(forma, str(tmp_s))
                os.replace(tmp_s, destino.with_suffix(".step"))
            except Exception as e:
                log(f"aviso: STEP no exportado ({e})")
        if "3mf" in formatos:
            try:
                m.export(destino.with_suffix(".3mf"))
            except Exception as e:
                log(f"aviso: 3MF no exportado ({e})")
        info, av, grave = analizar(m, destino.name, args.material)
        if k == "__placa__" and info.get("cuerpos", 1) > 1:
            av = [a for a in av]  # varias piezas en una placa es lo esperado
        grave_total |= grave
        resultados.append((info, av))
        if k != "__placa__":
            mallas[k] = m
    if not mallas and "__placa__" in archivos:
        mallas = {"placa": cargar_stl(archivos["__placa__"])}

    extra = revisar_ensamble(ns["ENSAMBLE"]) if isinstance(ns.get("ENSAMBLE"), dict) else []
    png = None
    if not args.sin_vista:
        png = VISTAS / f"{nombre}_vista.png"
        vista(mallas, png, detalle)
    log("STL: " + " | ".join(str(p) for p in archivos.values()))
    informe(resultados, extra, png, t0)
    return 2 if grave_total else 0


if __name__ == "__main__":
    sys.exit(main())
