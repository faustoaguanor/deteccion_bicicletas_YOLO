# 🚴 Detección y Conteo de Ciclistas con YOLOv11

Aplicación web de visión por computadora que **detecta, rastrea y cuenta ciclistas** en videos de intersecciones urbanas. Calcula el flujo (ciclistas por minuto y por hora proyectado), la direccionalidad y genera recomendaciones orientadas a la planificación de movilidad.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![YOLOv11](https://img.shields.io/badge/YOLOv11-Ultralytics-blue)
![Tracking](https://img.shields.io/badge/Tracking-BoT--SORT-green)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Demo

🔗 **https://deteccionbicicletasyolo.streamlit.app/**

Para probarla sin instalar nada, pega este enlace de ejemplo en el campo de enlace de video de la app:
`https://www.youtube.com/shorts/eKJVww2YbEU`

## Características

- Detección de bicicletas con **YOLOv11** (clase `bicycle` de COCO) y seguimiento multi-objeto con **BoT-SORT**.
- Línea de conteo **horizontal**, **vertical** o **ambas**, con posición ajustable (30 %–70 % del frame).
- Cada ciclista se cuenta **una sola vez** gracias a su ID de seguimiento, con la dirección de cruce (↑ ↓ ← →).
- **Entrada de video flexible**: sube un archivo (MP4, AVI, MOV) o pega un enlace de YouTube / Shorts (se descarga en máx. 720p, hasta 10 min y 100 MB).
- Métricas: total, ciclistas/minuto, proyección por hora, duración y FPS.
- Gráficas (Plotly), recomendaciones de planificación y exportación de resultados (CSV y video anotado).
- Opción experimental para detectar también personas (puede generar falsos positivos con peatones).

### Modelos

| Modelo | Tamaño aprox. | Cuándo usarlo |
|--------|---------------|---------------|
| YOLOv11n (nano) | ~5 MB | Videos largos o equipos con poca capacidad |
| YOLOv11s (small) | ~19 MB | Cuando se necesita mayor precisión |

Los pesos se descargan automáticamente en la primera ejecución.

## Instalación local

Requisitos: Python 3.10 o superior y [FFmpeg](https://ffmpeg.org/) instalado (se usa para convertir el video procesado a H.264 y que se reproduzca en el navegador; si no está disponible, la app funciona pero el video podría no reproducirse).

```bash
git clone https://github.com/faustoaguanor/deteccion_bicicletas_YOLO.git
cd deteccion_bicicletas_YOLO

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

Abre `http://localhost:8501` en el navegador.

> Para instalar PyTorch solo-CPU (más liviano):
> `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`

## Uso

1. Sube un video (MP4, AVI o MOV) **o pega un enlace** como `https://www.youtube.com/shorts/eKJVww2YbEU`. Idealmente de 30 s a 2 min, con cámara fija y vista elevada.
2. Elige el modelo, el umbral de confianza y la orientación y posición de la línea en el panel lateral.
3. Pulsa **Iniciar Análisis** (o **Descargar y Analizar** si usas un enlace).
4. Revisa las métricas, el video anotado, las gráficas y las recomendaciones; descarga el CSV o el video.

| Parámetro | Valor por defecto | Notas |
|-----------|-------------------|-------|
| Confianza mínima | 0.15 | Valores bajos detectan más (y pueden añadir falsos positivos) |
| Orientación de línea | Horizontal | Horizontal, vertical o ambas |
| Posición de línea | 0.5 | Fracción de la altura / ancho del frame |
| Procesar cada N frames | 1 | Mayor valor = más rápido, menos preciso |

## Despliegue

**Streamlit Cloud:** sube el repositorio a GitHub, conéctalo en [streamlit.io/cloud](https://streamlit.io/cloud) y selecciona `app.py`. El archivo `packages.txt` instala las dependencias del sistema (FFmpeg, libGL).

## Estructura del proyecto

```
├── app.py               # Interfaz Streamlit
├── detector.py          # Detección, tracking, conteo y conversión de video a H.264
├── utils.py             # Métricas, gráficas y recomendaciones
├── video_source.py      # Descarga de videos desde enlaces (yt-dlp)
├── requirements.txt     # Dependencias de Python
├── packages.txt         # Dependencias del sistema (Streamlit Cloud)
├── .streamlit/config.toml
└── LICENSE
```

## Detalles técnicos

- Un ciclista se cuenta cuando el centro de su caja delimitadora **cruza** la línea entre dos frames consecutivos procesados.
- En modo "ambas líneas", el total usa IDs únicos para no contar dos veces al mismo ciclista.
- El video anotado se escribe con OpenCV (`mp4v`) y luego se convierte a H.264 con FFmpeg para su reproducción web.
- La proyección por hora extrapola el flujo medido en el video; úsala como referencia, no como aforo definitivo.

## Limitaciones

- La descarga por enlace depende de yt-dlp y de que el servidor permita acceder al sitio de origen; si falla (p. ej. YouTube bloquea la IP del servidor), descarga el video y súbelo como archivo.
- Descarga solo contenido que tengas derecho a usar y respeta los términos del sitio de origen.
- La precisión depende de la calidad del video, la iluminación, la distancia a la cámara y las oclusiones.
- Los cambios de ID del tracker pueden provocar conteos duplicados o perdidos.
- Se recomienda validar los resultados contra un conteo manual antes de usarlos en decisiones de planificación.

## Licencia

Distribuido bajo licencia [MIT](LICENSE).

## Autor

**Fausto Guano** — Universidad Yachay Tech
Proyecto de análisis de movilidad ciclística urbana.
