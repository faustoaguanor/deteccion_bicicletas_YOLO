# Detección y Conteo de Ciclistas con YOLOv11

Sistema de visión por computadora para contar ciclistas en intersecciones urbanas. Utiliza YOLOv11 para la detección y algoritmos de tracking para el seguimiento de objetos.

## Demo en línea

Puedes probar la aplicación directamente en:
- **Streamlit Cloud**: https://deteccionbicicletasyolo.streamlit.app/
- **HuggingFace Spaces**: https://huggingface.co/spaces/FaustoAlejo/contador-ciclistas-yolov11

## ¿Qué hace?

El sistema detecta ciclistas en video y cuenta cuántos cruzan una línea virtual. Calcula métricas como ciclistas por minuto y por hora, útil para estudios de movilidad urbana o planificación vial.

**Funcionalidades principales:**
- Detección de ciclistas usando YOLOv11
- Seguimiento de objetos con BoT-SORT
- Conteo bidireccional (configurable con línea virtual)
- Métricas en tiempo real
- Gráficas de flujo de ciclistas

## Modelos

Se incluyen dos versiones de YOLOv11:

| Modelo | Tamaño | Ventaja |
|--------|--------|---------|
| YOLOv11n | ~3MB | Más rápido, ideal para videos largos o hardware limitado |
| YOLOv11s | ~10MB | Mayor precisión en detecciones |

Puedes cambiar entre modelos desde la interfaz de Streamlit.

## Instalación y uso local

Clonar el repositorio:
```bash
git clone https://github.com/faustoaguanor/deteccion_bicicletas_YOLO.git
cd deteccion_bicicletas_YOLO
```

Instalar dependencias:
```bash
pip install -r requirements.txt
```

Ejecutar la aplicación:
```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

## Deploy en la nube

### Streamlit Community Cloud

1. Haz push de tu repositorio a GitHub
2. Ve a https://streamlit.io/cloud
3. Conecta tu cuenta de GitHub
4. Selecciona el repositorio y la rama
5. El archivo principal debe ser `app.py`
6. Click en "Deploy"

### HuggingFace Spaces

1. Crea una cuenta en https://huggingface.co
2. Ve a tu perfil → Spaces → "Create new Space"
3. Selecciona "Streamlit" como SDK
4. Configura como público o privado
5. Clona el repo de HF y push tu código:
```bash
git clone https://huggingface.co/spaces/<tu-usuario>/<nombre-space>
cd <nombre-space>
# copia archivos del proyecto
git add .
git commit -m "Initial commit"
git push
```

El Space se construirá automáticamente.

## Estructura del proyecto

```
├── app.py                  # Aplicación principal de Streamlit
├── requirements.txt        # Dependencias Python
├── yolo11n.pt             # Modelo YOLOv11 nano
├── yolo11s.pt             # Modelo YOLOv11 small
└── README.md
```

## Notas técnicas

- Los videos procesados se convierten a H.264 para compatibilidad con navegadores
- El tracking usa BoT-SORT que combina detección y re-identificación
- La línea de conteo se puede ajustar arrastrándola en la interfaz
- Las detecciones solo cuentan objetos con confianza > 0.25

## Autor

Fausto Guano
Universidad Yachay Tech

---

Proyecto desarrollado para análisis de movilidad ciclística urbana.
