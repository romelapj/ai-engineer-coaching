# Portadas

Aquí van las imágenes de las piezas de la biblioteca. Una por pieza, referenciada
desde `catalogo.yaml` con `portada: portadas/<archivo>.jpg`.

## No se enlazan desde fuera

La imagen se **descarga una vez y se versiona**, nunca se apunta al servidor de
otro. Es la misma regla que ya rige los talleres —lo que se muestra es lo que
hay— aplicada a las imágenes: un `<img>` a un dominio ajeno convierte la página
en algo que se rompe solo, sin que nadie toque nada, el día que ese dominio
cambie de estructura. Y de paso el sitio deja de contarle a terceros quién lo
está leyendo.

## Cómo bajarlas

**Libros**, por ISBN, desde Open Library:

```bash
curl -L -o biblioteca/portadas/<slug>.jpg \
  "https://covers.openlibrary.org/b/isbn/9781098166304-L.jpg"
```

Si devuelve una imagen de 1x1 píxel, ese ISBN no tiene portada: no pasa nada,
se deja sin `portada` y la ficha compone la tipográfica.

**Artículos**, desde su `og:image`:

```bash
curl -sL "<url del artículo>" \
  | grep -o '<meta[^>]*og:image[^>]*>' | head -1
```

y luego se descarga esa URL igual que arriba.

## Cuando no hay imagen decente

**No se pone nada.** Se deja el campo `portada` fuera y `build.py` compone una
portada tipográfica con el título y la fuente sobre el degradado de la marca.

Es a propósito: la mitad de los artículos no tienen más imagen que un banner
genérico de su blog, y una foto de archivo de un robot mirando al horizonte no
dice nada de la pieza. La tipográfica sí: se lee el título.

## Formato

- JPG o PNG, el lado largo ~800px basta (las tarjetas se ven a 260px).
- El nombre del archivo, el mismo slug que la pieza en `catalogo.yaml`.
