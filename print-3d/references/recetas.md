# Recetas probadas (copiar, ajustar parámetros, construir)

Cada bloque es un modelo completo para `cad.py build`. Todos pasan la validación sin avisos graves.

## Llavero con texto y anilla
```python
from lib3d import *
NOMBRE = "llavero"
TXT, L, A, G = "ANA", 50, 16, 3.0
base = caja(L, A, G, r=A / 2 - 0.01, redondeo_arriba=0.8)
base -= Pos(-L / 2 + 5, 0, G) * Cylinder(2.25, 2 * G + 1)          # agujero de anilla Ø4,5
base += Pos(3, 0, G) * texto(TXT, 7, 0.8)                            # relieve 0,8 (4 capas)
resultado = base
```

## Cartel / placa con texto grabado y colgador oculto
```python
from lib3d import *
NOMBRE = "cartel"
X, Y, G = 140, 45, 5
p = placa(X, Y, G)
p -= Pos(0, 0, G - 0.6) * texto("OFICINA", 18, 0.6 + EPS, fuente="Arial Black")
for x in (-X / 2 + 20, X / 2 - 20):                                   # colgadores en la cara de la cama
    p -= Pos(x, -4, 0) * Rot(180, 0, 0) * corte_colgador(prof=3.5, alto_cabeza=2.0)
resultado = p
```
Los techos de los ojos de cerradura salen como "techo plano": son puentes de 8,4 mm, válidos.
Si el texto es de otro color: pausa en z = G - 0.6 en el laminador y cambia el filamento.

## Soporte de pared en L (escuadra) con nervio
```python
from lib3d import *
NOMBRE = "escuadra"
ANCHO, BRAZO, ALTO, G = 25, 60, 60, 5
base = caja(BRAZO, ANCHO, G, r=2)                                    # brazo horizontal (apoyado)
pared = Pos(-BRAZO / 2 + G / 2, 0, ALTO / 2) * Box(G, ANCHO, ALTO)   # brazo vertical
nervio = extrude(Plane.XZ * make_face(Polyline((0, 0), (BRAZO - G, 0), (0, ALTO - G), close=True)), 3, both=True)
nervio = Pos(-BRAZO / 2 + G, 0, G) * nervio
p = base + pared + nervio
for z in (ALTO * 0.45, ALTO * 0.8):                                   # tornillos a pared por la cara -X
    p -= Pos(-BRAZO / 2, 0, z) * Rot(0, -90, 0) * corte_tornillo("pared4", G + 1, "allen")
for x, y in ((0, 7.5), (BRAZO / 2 - 9, -7.5)):                      # fuera del nervio (±3) con cabeza Ø7,8
    p -= Pos(x, y, G) * corte_tornillo("M4", G + 1, "allen")
resultado = p
```
Se imprime así (L tumbada sobre el brazo horizontal); el nervio es triangular → sin voladizos.
Los tornillos de la pared vertical llevan rebaje cilíndrico (su techo es un puente < 10 mm); avellanado ahí colgaría.

## Caja con tapa encajable
```python
from lib3d import *
NOMBRE = "caja"
X, Y, Z = 80, 50, 30
SALIDA = "separadas"
resultado = {"caja": caja_hueca(X, Y, Z), "tapa": tapa_para(X, Y)}
ENSAMBLE = {"caja": caja_hueca(X, Y, Z), "tapa": Pos(0, 0, Z + 1.6) * Rot(180, 0, 0) * tapa_para(X, Y)}
```

## Adaptador de tubo (revolución) Ø exterior 32 → Ø interior 20
```python
from lib3d import *
NOMBRE = "adaptador"
D1, D2, L1, L2, TR, G = 32.0, 20.0, 20, 20, 12, 2.0   # D1 encaja POR FUERA de tubo Ø32; D2 entra DENTRO de tubo Ø20
h = HOLG["ajustado"]
r1i, r1e = D1 / 2 + h, D1 / 2 + h + G                 # boca grande: tubo entra dentro
r2e, r2i = D2 / 2 - h, D2 / 2 - h - G                 # boca pequeña: entra en el tubo
perfil = Polyline((r1i, 0), (r1e, 0), (r1e, L1), (r2e, L1 + TR), (r2e, L1 + TR + L2),
                  (r2i, L1 + TR + L2), (r2i, L1 + TR), (r1i, L1), close=True)
resultado = revolve(Plane.XZ * make_face(perfil), Axis.Z)
```
La transición cónica debe ser ≤ 45° (TR ≥ diferencia de radios) para imprimir sin soportes.

## Encaje caja-espiga entre dos barras (con comprobación de montaje)
Ver `Diseños/varilla-espiga/varilla_espiga.py`. Patrón: piezas en posición de impresión en `resultado`,
las mismas en posición montada en `ENSAMBLE`, y `DETALLE` apuntando a la unión.

## Gancho (tumbado, carga en el plano de capas)
```python
from lib3d import *
NOMBRE = "gancho"
G, ANCHO = 5, 15
camino = FilletPolyline((0, 0, 0), (0, 60, 0), (25, 60, 0), (25, 45, 0), radius=8)
cuerpo = sweep(Plane.XZ * Rectangle(G, ANCHO), camino, transition=Transition.RIGHT)
placa_ = Pos(0, -5, 0) * Box(30, 10, ANCHO)
p = apoyar(cuerpo + placa_)
resultado = p
```
