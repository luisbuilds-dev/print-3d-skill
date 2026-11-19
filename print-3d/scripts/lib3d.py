"""lib3d — proven parts for FDM printing (build123d, algebra mode). Docstrings in Spanish; API documented in SKILL.md.

Uso dentro de un modelo:   from lib3d import *
Todas las funciones devuelven `Part`. Las que empiezan por `corte_` son para RESTAR (pieza - corte).
Los cortes nacen en el origen, apuntando hacia -Z desde z=0 (la cara superior de la pieza):
coloca con  Pos(x, y, z_cara) * corte   y gira con Rot(...) si la cara no mira a +Z.
Medidas en mm. Holguras sacadas de perfil-impresora.json (sección "probado" gana).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from build123d import *  # noqa: F401,F403  (los modelos usan `from lib3d import *` y reciben todo build123d)

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import printer_profile as _pp  # noqa: E402

PERFIL = _pp.load()                      # user's profile (~/.claude/print-3d/profile.json) over the defaults
REGLAS = PERFIL["reglas"]
HOLG = _pp.clearances(PERFIL)            # the "probado" (tested) block wins
FIRMA = PERFIL.get("preferencias", {}).get("firma", "")   # user's signature text ("" = none)
# English aliases for the clearance keys
for _es, _en in (("a_presion", "press"), ("ajustado", "snug"), ("deslizante", "sliding"), ("holgado", "loose"), ("tapa_caja", "lid")):
    HOLG[_en] = HOLG[_es]

PARED = REGLAS["pared_estructural_mm"]
EPS = 0.01  # sobremedida de los cortes para que no queden pieles de 0 mm

# --- tablas de tornillería (diámetros ya compensados para FDM) -----------------------
# paso: agujero pasante | cabeza Allen (DIN 912): Ø, alto | avellanada 90° (DIN 7991): Ø cabeza
# rosca_directa: agujero para que el tornillo haga rosca en el plástico
TORNILLO = {
    "M2":   dict(paso=2.4, cab_d=4.4,  cab_h=2.2, avell_d=4.4,  rosca=1.75, tuerca=4.0, tuerca_h=1.6),
    "M2.5": dict(paso=2.9, cab_d=5.0,  cab_h=2.7, avell_d=5.1,  rosca=2.2,  tuerca=5.0, tuerca_h=2.0),
    "M3":   dict(paso=3.4, cab_d=6.0,  cab_h=3.2, avell_d=6.4,  rosca=2.7,  tuerca=5.5, tuerca_h=2.4),
    "M4":   dict(paso=4.5, cab_d=7.8,  cab_h=4.2, avell_d=8.6,  rosca=3.6,  tuerca=7.0, tuerca_h=3.2),
    "M5":   dict(paso=5.5, cab_d=9.4,  cab_h=5.2, avell_d=10.8, rosca=4.5,  tuerca=8.0, tuerca_h=4.0),
    "M6":   dict(paso=6.6, cab_d=11.2, cab_h=6.2, avell_d=12.8, rosca=5.4,  tuerca=10.0, tuerca_h=5.0),
    # tornillo de madera/taco típico para colgar en pared (Ø4 y Ø5)
    "pared4": dict(paso=4.5, cab_d=8.4, cab_h=3.0, avell_d=8.8, rosca=3.0, tuerca=0, tuerca_h=0),
    "pared5": dict(paso=5.5, cab_d=10.0, cab_h=3.5, avell_d=10.4, rosca=3.8, tuerca=0, tuerca_h=0),
}
# insertos térmicos (tipo Ruthex/CNC Kitchen): Ø agujero, profundidad mínima
INSERTO = {"M2": (3.2, 4.0), "M2.5": (3.6, 5.0), "M3": (4.0, 5.7), "M4": (5.6, 8.1), "M5": (6.4, 9.5)}
# patrones VESA: separación entre agujeros (cuadrado) y métrica del tornillo
VESA = {75: ("M4", 75), 100: ("M4", 100), 200: ("M6", 200)}


def _cil(d: float, h: float) -> Part:
    """Cilindro de diámetro d desde z=0 hacia abajo hasta z=-h."""
    return Pos(0, 0, -h / 2) * Cylinder(d / 2, h)


# ------------------------------------------------------------------------- formas base
def caja(x: float, y: float, z: float, r: float = 2.0, chaflan_base: float | None = None,
         redondeo_arriba: float = 0.0) -> Part:
    """Bloque apoyado en z=0, centrado en XY, esquinas verticales redondeadas r.
    chaflan_base evita la 'pata de elefante' (por defecto el del perfil). redondeo_arriba suaviza el borde superior."""
    cb = REGLAS["chaflan_base_mm"] if chaflan_base is None else chaflan_base
    p = Pos(0, 0, z / 2) * Box(x, y, z)
    if r > 0:
        p = fillet(p.edges().filter_by(Axis.Z), min(r, x / 2 - 0.01, y / 2 - 0.01))
    if redondeo_arriba > 0:
        p = fillet(p.edges().group_by(Axis.Z)[-1], redondeo_arriba)
    if cb > 0:
        p = chamfer(p.edges().group_by(Axis.Z)[0], cb)
    return p


def caja_hueca(x: float, y: float, z: float, pared: float = PARED, suelo: float = 1.2,
               r: float = 3.0) -> Part:
    """Caja abierta por arriba. Medidas EXTERIORES. Interior con radio r-pared."""
    ext = caja(x, y, z, r)
    ri = max(r - pared, 0.3)
    hueco = Pos(0, 0, suelo + (z - suelo) / 2 + EPS) * Box(x - 2 * pared, y - 2 * pared, z - suelo + 2 * EPS)
    hueco = fillet(hueco.edges().filter_by(Axis.Z), ri)
    return ext - hueco


def tapa_para(x: float, y: float, pared: float = PARED, r: float = 3.0, grosor: float = 1.6,
              labio: float = 4.0, holgura: float | None = None) -> Part:
    """Tapa que encaja en caja_hueca(x, y, ..., pared, r). Se imprime boca abajo (labio hacia +Z)."""
    h = HOLG["tapa_caja"] if holgura is None else holgura
    placa = caja(x, y, grosor, r)
    xi, yi = x - 2 * pared - 2 * h, y - 2 * pared - 2 * h
    ri = max(r - pared - h, 0.3)
    lab = Pos(0, 0, grosor + labio / 2) * Box(xi, yi, labio)
    lab = fillet(lab.edges().filter_by(Axis.Z), ri)
    hueco = Pos(0, 0, grosor + labio / 2 + EPS) * Box(xi - 2 * 1.2, yi - 2 * 1.2, labio + 2 * EPS)
    hueco = fillet(hueco.edges().filter_by(Axis.Z), max(ri - 1.2, 0.3))
    return placa + lab - hueco


def placa(x: float, y: float, grosor: float = 3.0, r: float = 3.0) -> Part:
    """Placa plana con bordes superiores suavizados."""
    return caja(x, y, grosor, r, redondeo_arriba=min(0.8, grosor / 3))


# ---------------------------------------------------------------------- cortes (restar)
def corte_tornillo(m: str = "M3", largo: float = 20.0, cabeza: str = "allen") -> Part:
    """Agujero pasante con alojamiento de cabeza en z=0.
    cabeza: 'allen' (rebaje cilíndrico), 'avellanado' (cono 90°) o 'ninguna'."""
    t = TORNILLO[m]
    c = _cil(t["paso"], largo + EPS)
    c = Pos(0, 0, EPS) * c
    if cabeza == "allen":
        c += Pos(0, 0, EPS) * _cil(t["cab_d"], t["cab_h"] + EPS)
    elif cabeza == "avellanado":
        prof = (t["avell_d"] - t["paso"]) / 2
        c += Pos(0, 0, -prof) * Cone(t["paso"] / 2, t["avell_d"] / 2, prof,
                                    align=(Align.CENTER, Align.CENTER, Align.MIN))
        c += Pos(0, 0, 0.5) * _cil(t["avell_d"], 0.5)  # sobremedida por encima de la cara
    return c


def corte_rosca_directa(m: str = "M3", prof: float = 10.0) -> Part:
    """Agujero ciego para que el tornillo haga su propia rosca en el plástico."""
    return Pos(0, 0, EPS) * _cil(TORNILLO[m]["rosca"], prof + EPS)


def corte_inserto(m: str = "M3", prof: float | None = None) -> Part:
    """Agujero para inserto térmico (con 0.5 mm extra de profundidad para el plástico desplazado)."""
    d, p = INSERTO[m]
    return Pos(0, 0, EPS) * _cil(d, (prof or p) + 0.5 + EPS)


def corte_tuerca(m: str = "M3", prof: float | None = None, holgura: float = 0.15) -> Part:
    """Alojamiento hexagonal para tuerca (entre caras + holgura), boca en z=0."""
    t = TORNILLO[m]
    h = (prof or t["tuerca_h"] + 0.2) + EPS
    entre_caras = t["tuerca"] + 2 * holgura
    hexa = extrude(RegularPolygon(entre_caras / math.sqrt(3), 6, major_radius=True), h)
    return Pos(0, 0, EPS - h) * hexa


def corte_iman(d: float, h: float, ajuste: str = "a_presion") -> Part:
    """Hueco para imán de disco. ajuste: 'a_presion' o 'holgado' (para pegar)."""
    return Pos(0, 0, EPS) * _cil(d + 2 * HOLG[ajuste], h + 0.2 + EPS)


def corte_lagrima(d: float, largo: float) -> Part:
    """Agujero HORIZONTAL imprimible sin soportes (punta a 45° hacia +Z). Eje a lo largo de X, centrado."""
    r = d / 2
    s = Circle(r) + Rot(0, 0, 45) * Rectangle(r, r, align=(Align.MIN, Align.MIN))
    s = Plane.YZ * s
    return Pos(-largo / 2, 0, 0) * extrude(s, largo)


def corte_ranura(ancho: float, largo: float, prof: float) -> Part:
    """Ranura alargada (colgador de pared / ajuste). Eje X, centrada, boca en z=0."""
    return Pos(0, 0, -prof) * extrude(SlotCenterToCenter(largo, ancho), prof + EPS)


def corte_colgador(cabeza_d: float = 8.4, cuello_d: float = 4.5, recorrido: float = 8.0,
                   prof: float = 6.0, alto_cabeza: float = 3.0) -> Part:
    """Ojo de cerradura para colgar de un tornillo (se mete por el círculo grande y baja por la ranura).
    Se resta desde la cara TRASERA (la que toca la pared), boca en z=0 hacia -Z. Ranura hacia +Y."""
    grande = _cil(cabeza_d, prof + EPS)
    cuello = Pos(0, recorrido / 2, -(prof + EPS) / 2) * Box(cuello_d, recorrido, prof + EPS)
    cuello += Pos(0, recorrido, 0) * _cil(cuello_d, prof + EPS)
    bajo = Pos(0, recorrido / 2, -(prof - alto_cabeza) - alto_cabeza / 2 - EPS / 2) * Box(cabeza_d, recorrido, alto_cabeza + EPS)
    bajo += Pos(0, recorrido, -(prof - alto_cabeza)) * _cil(cabeza_d, alto_cabeza + EPS)
    return Pos(0, 0, EPS) * (grande + cuello + bajo)


def puntos_vesa(tam: int = 100) -> list[tuple[float, float]]:
    """Las 4 posiciones de agujero de un patrón VESA, centradas en el origen."""
    s = VESA[tam][1] / 2
    return [(-s, -s), (s, -s), (-s, s), (s, s)]


# ---------------------------------------------------------------------------- texto
def texto(t: str, tam: float = 8.0, prof: float = 0.6, fuente: str = "Arial",
          estilo: str = "negrita", alinear: str = "centro") -> Part:
    """Texto extruido desde z=0 hacia +Z (súmalo para relieve; réstalo con Pos(0,0,-prof) para grabado).
    tam = altura de mayúscula aprox. Trazos < 0.5 mm no salen: usa tam >= 5 y negrita."""
    fs = {"negrita": FontStyle.BOLD, "normal": FontStyle.REGULAR, "cursiva": FontStyle.ITALIC}[estilo]
    al = {"centro": (Align.CENTER, Align.CENTER), "izquierda": (Align.MIN, Align.CENTER)}[alinear]
    sk = Text(t, font_size=tam * 1.4, font=fuente, font_style=fs, align=al)
    return extrude(sk, prof)


# ---------------------------------------------------------------------------- utilidades
def apoyar(p: Part) -> Part:
    """Baja la pieza a z=0 y la centra en XY (orientación de impresión)."""
    bb = p.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * p


def matriz(p: Part, nx: int, ny: int, dx: float, dy: float) -> Part:
    """Repite p en rejilla nx × ny centrada."""
    out = None
    for i in range(nx):
        for j in range(ny):
            q = Pos((i - (nx - 1) / 2) * dx, (j - (ny - 1) / 2) * dy, 0) * p
            out = q if out is None else out + q
    return out


def medidas(p: Part) -> str:
    bb = p.bounding_box()
    return f"{bb.size.X:.1f} × {bb.size.Y:.1f} × {bb.size.Z:.1f} mm"
