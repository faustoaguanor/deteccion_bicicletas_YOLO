# Detección y Conteo de Ciclistas con YOLOv11

Sistema de visión por computadora que detecta y cuenta ciclistas en videos de intersecciones urbanas. Útil para estudios de movilidad y planificación vial.

## Demos y ejemplos

Prueba la aplicación sin instalar nada:

- **Streamlit Cloud**: https://deteccionbicicletasyolo.streamlit.app/
- **HuggingFace Spaces**: https://huggingface.co/spaces/FaustoAlejo/contador-ciclistas-yolov11
- **HuggingFace con GPU** (Gradio): https://huggingface.co/spaces/FaustoAlejo/contador-ciclistas-yolov11-gradio

Descarga videos de prueba: [Google Drive](https://drive.google.com/drive/folders/197-TlVIFMnjTCFFJ6UEXk89saz1YRV8s?usp=drive_link)

## Cómo funciona

El sistema procesa videos y cuenta cuántos ciclistas cruzan una línea virtual configurable. Genera métricas como ciclistas por minuto y por hora, además de gráficas del flujo de tráfico.

**Tecnologías:**
- YOLOv11 para detectar ciclistas en cada frame
- BoT-SORT para seguir objetos entre frames
- Línea de conteo virtual ajustable
- Visualización en tiempo real

**Modelos disponibles:**

| Modelo | Tamaño | Cuando usarlo |
|--------|--------|---------------|
| YOLOv11n | 3MB | Videos largos o computadoras lentas |
| YOLOv11s | 10MB | Cuando necesitas mayor precisión |

## Instalación local

```bash
git clone https://github.com/faustoaguanor/deteccion_bicicletas_YOLO.git
cd deteccion_bicicletas_YOLO
pip install -r requirements.txt
streamlit run app.py
```

Abre tu navegador en `http://localhost:8501`

## Deployment

### Streamlit Cloud

1. Sube tu repo a GitHub
2. Ve a https://streamlit.io/cloud y conecta tu cuenta
3. Selecciona el repositorio, rama y archivo `app.py`
4. Da click en Deploy

### HuggingFace Spaces

1. Crea una cuenta en https://huggingface.co
2. Crea un nuevo Space (tipo Streamlit)
3. Clona y sube el código:

```bash
git clone https://huggingface.co/spaces/tu-usuario/nombre-space
cd nombre-space
# copia los archivos del proyecto aquí
git add .
git commit -m "Initial commit"
git push
```

El deploy se hace automáticamente.

## Archivos del proyecto

```
├── app.py               # Aplicación Streamlit
├── requirements.txt     # Librerías necesarias
├── yolo11n.pt          # Modelo nano (rápido)
├── yolo11s.pt          # Modelo small (preciso)
└── README.md
```

## Detalles técnicos

- Los videos se convierten a H.264 para funcionar en cualquier navegador
- BoT-SORT combina detección con re-identificación de objetos
- Solo se cuentan detecciones con confianza mayor al 25%
- La línea de conteo se puede mover arrastrándola en la interfaz

---

**Desarrollado por:** Fausto Guano
**Institución:** Universidad Yachay Tech

Proyecto de análisis de movilidad ciclística urbana
