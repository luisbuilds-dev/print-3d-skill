# Materials (pick by use, then design for it)

Temps are typical starting points; the filament box wins. "Encl." = needs an enclosed printer (check `cerrada`).

| Material | Nozzle °C | Bed °C | Encl. | Heat (HDT approx.) | Use it for | Design notes |
|---|---|---|---|---|---|---|
| PLA | 200–220 | 55–65 | no | ~55 °C | indoor parts, prototypes, decor, signs | stiff but brittle; creeps under constant load; sun-heated car = deforms |
| PLA+ / Tough PLA | 205–230 | 55–65 | no | ~55–60 °C | snap fits, brackets indoors | tougher than PLA, same heat limit |
| PETG | 230–250 | 70–85 | no | ~70 °C | functional, outdoor shade, water, food-adjacent | stringy; bridges sag more (keep ≤ 8 mm); add +0.05 mm clearance; sticks too hard to PEI smooth → glue stick |
| PCTG | 240–260 | 70–85 | no | ~70 °C | like PETG but tougher, clearer | same rules as PETG |
| ABS | 240–260 | 95–110 | yes | ~95 °C | car interiors, heat, acetone smoothing | warps: big flat parts need brim + rounded corners; fumes → ventilate |
| ASA | 240–260 | 95–110 | yes | ~95 °C | outdoor (UV-stable), garden, car exterior | like ABS, less warping |
| TPU 95A | 220–235 | 40–60 | no | — | grips, bumpers, gaskets, phone cases | print slow (≤ 40 mm/s, or the profile's TPU preset); walls ≥ 1.2 mm; no tight clearances (flexes); avoid bridges/supports |
| PC / PC blend | 260–290 | 100–115 | yes | ~110 °C | strong + hot parts | needs ≥ 280 °C hotend capability (check `boquilla_max_c`) |
| Nylon PA / PA-CF | 260–290 | 80–100 | yes | 80–150 °C | gears, hinges, wear parts | dry the spool (absorbs water); CF needs hardened nozzle |
| PLA-CF / PETG-CF | base +10 °C | as base | as base | as base | stiff, matte, dimensionally stable | hardened-steel nozzle; ≥ 0.4 mm nozzle; slightly brittle; good for brackets |

## Choosing (ask only if use/environment is unclear)
- Indoors, no heat, no load → **PLA**.
- Outdoors, sun, water, or ≥ 50 °C (car, near electronics, 3D printer enclosure) → **PETG** (open printer) or **ASA** (enclosed).
- Must bend / absorb shocks → **TPU**. Must slide / wear → **PA** or PETG.
- Load-bearing screw bosses in PLA → use heat-set inserts (`corte_inserto`) rather than self-tapping.
- The user's printer can't heat enough (`boquilla_max_c` < material min) or isn't enclosed for ABS/ASA/PC/PA → say so and offer PETG.

## Shrinkage / fit (add to the clearance table if no tested values)
PLA 0 · PETG +0.05 · ABS/ASA +0.1 (holes shrink: +0.2 on Ø) · TPU +0.1 · PA +0.1 (mm per side).

## Strength rules of thumb
- Layers are the weak direction: orient so the load is along the layers, not pulling them apart.
- 3–4 walls give more strength than more infill. Functional parts: 4 walls, 25–40 % gyroid. Decor: 2 walls, 10–15 %.
- Screw bosses: outer Ø ≥ 2.5 × screw Ø; walls around inserts ≥ 1.6 mm.
