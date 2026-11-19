# Reglas de diseño FDM (boquilla 0,4) — design rules (Spanish; Claude reads both)

Procedencia: [comunidad] = consenso de guías/skills públicas · [regla] = regla general · [medido] = medido en impresiones reales del autor
(lo medido va en perfil-impresora.json → "probado" y gana siempre).

## Orientación (decídela ANTES de modelar)
1. La cara plana más grande, abajo. Nada de apoyar sobre curvas o aristas.
2. Las cargas de tracción/flexión van **a lo largo de las capas** (en XY), nunca separándolas (Z). Un gancho
   se imprime tumbado, no de pie. [regla]
3. Agujeros que deben ser redondos y precisos → eje vertical (Z). Si tienen que ser horizontales → `corte_lagrima`.
4. Superficie estética arriba o en vertical; la cara de la cama sale lisa pero con posible pata de elefante.
5. Piezas altas y finas (alto > 5 × base): brim o rediseñar con base ancha. Mejor partir en dos y unir.

## Voladizos y puentes
- Hasta **45°** desde la vertical sin soporte. [comunidad] Más que eso → chaflán a 45° o rediseño.
- Bajo un saliente horizontal pon **chaflán de 45°** en vez de redondeo (el redondeo inferior cuelga).
- Puente (apoyado en los dos lados): hasta **10 mm** limpio. [comunidad] Más → soporte o arco/lágrima.
- Voladizo en ménsula (apoyado en un solo lado) cerca de la cama — p.ej. una espiga horizontal que sale de
  una cara a z=1,6 — **se cae**: activa "soporte solo en la cama" en el laminador, o rediseña (bájala a ras de cama,
  o imprime esa pieza en otra orientación).
- cad.py marca en rojo y lista las "zonas colgantes" con su z: un "techo plano" con apoyo a ambos lados ≤ 10 mm es
  un puente válido; si solo apoya en un lado, es un problema.

## Paredes y grosores (ancho de línea ≈ 0,42)
| Elemento | Mínimo | Recomendado |
|---|---|---|
| Pared vertical | 0,84 (2 líneas) | 1,6 (4 líneas) en piezas que trabajan |
| Suelo / techo | 0,8 (4 capas de 0,2) | 1,2–2 |
| Detalle en relieve | 0,5 de ancho | 0,8+ |
| Texto en relieve | trazo ≥ 0,5; alto ≥ 5 mm; prof 0,4–1,0 (múltiplo de capa) | negrita |
| Pasador/espiga | Ø/lado ≥ 2,5 | ≥ 4 si soporta carga |
| Clip elástico (PLA) | grosor 1,2–2 y largo ≥ 10 × grosor | PETG si se dobla a menudo |

Alturas de detalles en Z: múltiplos de la capa (0,2) → 0,4 / 0,6 / 0,8 / 1,0.

## Holguras (por lado, en mm) — punto de partida (los valores reales del usuario están en su perfil) [comunidad]
| Ajuste | Holgura/lado | Ejemplo |
|---|---|---|
| A presión (no se mueve) | 0,05–0,1 | imán, rodamiento |
| Ajustado (entra con fuerza de mano) | 0,15 | espiga/caja, pasador |
| Deslizante | 0,2–0,25 | tapa de caja, cajón |
| Holgado / giratorio | 0,3–0,4 | bisagra, eje que gira |
Agujeros verticales pequeños salen ~0,1–0,2 mm más pequeños → lib3d ya compensa los de tornillo.
Si un encaje es crítico: **haz primero una probeta** (ver abajo) en vez de la pieza entera.

## Tornillería (lib3d.TORNILLO ya trae las cotas)
- Pasante: M3 3,4 · M4 4,5 · M5 5,5. Rosca directa en plástico: M3 2,7 · M4 3,6 (solo pocas veces de montaje).
- Para montar/desmontar muchas veces → **inserto térmico** (`corte_inserto`), con ≥ 1,6 mm de pared alrededor.
- Tuerca cautiva: `corte_tuerca` desde una cara; si queda bajo un techo → puente pequeño, ok.
- Cabeza avellanada solo en caras horizontales hacia arriba (en vertical el cono cuelga).
- Tornillos a pared (taco Ø6, tornillo Ø4) → `corte_tornillo("pared4", cabeza="avellanado")` o `corte_colgador()`.

## Calidad y acabado
- Chaflán 0,4 en la base (`caja()` lo hace) → elimina la pata de elefante y los encajes entran.
- Aristas expuestas: redondeo 0,5–1 mm. Aristas que tocan otra pieza: vivas.
- Esquinas interiores con carga: redondeo ≥ 1 mm (concentran tensión).
- Superficies grandes planas arriba: el laminador hace "ironing" si se quiere acabado espejo.
- Evita paredes de 1,0–1,2 mm exactas en piezas que no trabajan: el laminador mete huecos raros; usa 0,84 o 1,6.

## Material (recomendación corta)
- **PLA**: decorativo, interior, soportes de escritorio. Se ablanda a ~55–60 °C (no coche, no sol).
- **PETG**: piezas útiles, clips, exterior suave, cocina/baño. ~75 °C. Algo menos preciso (holgura +0,05).
- **ABS/ASA**: calor y exterior (ASA aguanta UV). Necesitan impresora cerrada (mira `cerrada` en el perfil). ~95 °C.
- **PLA-CF / PETG-CF**: rígido y mate; la boquilla de serie es bimetálica (aguanta CF).
- **TPU**: flexible (fundas, topes). Holguras +0,1, sin puentes largos.

## Ajustes a recomendar al entregar (2–4 líneas, no más)
Capa: 0,2 normal · 0,12 estético/texto pequeño · 0,28 rápido. Paredes: 3 (4–5 si trabaja). Relleno: 15 % decorativo,
25–40 % funcional (más paredes > más relleno). Soportes: solo si cad.py dejó zonas colgantes sin resolver.
Brim: piezas con poco apoyo o altas y finas.

## Probetas (test-first) — antes de imprimir algo largo con un encaje crítico
Imprime solo la zona del encaje: `split()` el modelo cerca de la unión o modela un tramo corto (10–15 mm) de cada pieza.
Para no adivinar la holgura, una **escalera de holguras**: varias espigas/huecos con 0,10 / 0,15 / 0,20 / 0,25 rotulados.
Lo que funcione → `perfil-impresora.json` → "probado".
