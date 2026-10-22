# Escudo Solar · Modelo 3D interactivo para web

Escudo de fantasía medieval con tres materiales PBR: **madera, acero y bronce**. La página utiliza **Google model-viewer 4.4.0** para explorar y modificar la apariencia del modelo en tiempo real.

Web estática, sin compilación, servidor de aplicación ni claves de acceso. Todos los archivos del visor, modelo y texturas se alojan en este repositorio.

## Publicar con GitHub Pages

1. Abre [Settings → Pages](https://github.com/NessXx18/Proyecto-personal-Modelo-3D-interactivo-para-web-escudo/settings/pages).
2. En **Build and deployment → Source**, selecciona **Deploy from a branch**.
3. En **Branch**, selecciona **main** y **/ (root)**.
4. Pulsa **Save**.
5. Espera a que el despliegue termine. Puedes revisar su estado en la pestaña **Actions** o en **Settings → Pages**.

La dirección prevista después de activar Pages es:

**https://nessxx18.github.io/Proyecto-personal-Modelo-3D-interactivo-para-web-escudo/**

El archivo `.nojekyll` permite servir los archivos estáticos directamente. Las rutas de recursos son relativas para funcionar bajo el nombre del repositorio. Los cambios que subas a `main` se publicarán automáticamente después de activar Pages.

Referencia oficial: [Configurar el origen de publicación de GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Probar localmente

Con Python instalado, ejecuta desde la raíz del repositorio:

```sh
python -m http.server 8000
```

Abre **http://localhost:8000**. Usa un navegador con WebGL. La versión de archivos separados necesita HTTP/HTTPS; abrir `index.html` con `file://` puede bloquear la carga del GLB.

## Interacciones

- Girar con ratón o toque y acercar con rueda o pellizco.
- Vistas Frente, Reverso y Detalle.
- Tres tintes y un selector de color para cada material.
- Acabados Forjado, Pulido y Mate para modificar la rugosidad metálica.
- Exposición de la luz, giro automático, pantalla completa y restauración.
- Descarga del GLB original. Los cambios de apariencia del visor son temporales y no se guardan en el archivo descargado.

## Modelo y texturas

| Propiedad | Valor |
|---|---:|
| Triángulos | 5.532 |
| Materiales / primitivas | 3 / 3 |
| Texturas | 512 × 512 px |
| Tamaño del GLB | 1.837.588 bytes ≈ 1,75 MiB |
| Dimensiones | 0,926 × 0,926 × 0,317 m |

Cada material tiene Base Color, Roughness, Metallic y Normal. El GLB incrusta Base Color, Normal y un mapa combinado MetallicRoughness por material: canal G = rugosidad, canal B = metalicidad. Los mapas separados y los diagramas UV están en `texturas/`.

El GLB contiene UVs, normales, tangentes e imágenes. El informe de [validación glTF](docs/validacion-glb.json) registra **0 errores y 0 advertencias**.

El modelado y las texturas son procedurales; los normales se derivan de campos de altura. No se realizó un bake de una malla de alta resolución. El archivo GLB puede importarse en Blender; no se incluye un archivo `.blend`.

## Estructura

```text
index.html                  Página principal
style.css                   Estilos adaptables
app.js                      Controles y API de materiales
.nojekyll                   Publicación estática en GitHub Pages
assets/escudo-solar.glb      Modelo con texturas incrustadas
assets/datos-modelo.json     Estadísticas reales
texturas/                   Mapas PBR y diagramas UV
vendor/                     model-viewer y su licencia
scripts/generar_escudo.py    Fuente del modelo y de las texturas
docs/validacion-glb.json     Informe del validador de Khronos
```

## Regenerar modelo y texturas

```sh
python -m pip install -r requirements.txt
python scripts/generar_escudo.py
```

El script actualiza `assets/escudo-solar.glb`, `assets/datos-modelo.json` y `texturas/`. No requiere Blender ni Substance Painter. Si modificas su geometría o texturas, vuelve a validar el GLB y revisa la web antes de publicarlo.

## Créditos

Geometría y texturas creadas específicamente para este proyecto. Google model-viewer se distribuye bajo Apache 2.0; la licencia original está en [vendor/LICENSE-model-viewer.txt](vendor/LICENSE-model-viewer.txt).

- [Documentación de model-viewer](https://modelviewer.dev/)
- [API de materiales](https://modelviewer.dev/examples/scenegraph/)
- [glTF Validator](https://github.com/KhronosGroup/glTF-Validator)
