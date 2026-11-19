# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""publicar.py — Printables/MakerWorld pack: Blender renders + watermark (signature from the profile) + STL copies.

  uv run publicar.py pieza.stl [otra.stl ...] [--color "#c8f050"] [--salida carpeta] [--marca "@your_handle"]

Crea <carpeta del primer STL>/printables/ con: los STL, fotos/1_portada.png ... 4_trasera.png (con marca de agua).
La descripción (descripcion.md) la escribe Claude aparte. Las fotos crudas sin marca quedan en printables/_crudas/.
"""
import argparse, shutil, subprocess, sys, glob
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

AQUI = Path(__file__).parent
FUENTES = ["C:/Windows/Fonts/bahnschrift.ttf", "C:/Windows/Fonts/arialbd.ttf",
           "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


def blender() -> str:
    import os
    if os.environ.get("BLENDER"):
        return os.environ["BLENDER"]
    c = sorted(glob.glob("C:/Program Files/Blender Foundation/Blender*/blender.exe"))
    c += ["/Applications/Blender.app/Contents/MacOS/Blender"] if Path("/Applications/Blender.app").exists() else []
    c += [w for w in [shutil.which("blender")] if w]
    if not c:
        sys.exit("Blender not found: install it or set BLENDER=/path/to/blender")
    return c[-1]


def firma_perfil() -> str:
    sys.path.insert(0, str(AQUI))
    import printer_profile
    f = printer_profile.load().get("preferencias", {}).get("firma", "")
    return f"@{f.lstrip('@')}" if f else ""


def marca_agua(src: Path, dst: Path, texto: str) -> None:
    if not texto:
        Image.open(src).convert("RGB").save(dst, quality=92)
        return
    im = Image.open(src).convert("RGBA")
    W, H = im.size
    tam = int(H * 0.045)
    f = next((ImageFont.truetype(p, tam) for p in FUENTES if Path(p).exists()), ImageFont.load_default())
    capa = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    x0, y0, x1, y1 = d.textbbox((0, 0), texto, font=f)
    m = int(H * 0.035)
    x, y = W - (x1 - x0) - m, H - (y1 - y0) - m - y0
    sombra = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).text((x + 2, y + 2), texto, font=f, fill=(0, 0, 0, 160))
    sombra = sombra.filter(ImageFilter.GaussianBlur(3))
    d.text((x, y), texto, font=f, fill=(245, 242, 235, 200))
    # rayita de acento de la marca bajo el texto
    d.rectangle((x, y + (y1 - y0) + y0 + 6, x + int((x1 - x0) * 0.25), y + (y1 - y0) + y0 + 9), fill=(200, 240, 80, 220))
    Image.alpha_composite(Image.alpha_composite(im, sombra), capa).convert("RGB").save(dst, quality=92)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stl", nargs="+")
    ap.add_argument("--color", default="#c8f050")
    ap.add_argument("--salida")
    ap.add_argument("--marca", default=None, help="watermark text; default = signature in the profile; '' = none")
    a = ap.parse_args()
    if a.marca is None:
        a.marca = firma_perfil()
    stls = [Path(s).resolve() for s in a.stl]
    out = Path(a.salida).resolve() if a.salida else stls[0].parent / "printables"
    crudas, fotos = out / "_crudas", out / "fotos"
    crudas.mkdir(parents=True, exist_ok=True)
    fotos.mkdir(exist_ok=True)
    for s in stls:
        shutil.copy2(s, out / s.name)
    cmd = [blender(), "-b", "-P", str(AQUI / "render_blender.py"), "--", crudas.as_posix(), a.color, *[s.as_posix() for s in stls]]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    pngs = sorted(crudas.glob("*.png"))
    if r.returncode or not pngs:
        print(r.stdout[-2000:], r.stderr[-2000:])
        return 1
    for p in pngs:
        marca_agua(p, fotos / (p.stem + ".jpg"), a.marca)
    print("PAQUETE:", out)
    for p in sorted(fotos.glob("*.jpg")):
        print("  foto:", p.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
