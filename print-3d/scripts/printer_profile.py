# /// script
# requires-python = ">=3.11"
# ///
"""printer_profile.py — the user's printer profile (created by the onboarding form, lives OUTSIDE the skill).

Location: $PRINT3D_PROFILE, else ~/.claude/print-3d/profile.json  (survives skill updates; one per computer).
Missing keys fall back to ../profile.default.json. The "probado" (tested) block wins over everything.

  uv run printer_profile.py status                       -> NO_PROFILE | compact summary (cheap: ~10 lines)
  uv run printer_profile.py printers [search words]      -> presets from references/printers.json
  uv run printer_profile.py init --printer bambu-p1s [--nozzle 0.4] [--slicer OrcaSlicer] [--material PLA]
         [--materials PLA,PETG] [--signature "MyName_"] [--output-dir PATH] [--formats stl,3mf,step]
         [--style "minimal tech"] [--language es] [--bed 256,256,256] [--enclosed yes|no] [--name "Ana"] [--notes ".."]
  uv run printer_profile.py set key.sub=value [...]      -> e.g. preferencias.firma="" holguras_por_lado_mm.deslizante=0.3
  uv run printer_profile.py tested deslizante 0.3 --material PETG --note "lid slides fine"
"""
from __future__ import annotations

import argparse
import copy
import datetime as _dt
import json
import os
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
DEFAULT = SKILL / "profile.default.json"
PRINTERS = SKILL / "references" / "printers.json"


def path() -> Path:
    env = os.environ.get("PRINT3D_PROFILE")
    return Path(env).expanduser() if env else Path.home() / ".claude" / "print-3d" / "profile.json"


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def exists() -> bool:
    return path().exists()


def raw_user() -> dict:
    p = path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def load() -> dict:
    """Default profile merged with the user's. Always returns a complete dict."""
    return _merge(json.loads(DEFAULT.read_text(encoding="utf-8")), raw_user())


def clearances(prof: dict) -> dict:
    h = dict(prof["holguras_por_lado_mm"])
    for k, v in prof.get("probado", {}).items():
        if not k.startswith("_") and isinstance(v, dict) and k in h:
            h[k] = v["valor"]
    return h


def _save(data: dict) -> Path:
    p = path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _presets() -> dict:
    return json.loads(PRINTERS.read_text(encoding="utf-8"))["printers"]


def _value(s: str):
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return s


def cmd_status() -> int:
    if not exists():
        print(f"NO_PROFILE  (expected at {path()}) -> run the onboarding form (references/onboarding.md)")
        return 3
    p = load()
    pref = p.get("preferencias", {})
    tested = [f"{k}={v['valor']}" for k, v in p.get("probado", {}).items() if not k.startswith("_") and isinstance(v, dict)]
    print(f"printer: {p['impresora']} | bed {p['cama_mm']} | nozzle {p['boquilla_mm']} | enclosed {p.get('cerrada')}")
    print(f"slicer: {p['laminador']} | material {p['material_por_defecto']} | has {', '.join(p.get('materiales', []))}")
    print(f"clearances/side: {clearances(p)}" + (f" | tested: {', '.join(tested)}" if tested else ""))
    print(f"output: {p.get('carpeta_salida') or '(next to the model)'} | formats {p.get('formatos', ['stl'])}")
    print(f"signature: {pref.get('firma') or '(none)'} | style: {pref.get('estilo') or '(ask)'} | "
          f"language: {pref.get('idioma') or '(user)'} | ask before modelling: {pref.get('preguntar_antes', True)}")
    if pref.get("notas"):
        print(f"notes: {pref['notas']}")
    print(f"profile: {path()}")
    return 0


def cmd_printers(words: list[str]) -> int:
    q = [w.lower() for w in words]
    for pid, d in _presets().items():
        line = f"{pid}: {d['nombre']} | bed {d['cama_mm']} | {'enclosed' if d.get('cerrada') else 'open'} | {d.get('laminador', '')}"
        if all(w in line.lower() for w in q):
            print(line + (" | verify bed size" if d.get("verificar") else ""))
    return 0


def cmd_init(a) -> int:
    data = raw_user()
    pre = {}
    if a.printer:
        presets = _presets()
        if a.printer not in presets:
            print(f"Unknown preset '{a.printer}'. Use `printers <words>` or pass --bed/--enclosed with --name-printer.")
            return 1
        pre = presets[a.printer]
    if pre or a.printer_name:
        data["impresora"] = a.printer_name or pre["nombre"]
    for k_pre, k_prof in (("cama_mm", "cama_mm"), ("cerrada", "cerrada"), ("boquilla_max_c", "boquilla_max_c"),
                          ("cama_max_c", "cama_max_c"), ("laminador", "laminador"), ("cinematica", "cinematica")):
        if k_pre in pre:
            data[k_prof] = pre[k_pre]
    if a.bed:
        data["cama_mm"] = [float(v) for v in a.bed.split(",")]
    if a.enclosed:
        data["cerrada"] = a.enclosed.lower() in ("yes", "si", "sí", "true", "1")
    if a.nozzle:
        n = float(a.nozzle)
        data["boquilla_mm"], data["ancho_linea_mm"] = n, round(n * 1.05, 2)
        data["capa_mm"] = {"fina": round(n * 0.3, 2), "normal": round(n * 0.5, 2), "rapida": round(n * 0.7, 2)}
        data.setdefault("reglas", {})["pared_min_mm"] = round(2 * n * 1.05, 2)
        data["reglas"]["detalle_min_mm"] = round(n * 1.25, 2)
    if a.slicer:
        data["laminador"] = a.slicer
    if a.material:
        data["material_por_defecto"] = a.material
    if a.materials:
        data["materiales"] = [m.strip() for m in a.materials.split(",") if m.strip()]
    if a.output_dir is not None:
        data["carpeta_salida"] = a.output_dir.replace("\\", "/")
    if a.formats:
        data["formatos"] = [f.strip().lower() for f in a.formats.split(",") if f.strip()]
    pref = data.setdefault("preferencias", {})
    for arg, key in (("signature", "firma"), ("style", "estilo"), ("language", "idioma"), ("name", "nombre"), ("notes", "notas")):
        v = getattr(a, arg)
        if v is not None:
            pref[key] = v
    data.setdefault("probado", {"_nota": "Values confirmed by real prints. They win over everything. "
                                         "Add with: printer_profile.py tested <key> <value> --material X --note '...'"})
    data["actualizado"] = _dt.date.today().isoformat()
    print(f"saved {_save(data)}")
    return cmd_status()


def cmd_set(pairs: list[str]) -> int:
    data = raw_user()
    for pair in pairs:
        key, _, val = pair.partition("=")
        node = data
        parts = key.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = _value(val)
    _save(data)
    return cmd_status()


def cmd_tested(a) -> int:
    data = raw_user()
    data.setdefault("probado", {})[a.key] = {"valor": _value(a.value), "material": a.material,
                                            "fecha": _dt.date.today().isoformat(), "nota": a.note or ""}
    _save(data)
    return cmd_status()


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    pr = sub.add_parser("printers"); pr.add_argument("words", nargs="*")
    i = sub.add_parser("init")
    for opt in ("printer", "printer-name", "nozzle", "slicer", "material", "materials", "signature", "output-dir",
                "formats", "style", "language", "bed", "enclosed", "name", "notes"):
        i.add_argument("--" + opt)
    s = sub.add_parser("set"); s.add_argument("pairs", nargs="+")
    t = sub.add_parser("tested"); t.add_argument("key"); t.add_argument("value")
    t.add_argument("--material", default="PLA"); t.add_argument("--note")
    a = ap.parse_args()
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    return {"status": lambda: cmd_status(), "printers": lambda: cmd_printers(a.words), "init": lambda: cmd_init(a),
            "set": lambda: cmd_set(a.pairs), "tested": lambda: cmd_tested(a)}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
