# Slicer settings — say them with the names of the user's slicer (`laminador` in the profile)

Orca family = OrcaSlicer, Bambu Studio, ElegooSlicer, Creality Print 6+, QIDI Studio, Anycubic Slicer Next, Snapmaker Orca, Orca-Flashforge.

| What | Orca family | PrusaSlicer | Cura |
|---|---|---|---|
| Layer height | Quality › Layer height | Print settings › Layers and perimeters › Layer height | Quality › Layer Height |
| Walls | Strength › Wall loops | Perimeters | Walls › Wall Line Count |
| Top/bottom | Strength › Top/Bottom shell layers | Solid layers › Top / Bottom | Top/Bottom Layers |
| Infill | Strength › Sparse infill density / pattern | Infill › Fill density / pattern | Infill Density / Pattern |
| Supports | Support › Enable support; type Tree (auto); "On build plate only" | Support material › Generate; Style: Organic; "On build plate only" | Support › Generate Support; Type: Tree; Placement: Touching Buildplate |
| Paint supports / blockers | Toolbar › Support painting | Toolbar › Paint-on supports | Plugin "Support Eraser" / mesh modifiers |
| Brim | Others › Brim type (Outer brim) | Skirt and brim › Brim width | Build Plate Adhesion › Brim |
| Elephant foot | Quality › Elephant foot compensation (0.1–0.15) | Advanced › Elephant foot compensation | Initial Layer Horizontal Expansion (−0.1) |
| Hole/fit correction | Quality › X-Y hole compensation (+0.05–0.1) | Advanced › XY size compensation | Hole Horizontal Expansion |
| Seam | Quality › Seam position (Back / Aligned) | Layers and perimeters › Seam position | Z Seam Alignment |
| Ironing (smooth top) | Quality › Ironing type: Top surfaces | Ironing › Enable | Ironing › Enable Ironing |
| Variable layer height | Right-click object › Adaptive layer height | Variable layer height tool | Adaptive Layers |
| Pause / filament change at height | Layer slider › right-click › Add pause / color change | Layer slider › + (color change) | Extension › Post Processing › Filament Change |
| Fuzzy skin (texture) | Others › Fuzzy skin | Layers and perimeters › Fuzzy skin | Experimental › Fuzzy Skin |

## Delivery template (2–4 lines, adapt to the part)
`Layer 0.2 (0.12–0.16 if there is small text/curves) · 3 walls · 15 % gyroid (functional: 4 walls, 30 %) ·
supports: none / tree, build plate only · brim: only for tall thin parts or ABS/ASA · orientation: <face> on the bed.`

## Defaults by printer type (the profile says `cinematica`)
- Bedslinger (A1, MK4S, Ender-3, Neptune, Kobra 3): tall thin parts wobble → brim, or lower speed; put the long axis along Y.
- CoreXY enclosed (P1S/P2S/X1, K1/K2, Centauri, CORE One, Q1/Q2): ABS/ASA ok with the door closed; PLA → open the lid/door or the hotend clogs (heat creep).
- Multi-colour (AMS, CFS, CANVAS, MMU, toolchanger): signature/text can be a second colour — design text as a separate body or rely on a colour change at height.
