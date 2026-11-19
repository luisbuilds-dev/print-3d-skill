# Chuleta build123d 0.13 (modo algebraico) — todo probado en esta máquina

Lee esto solo si vas a usar algo que no está en lib3d o si un modelo falla.

## Reglas que evitan el 90 % de errores
- **Modo algebraico** siempre (`a + b`, `a - b`, `a & b`). No uses `with BuildPart()`: es más largo y falla más.
- Orden de transformaciones: `Pos(x,y,z) * Rot(rx,ry,rz) * forma` → primero gira, luego mueve.
- Las primitivas (`Box`, `Cylinder`, `Sphere`, `Cone`, `Torus`) nacen **centradas en el origen**. `Pos(0,0,h/2) * Box(x,y,h)` la apoya en z=0. O `align=(Align.CENTER, Align.CENTER, Align.MIN)`.
- **Redondea/achaflana antes de restar** agujeros: las aristas son más fáciles de seleccionar.
- Los cortes deben **sobresalir** (`EPS`) de la cara que atraviesan: si coinciden exactamente quedan pieles de 0 mm.
- El texto y las extrusiones crecen hacia +Z desde el plano del sketch.
- Rutas con ñ/acentos: `export_stl` de OCC falla → `cad.py` ya exporta vía temporal ASCII. No exportes tú a mano.
- `import_stl` da una **malla sin volumen** (no vale para booleanas) → para editar STL usa `stl.py` (manifold3d).
- `sweep` por `Polyline` con esquinas: pasa `transition=Transition.RIGHT` (o `ROUND`). El valor por defecto pierde tramos. Mejor aún: `FilletPolyline(..., radius=r)`.
- Si una booleana o un fillet falla: baja el radio, comprueba que el radio < mitad del grosor, o haz el fillet sobre una pieza más simple antes de combinar.

## Perfiles 2D → sólido
```python
perfil = make_face(Polyline((0,0),(30,0),(30,5),(5,20),(0,20), close=True))   # en XY
pieza  = extrude(perfil, 10)                                                    # hacia +Z
lado   = extrude(Plane.XZ * perfil, 10)        # perfil dibujado en XZ, extruye hacia -Y (normal de XZ)
s = Rectangle(40, 20) - Circle(5)              # sketches admiten + - &
s = SlotCenterToCenter(20, 5)   ;  RegularPolygon(r, 6)  ;  Ellipse(rx, ry)  ;  Trapezoid(w, h, 60)
redondo = fillet(Rectangle(40,20).vertices(), 3)   # esquinas de un sketch
```

## Revolución, loft, barrido, hélice
```python
vaso  = revolve(Plane.XZ * make_face(Polyline((5,0),(10,0),(10,30),(8,30),(5,5), close=True)), Axis.Z)
trans = loft([Rectangle(30,30), Pos(0,0,20) * Circle(8)])            # transición cuadrado → círculo
tubo  = sweep(Plane.YZ * Circle(2), FilletPolyline((0,0,0),(30,0,0),(30,30,0), radius=5))
rosca = sweep(Plane.XZ * Pos(6,0) * RegularPolygon(0.8,3), Helix(pitch=2, height=10, radius=6), is_frenet=True)
```

## Vaciar, espejo, partir, patrones
```python
b = Box(30,30,20);  hueca = offset(b, amount=-2, openings=b.faces().sort_by(Axis.Z)[-1])
simetrica = pieza + mirror(pieza, about=Plane.YZ)
mitad = split(pieza, bisect_by=Plane.XY, keep=Keep.BOTTOM)          # Keep.TOP / Keep.BOTH
pieza -= [loc * Cylinder(2, 10) for loc in PolarLocations(14, 6)]    # 6 agujeros en círculo r=14
pieza -= [loc * Cylinder(2, 10) for loc in GridLocations(10, 10, 4, 4)]
```

## Seleccionar aristas y caras
```python
p.edges().filter_by(Axis.Z)              # aristas verticales
p.edges().group_by(Axis.Z)[-1]           # aristas de la cara más alta  ([0] = la de abajo)
p.edges().group_by(Axis.X)[-1]           # aristas del extremo +X (punta de una espiga)
p.faces().sort_by(Axis.Z)[-1]            # cara superior
p.edges().filter_by_position(Axis.Z, 0, 5)   # aristas con z entre 0 y 5
p.edges().filter_by(GeomType.CIRCLE)     # bordes de agujeros
fillet(p.edges()..., r)  /  chamfer(p.edges()..., d)
```

## Medir en el script (sale por consola en el build)
```python
bb = p.bounding_box(); bb.size.X; bb.min.Z     # caja envolvente
p.volume ; p.area ; (a & b).volume             # solape entre piezas (0 = no chocan)
a.distance_to(b)                               # separación mínima
```

## Texto
`texto("ABC", tam, prof)` de lib3d (altura de mayúscula ≈ tam). Fuentes de Windows por nombre: "Arial", "Arial Black",
"Impact", "Bahnschrift", "Consolas", "Segoe UI". Para texto en una pared vertical: `Pos(x, y_cara, z) * Rot(90,0,0) * texto(...)`
(Rot(90,0,0) lo pone en el plano XZ mirando a -Y).
