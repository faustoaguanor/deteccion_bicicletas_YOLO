# 🚴‍♂️ Sistema de Conteo Automático de Ciclistas

## Descripción
Aplicación de Computer Vision para conteo automático de ciclistas en intersecciones urbanas usando YOLOv11 y tracking.

## Características
- Detección de ciclistas con YOLOv11 (nano o small)
- Tracking multi-objeto con BoT-SORT
- Conteo bidireccional con línea virtual
- Métricas en tiempo real (ciclistas/minuto, ciclistas/hora)
- Visualizaciones interactivas

## Modelos Disponibles
- **YOLOv11n** (nano): ~3MB, más rápido, 80-85% precisión
- **YOLOv11s** (small): ~10MB, más preciso, 85-90% precisión

## Deployment

### HuggingFace Spaces (Primario)
1. Crear cuenta en https://huggingface.co
2. Crear nuevo Space: Settings → Spaces → Create new Space
3. Seleccionar: Streamlit + Public
4. Push código a HF repo

### Streamlit Community Cloud (Backup)
1. Push a GitHub
2. https://streamlit.io/cloud
3. Deploy desde GitHub repo

## Uso Local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Autor
Alejandro Aguanor - Universidad Yachay Tech
