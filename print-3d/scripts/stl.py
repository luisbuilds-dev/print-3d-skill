# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["trimesh", "manifold3d", "numpy", "scipy", "networkx", "shapely", "mapbox-earcut", "rtree"]
# ///
"""stl.py — operaciones sobre STL que ya existen (descargados o hechos antes). Booleanas con manifold3d.

  uv run stl.py info      pieza.stl
  uv run stl.py reparar   pieza.stl  salida.stl
  uv run stl.py escalar   pieza.stl  salida.stl  --factor 1.2 | --medida x=100 | --xyz 1,1,1.5
  uv run stl.py rotar     pieza.stl  salida.stl  --grados x=90,z=45        (y la apoya en z=0)
  uv run stl.py espejo    pieza.stl  salida.stl  --eje x
  uv run stl.py cortar    pieza.stl  salida_prefijo --plano z=10           -> _abajo.stl / _arriba.stl (tapados)
  uv run stl.py unir      a.stl b.stl ... salida.stl
  uv run stl.py restar    base.stl corte.stl ... salida.stl
  uv run stl.py intersecar a.stl b.stl salida.stl
  uv run stl.py mover     pieza.stl salida.stl --xyz 10,0,0
  uv run stl.py apoyar    pieza.stl salida.stl                             (z min = 0, centrada en XY)
  uv run stl.py cara-abajo pieza.stl salida.stl                            (gira para apoyar la cara plana más grande)

Para piezas nuevas desde STL (p.ej. añadir un agujero de lib3d a un STL), exporta el corte con cad.py y usa `restar`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh


def cargar(p: str) -> trimesh.Trimesh:
    m = trimesh.load_mesh(p, force="mesh")
    return m


def a_manifold(m: trimesh.Trimesh):
    import manifold3d as mf
    mesh = mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32))
    man = mf.Manifold(mesh)
    if man.status() != mf.Error.NoError:
        m2 = reparar_malla(m.copy())
        mesh = mf.Mesh(vert_properties=np.asarray(m2.vertices, np.float32), tri_verts=np.asarray(m2.faces, np.uint32))
        man = mf.Manifold(mesh)
        if man.status() != mf.Error.NoError:
            sys.exit(f"ERROR: la malla no es manifold ni tras reparar ({man.status()}). Prueba: stl.py reparar")
    return man


def de_manifold(man) -> trimesh.Trimesh:
    out = man.to_mesh()
    return trimesh.Trimesh(vertices=out.vert_properties[:, :3], faces=out.tri_verts, process=False)


def reparar_malla(m: trimesh.Trimesh) -> trimesh.Trimesh:
    m.merge_vertices()
    m.update_faces(m.nondegenerate_faces())
    m.update_faces(m.unique_faces())
    m.remove_unreferenced_vertices()
    trimesh.repair.fix_normals(m)
    trimesh.repair.fill_holes(m)
    return m


def guardar(m: trimesh.Trimesh, p: str) -> None:
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    m.export(p)
    s = m.bounds[1] - m.bounds[0]
    print(f"OK {p}: {s[0]:.2f} × {s[1]:.2f} × {s[2]:.2f} mm, cerrada={m.is_watertight}, cuerpos={m.body_count}, "
          f"vol={m.volume / 1000:.2f} cm³")


def apoyar(m: trimesh.Trimesh) -> trimesh.Trimesh:
    b = m.bounds
    m.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
    return m


def kv(s: str) -> dict:
    return {k.strip().lower(): float(v) for k, v in (p.split("=") for p in s.split(","))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("op")
    ap.add_argument("archivos", nargs="+")
    ap.add_argument("--factor", type=float)
    ap.add_argument("--medida")
    ap.add_argument("--xyz")
    ap.add_argument("--grados")
    ap.add_argument("--eje")
    ap.add_argument("--plano")
    a = ap.parse_args()
    op, f = a.op, a.archivos

    if op == "info":
        m = cargar(f[0])
        s = m.bounds[1] - m.bounds[0]
        print(f"{f[0]}: {s[0]:.2f} × {s[1]:.2f} × {s[2]:.2f} mm | límites {m.bounds.round(2).tolist()} | caras {len(m.faces)} | "
              f"cerrada={m.is_watertight} | cuerpos={m.body_count} | vol={m.volume / 1000:.2f} cm³")
        return
    if op == "reparar":
        guardar(reparar_malla(cargar(f[0])), f[1]); return
    if op == "escalar":
        m = cargar(f[0])
        s = m.bounds[1] - m.bounds[0]
        if a.factor:
            k = [a.factor] * 3
        elif a.medida:
            (eje, val), = kv(a.medida).items()
            k = [val / s["xyz".index(eje)]] * 3
        else:
            k = [float(v) for v in a.xyz.split(",")]
        m.apply_scale(k)
        print(f"factor {np.round(k, 4).tolist()}  (ojo: escala también agujeros y encajes; si hay tornillos, re-taladra)")
        guardar(apoyar(m), f[1]); return
    if op == "rotar":
        m = cargar(f[0])
        for eje, g in kv(a.grados).items():
            v = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}[eje]
            m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(g), v, m.centroid))
        guardar(apoyar(m), f[1]); return
    if op == "espejo":
        m = cargar(f[0])
        k = {"x": [-1, 1, 1], "y": [1, -1, 1], "z": [1, 1, -1]}[a.eje]
        m.apply_transform(np.diag(k + [1]))  # trimesh corrige el sentido de las caras
        guardar(apoyar(m), f[1]); return
    if op == "mover":
        m = cargar(f[0]); m.apply_translation([float(v) for v in a.xyz.split(",")]); guardar(m, f[1]); return
    if op == "apoyar":
        guardar(apoyar(cargar(f[0])), f[1]); return
    if op == "cara-abajo":
        m = cargar(f[0])
        facets_area = m.facets_area
        if len(facets_area) == 0:
            sys.exit("sin caras planas")
        n = m.facets_normal[int(np.argmax(facets_area))]
        m.apply_transform(trimesh.geometry.align_vectors(n, [0, 0, -1]))
        guardar(apoyar(m), f[1]); return
    if op == "cortar":
        m = cargar(f[0])
        (eje, val), = kv(a.plano).items()
        n = np.zeros(3); n["xyz".index(eje)] = 1
        o = np.zeros(3); o["xyz".index(eje)] = val
        arriba_m, abajo_m = a_manifold(m).split_by_plane(tuple(n), float(val))
        arriba, abajo = de_manifold(arriba_m), de_manifold(abajo_m)
        guardar(abajo, f[1] + "_abajo.stl")
        guardar(arriba, f[1] + "_arriba.stl"); return
    if op in ("unir", "restar", "intersecar"):
        mans = [a_manifold(cargar(p)) for p in f[:-1]]
        r = mans[0]
        for x in mans[1:]:
            r = r + x if op == "unir" else (r - x if op == "restar" else r ^ x)
        guardar(de_manifold(r), f[-1]); return
    sys.exit(f"operación desconocida: {op}")


if __name__ == "__main__":
    main()
