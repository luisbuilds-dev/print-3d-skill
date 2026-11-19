# Onboarding form (run once per computer, ~2 minutes)

Trigger: `printer_profile.py status` prints `NO_PROFILE`, or the user says "set up / change my printer".
Speak the user's language. Two rounds of AskUserQuestion at most; the recommended option goes first.
Never invent a printer spec: use the preset or ask.

## Round 1 (4 questions)
1. **Printer**: run `$P printers <brand words>` first if the user already named it. Otherwise offer the 3 most
   common (Bambu Lab A1/P1S/P2S · Creality K1/Ender-3 V3 · Prusa MK4S/CORE One) + "Other" (they type the model).
   No preset → ask bed X×Y×Z and if it is enclosed, and use `--printer-name`, `--bed`, `--enclosed`.
2. **Nozzle**: 0.4 (recommended, the usual) · 0.6 (fast, strong) · 0.2 (fine detail).
3. **Slicer**: the preset's slicer first · OrcaSlicer · PrusaSlicer · Cura.
4. **Materials they have** (multiSelect): PLA · PETG · TPU · ABS/ASA (only if enclosed) · CF/other.

## Round 2 (up to 4 questions)
5. **Signature**: a short text to emboss on every new part (e.g. their handle `Name_`), or "No signature".
6. **File formats**: STL only (recommended) · STL + 3MF · STL + STEP (to edit in Fusion/FreeCAD/Onshape).
7. **Default style**: minimal tech · rounded/organic · industrial · plain (ask every time).
8. **Output folder**: next to each model (recommended) · a folder they type.
Optional free text: anything else ("I mostly print cosplay", "always ask me before supports").

## Save
```bash
$P init --printer <id> --nozzle 0.4 --slicer "OrcaSlicer" --material PLA --materials PLA,PETG \
   --signature "Name_" --formats stl --style "minimal tech" --language es --output-dir "" --notes "..."
```
Show the printed summary in 3 lines and say: "Saved. Change anything later with: «change my nozzle to 0.6»,
«my signature is …»". If they know a preset's figure is wrong (`verify bed size`), fix it with `--bed`.

## Calibration hint (offer once, optional)
Suggest printing the clearance test (`references/reglas-diseno.md` → probetas) and saving the result with
`$P tested deslizante 0.3 --material PLA --note "..."`. Real values beat every default.

## Later changes
- One value: `$P set preferencias.firma="New_"` · `$P set cama_mm=[300,300,300]` · `$P set formatos=["stl","3mf"]`.
- After a print the user reports ("the lid was too tight") → `$P tested tapa_caja 0.3 --material PETG --note "..."`.
- Different printer → run `init` again with `--printer`; it keeps their preferences and tested values.
