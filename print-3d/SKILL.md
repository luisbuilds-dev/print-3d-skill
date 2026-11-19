---
name: print-3d
description: Designs, edits and validates parts for FDM 3D printing, tuned to the user's own printer (saved profile created by a one-time onboarding form). Models in code (build123d) with a library of proven features (screws, heat-set inserts, nuts, magnets, boxes with lids, text, VESA, hangers), checks printability (closed mesh, fits the bed, overhangs, thin walls, bed contact, collisions between parts), measures the real STL and exports STL (+3MF/STEP if wanted). Also edits downloaded STLs (scale, cut, join, subtract, mirror, repair). Use when the user asks to "design a part", "make a bracket/adapter/box/keychain/sign/holder", "modify this STL", "make it bigger", "cut it in two", "add a hole", "make it fit…", "generate the STL", "set up my printer", or talks about their 3D printer. Responde en el idioma del usuario (español incluido).
---

# print-3d — from idea to a validated STL for the user's printer

Reply in the user's language. `SK` = the folder of this file.
```bash
SK="<folder of this SKILL.md>"   # quoted: paths may contain spaces
C() { uv run -q "$SK/scripts/cad.py" "$@"; }              # build / check / medir (measure)
S() { uv run -q "$SK/scripts/stl.py" "$@"; }              # edit existing STL files
P() { uv run -q "$SK/scripts/printer_profile.py" "$@"; }  # profile: status / printers / init / set / tested
```
Below, `$C`, `$S`, `$P` mean these functions (define them in each Bash call; PowerShell: `uv run -q "$SK/scripts/cad.py" ...`).
`uv` installs everything (build123d 0.13, trimesh, manifold3d) on first run (~1 min). Never call bare `python`.
No `uv`? → tell the user: `pip install uv` or https://docs.astral.sh/uv/ (one command), then continue.

## 0. Profile first (every session, ~10 lines)
Run `$P status`. **`NO_PROFILE` → run the onboarding form** (`references/onboarding.md`) before designing.
The summary gives printer, bed, nozzle, enclosure, slicer, materials, clearances, signature, style, formats.
Use it; don't re-ask what it already says. The `probado` (tested) values beat every default.
The user changes something ("my nozzle is now 0.6", "no signature") → `$P set ...` / `init` and confirm in one line.

## Token rules (mandatory)
- **Don't read** `lib3d.py`, `cad.py`, `stl.py`, `printers.json`: the API is below. Read `references/` only when needed.
- Verify with **numbers** (build report + `medir`), not images. Look at the PNG (one image, 6 views) only for the
  first version, after a shape change, or if a warning is unclear. Parameter change → `--sin-vista`.
- Changes: `Edit` the model's parameters, never rewrite the file. Complex part: phases (body → features → finish),
  each with `--sin-vista`, the view at the end.

## Workflow
1. **Ask BEFORE modelling** (unless `preferencias.preguntar_antes` is false): one round, **max 5 questions**
   (AskUserQuestion takes 4; the 5th goes in text; recommended option first) about what is missing or ambiguous:
   what it is and what for · critical dimensions (exact? inner/outer? measured with calipers?) · mounting (screw
   type/size, glue, tape, press fit; from which side) · load & environment (→ material, `references/materials.md`) ·
   **design style** (default `preferencias.estilo`, else ask: minimal tech, rounded/organic, industrial, plain) and
   **which face gets the signature/detail** (propose the most visible face that doesn't touch the bed or another part).
   Skip only when the request already has all dimensions and mounting (a drawing) or it is a tweak of an existing design.
   Unanswered → profile defaults, and say so at delivery. Standard parts (fans, Pi, bearings…) → `references/hardware.md`.
2. **New or existing?** New → build123d model. Existing STL → `$S`. Mix → lib3d cut exported as STL + `$S restar/unir`.
3. **Orientation first**: big flat face down, loads along the layers, precise holes vertical, no overhang > 45°.
   Model in print position (z=0 = bed). Doubts → `references/reglas-diseno.md`.
4. **Model** in `<carpeta_salida or the current folder>/<name>/<name>.py`. Start from a recipe if one fits
   (`references/recetas.md`: keychain, sign, bracket, box+lid, tube adapter, tenon, hook).
5. **Build**: `cd` there and `$C build <name>.py`. `ERROR en el modelo` → read only those lines and fix;
   build123d issue → `references/build123d.md`.
6. **Validate**: read the report. `GRAVE` = must fix. Overhang zones → bridge ≤ 10 mm supported both sides? ok;
   else 45° chamfer, `corte_lagrima`, reorient or, last resort, supports (say it). Critical fits →
   `$C medir part.stl x=.. z=..` and compare with what was asked.
7. **Deliver** (short): file path · size · grams · orientation on the bed · 2–4 slicer lines **using the names of
   the user's slicer** (`references/slicers.md`) · remaining warnings. Ask how it fitted after printing and save it:
   `$P tested <clearance> <value> --material X --note "..."`.

## Signature (if `preferencias.firma` is not empty)
Emboss it on every new part (lib3d exposes it as `FIRMA`), on the face chosen in step 1.
- Top face (+Z): relief 0.6–0.8 mm, size ≥ 5. Best quality.
- Vertical face: relief 0.6 mm (letter undersides overhang 0.6 mm: they print fine; the validator lists them as
  small overhang zones — not a problem). Proven:
  `Plane(origin=(x_face - EPS, y, z), x_dir=(0, s, 0), z_dir=(s, 0, 0)).location * texto(FIRMA, 8, 0.6 + EPS)`
  (s = +1 for the +X face, −1 for −X; for ±Y faces: `x_dir=(-s, 0, 0), z_dir=(0, s, 0)`).
- Never on the bed face or where it touches another part. Tiny part (face < ~40 mm) → initials.
- Tech font `"Bahnschrift"` (Windows) / `"DejaVu Sans"`; robust `"Arial Black"`. Constants on top: `F_TAM, F_PROF`.

## Model contract
```python
from lib3d import *            # all of build123d + lib3d
NOMBRE = "bracket"             # output name
WIDTH = 40                     # parameters on top, UPPERCASE, mm
resultado = part               # Part, or {"a": p1, "b": p2}
SALIDA = "separadas"           # dict: "separadas" (one file per part) | "placa" (one plate) | "ambas"
ENSAMBLE = {"a": p1, "b": Pos(..) * p2}   # optional: assembled parts -> checks overlaps and gaps
DETALLE = (x, y, z, r)         # optional: zoom area in the preview
```
Several parts on one plate: ≥ 5 mm apart.

## lib3d (all return Part; `corte_*` = cuts to SUBTRACT, mouth at z=0 pointing −Z)
| Function | What |
|---|---|
| `caja(x,y,z, r=2, chaflan_base=None, redondeo_arriba=0)` | block on z=0, rounded corners, anti elephant-foot chamfer |
| `caja_hueca(x,y,z, pared=1.6, suelo=1.2, r=3)` / `tapa_para(x,y, ...)` | open box + matching lid (profile clearance) |
| `placa(x,y, grosor=3, r=3)` | plate with soft top edge |
| `corte_tornillo(m, largo, cabeza="allen"/"avellanado"/"ninguna")` | screw hole M2–M6 (allen / countersunk / none), `"pared4"`, `"pared5"` = wood screw |
| `corte_rosca_directa(m, prof)` · `corte_inserto(m)` · `corte_tuerca(m)` | self-tap hole · heat-set insert · hex nut pocket |
| `corte_iman(d, h, ajuste="a_presion"/"holgado")` | magnet pocket (press / loose) |
| `corte_lagrima(d, largo)` | horizontal hole (X axis), teardrop, no supports |
| `corte_ranura(ancho, largo, prof)` · `corte_colgador()` | slot · keyhole hanger (from the back face) |
| `texto(t, tam=8, prof=0.6, fuente="Arial", estilo="negrita")` | text extruded +Z (add = relief, subtract = engraved) |
| `puntos_vesa(75/100/200)` · `matriz(p, nx, ny, dx, dy)` · `apoyar(p)` · `medidas(p)` | VESA points · array · drop to bed · size |
Constants: `HOLG[...]` clearance per side — `"a_presion"|"ajustado"|"deslizante"|"holgado"|"tapa_caja"`
(aliases `press|snug|sliding|loose|lid`), `PARED`, `EPS`, `TORNILLO`, `INSERTO`, `FIRMA`, `PERFIL`.
Cut on a face not facing +Z: `Pos(x,y,z_face) * Rot(...) * cut` (e.g. −X wall: `Rot(0,-90,0)`).

## Commands
```bash
$C build model.py [--detalle x,y,z,r] [--sin-vista] [--material PETG]   # files + report + preview (TEMP/impresion-3d)
$C check part.stl [--detalle ...]                                       # validate any STL (downloads too)
$C medir part.stl x=94 z=3                                              # exact sections: outline, holes, area
$S info|reparar|apoyar|cara-abajo part.stl [out.stl]                    # info / repair / drop to bed / best face down
$S escalar part.stl out.stl --factor 1.2 | --medida x=100 | --xyz 1,1,1.5
$S rotar part.stl out.stl --grados x=90,z=45      ·   $S espejo part.stl out.stl --eje x
$S cortar part.stl prefix --plano z=10            ·   $S mover part.stl out.stl --xyz 10,0,0
$S unir a.stl b.stl out.stl  ·  $S restar base.stl cut.stl out.stl  ·  $S intersecar a.stl b.stl out.stl
uv run -q $SK/scripts/publicar.py part.stl [--color "#hex"]   # Printables/MakerWorld photos (needs Blender)
```
Scaling an STL also scales its holes: if it has screws/magnets, say so and re-drill with `restar`.
Report: `cuerpos` > 1 in one part = loose pieces (error except plates). Exit code 2 = serious problem.
Report words are Spanish: GRAVE = serious, zona colgante = overhang, pared fina = thin wall, cama = bed.

## References (on demand)
- `references/onboarding.md` — the first-run form and how to change the profile.
- `references/materials.md` — temps, enclosure, heat, use, design notes per material.
- `references/slicers.md` — setting names in Orca/Bambu/Elegoo/Creality, PrusaSlicer, Cura + delivery template.
- `references/hardware.md` — fans, boards, bearings, magnets, camera, extrusions, batteries, ports.
- `references/reglas-diseno.md` — overhangs, bridges, walls, clearances, screws, test prints (Spanish).
- `references/build123d.md` — revolve, loft, sweep, helix, shell, mirror, patterns, edge selection, known traps.
- `references/recetas.md` — complete proven models.
