# Common hardware dimensions (mm) — use these instead of searching; confirm with calipers if the fit is critical

## Fans (square frame)
| Size | Hole spacing | Hole Ø (self-tap fan screw) | Air opening Ø | Common thickness |
|---|---|---|---|---|
| 40 | 32 | 3.4 | 38 | 10 / 20 |
| 50 | 40 | 3.4 | 48 | 10 / 15 |
| 60 | 50 | 4.3 | 58 | 15 / 25 |
| 80 | 71.5 | 4.5 | 78 | 25 |
| 92 | 82.5 | 4.5 | 89 | 25 |
| 120 | 105 | 4.5 | 116 | 25 |
| 140 | 124.5 | 4.5 | 136 | 25 |
Air flows toward the side with the frame struts/label (exhaust). Filters go on the intake side.

## Boards (mounting holes, centre to centre)
- Raspberry Pi 5/4/3B+: board 85×56, holes 58×49, M2.5 (Ø2.7), 3.5 from edges. Pi Zero: 65×30, holes 58×23.
- Arduino Uno: 68.6×53.4, holes at (14,2.5) (15.3,50.7) (66.1,7.6) (66.1,35.5), Ø3.2.
- ESP32 DevKitC: ~55×28 (varies) — no standard holes: design a slot/clip, ask for measurements.

## Bearings, magnets, rods
- 608 (skateboard): 8×22×7. 625: 5×16×5. 6200: 10×30×9. LM8UU: 8×15×24.
- Neodymium discs common: 6×2, 6×3, 8×3, 10×2, 10×3, 12×3, 20×3 → `corte_iman(d, h)`.
- Smooth rod 8 mm: hole 8.2 (sliding) / 7.9 (press).

## Camera / photo
- 1/4"-20 UNC (tripod): screw Ø6.35; print a hex pocket for a 1/4" nut (11.1 across flats, 5.6 thick) instead of printing the thread.
- GoPro mount: fingers 3 mm thick, 3 mm gaps (2 or 3 prongs), M5 bolt (Ø5.3 hole), finger outer Ø ~15.

## Extrusions & DIY
- 2020 aluminium profile: slot 6.2 wide, M5 T-nuts. 3030: slot 8.2, M6. 4040: slot 8.2/10, M8.
- Wood screws for wall plugs: Ø3.5–4 → profile shortcuts `"pared4"`, `"pared5"` in `corte_tornillo`.
- Pegboard (IKEA Skådis): holes 5×15 slots, 20 mm pitch (staggered 40). Standard pegboard 1/4" holes, 1" pitch.
- Gridfinity: 42×42 grid, 7 mm height unit, base profile 0.8/1.8/2.15 — use an existing generator if asked for many bins.

## Electrical
- USB-C port cutout: 9.2×3.4 (plug body needs 12.5×6.5). USB-A: 13×6. Barrel jack 5.5/2.1: panel hole Ø8 or Ø11 (varies).
- LED strip: 8 / 10 / 12 mm wide, ~2 mm thick (+silicone ~4).
- 18650 cell: Ø18.5×65 (holder Ø18.8–19.0). AA: Ø14.5×50.5. AAA: Ø10.5×44.5. CR2032: Ø20×3.2.
- Toggle switch 12 mm/6 mm round, rocker KCD1: 21×15 cutout.

## Household
- Standard toothbrush handle ~15–20; shower rail Ø19/22/25; curtain rods Ø16/19/25/28.
- Door thickness ~35–45 (hooks over doors: 40 + 2× clearance).
- Phones/tablets: ask the model; never guess dimensions.
