"""
Sistema de Conteo Automático de Ciclistas
Aplicación Streamlit para detección y conteo con YOLOv11
Autor: Alejandro Aguanor - Universidad Yachay Tech
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
import time
from detector import CyclistDetector
from utils import (
    create_metrics_dashboard,
    create_direction_chart,
    create_flow_gauge,
    create_comparison_chart,
    generate_recommendations,
    display_technical_details,
    create_summary_dataframe
)

# Configuración de la página
st.set_page_config(
    page_title="Contador Automático de Ciclistas",
    page_icon="🚴‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    h1 {
        color: #1f77b4;
        padding-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    """Función principal de la aplicación"""
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🚴‍♂️ Sistema de Conteo Automático de Ciclistas")
        st.markdown("""
        Sistema de Computer Vision para análisis de flujo ciclista en intersecciones urbanas.
        Utiliza **YOLOv11** con tracking multi-objeto para conteo preciso y métricas en tiempo real.
        """)
    
    with col2:
        st.image("https://img.shields.io/badge/YOLOv11-Ultralytics-blue", use_container_width=True)
        st.image("https://img.shields.io/badge/Tracking-BoT--SORT-green", use_container_width=True)
    
    # Sidebar - Configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Selección de modelo
        model_size = st.radio(
            "Modelo YOLOv11:",
            options=["n", "s"],
            format_func=lambda x: {
                "n": "🚀 Nano (rápido, ~3MB)",
                "s": "🎯 Small (preciso, ~10MB)"
            }[x],
            help="Nano es más rápido, Small es más preciso"
        )
        
        # Umbral de confianza
        confidence = st.slider(
            "Confianza mínima:",
            min_value=0.1,
            max_value=0.9,
            value=0.15,
            step=0.05,
            help="Umbral de confianza para detecciones (0.1-0.9). Valores bajos detectan más objetos."
        )
        
        # Orientación de línea de conteo
        line_orientation = st.radio(
            "Orientación de línea:",
            options=["horizontal", "vertical", "both"],
            format_func=lambda x: {
                "horizontal": "↔️ Horizontal",
                "vertical": "↕️ Vertical",
                "both": "✖️ Ambas"
            }[x],
            help="Selecciona la orientación de la(s) línea(s) de conteo"
        )

        # Posición de línea horizontal
        if line_orientation in ["horizontal", "both"]:
            line_position = st.slider(
                "Posición línea horizontal:",
                min_value=0.3,
                max_value=0.7,
                value=0.5,
                step=0.05,
                help="Posición vertical de la línea horizontal (fracción de altura)"
            )
        else:
            line_position = 0.5

        # Posición de línea vertical
        if line_orientation in ["vertical", "both"]:
            line_position_x = st.slider(
                "Posición línea vertical:",
                min_value=0.3,
                max_value=0.7,
                value=0.5,
                step=0.05,
                help="Posición horizontal de la línea vertical (fracción de ancho)"
            )
        else:
            line_position_x = 0.5

        # Frame skip para velocidad
        process_every_n = st.selectbox(
            "Procesar cada N frames:",
            options=[1, 2, 3],
            index=0,
            help="Mayor = más rápido pero menos preciso"
        )
        
        # Opción para detectar personas (experimental)
        st.markdown("---")
        st.markdown("**Opciones Avanzadas:**")
        
        detect_persons = st.checkbox(
            "Detectar personas además de bicicletas",
            value=False,
            help="⚠️ EXPERIMENTAL: Puede causar falsos positivos (peatones, gente esperando, etc.). Solo habilitar si es necesario."
        )
        
        if detect_persons:
            st.warning("⚠️ Detección de personas habilitada. Puede contar peatones como ciclistas.")
        
        st.markdown("---")
        
        # Información del proyecto
        with st.expander("ℹ️ Sobre el Proyecto"):
            st.markdown("""
            **Desarrollado por:**  
            Alejandro Aguanor
            
            **Universidad:**  
            Yachay Tech
            
            **Módulo:**  
            Fundamentos de IA
            
            **Tecnologías:**
            - YOLOv11 (Ultralytics)
            - BoT-SORT Tracking
            - OpenCV
            - Streamlit
            """)
        
        # Links útiles
        st.markdown("---")
        st.markdown("### 🔗 Links")
        st.markdown("[💻 GitHub](https://github.com/faustoaguanor)")
    
    # Main content
    st.markdown("---")
    
    # Tabs principales
    tab1, tab2, tab3 = st.tabs([
        "📹 Análisis de Video",
        "📊 Casos de Ejemplo",
        "📖 Guía de Uso"
    ])
    
    with tab1:
        st.header("Cargar y Analizar Video")
        
        # Upload de video
        uploaded_file = st.file_uploader(
            "Selecciona un video (MP4, AVI, MOV)",
            type=["mp4", "avi", "mov"],
            help="Recomendado: videos cortos (30 seg - 2 min) para mejor rendimiento"
        )
        
        if uploaded_file is not None:
            # Mostrar información del archivo
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.info(f"📁 Archivo: {uploaded_file.name} | Tamaño: {file_size_mb:.2f} MB")
            
            # Advertencia para archivos grandes
            if file_size_mb > 50:
                st.warning("⚠️ Archivo grande detectado. El procesamiento puede tomar varios minutos.")
            
            # Botón de procesamiento
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                process_button = st.button(
                    "🚀 Iniciar Análisis",
                    type="primary",
                    use_container_width=True
                )
            
            if process_button:
                process_video(
                    uploaded_file,
                    model_size,
                    confidence,
                    line_position,
                    line_position_x,
                    line_orientation,
                    process_every_n,
                    detect_persons
                )
        else:
            # Mostrar instrucciones
            st.info("""
            👆 **Instrucciones:**
            1. Carga un video de una intersección o calle
            2. Ajusta la configuración en el panel lateral
            3. Presiona "Iniciar Análisis"
            4. Revisa las métricas y visualizaciones
            """)
            
            # Mostrar video de ejemplo
            st.markdown("### 🎬 Ejemplo de Resultado")
            st.markdown("""
            El sistema detecta ciclistas, les asigna un ID único, los rastrea a través 
            de los frames y cuenta cuántos cruzan una línea virtual de conteo.
            """)
    
    with tab2:
        st.header("📊 Casos de Uso - Quito, Ecuador")
        
        st.markdown("""
        ### Escenarios Típicos de Análisis:
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🟢 Ciclovías Existentes**
            - Av. Naciones Unidas
            - Av. Simón Bolívar
            - Parque La Carolina
            
            **Objetivo:** Medir utilización y justificar ampliación
            """)
            
            st.markdown("""
            **🟡 Intersecciones Sin Infraestructura**
            - Zona Norte: La Gasca, González Suárez
            - Zona Centro: 10 de Agosto, 6 de Diciembre
            
            **Objetivo:** Evaluar necesidad de nueva ciclovía
            """)
        
        with col2:
            st.markdown("""
            **Métricas de Referencia:**
            
            | Flujo/Hora | Recomendación |
            |------------|---------------|
            | < 50 | Señalización compartida |
            | 50-150 | Carril compartido |
            | > 150 | Ciclovía segregada |
            """)
            
            st.info("""
            💡 **Tip:** Para análisis completo, recolectar datos en:
            - Horas pico (7-9 AM, 5-7 PM)
            - Horas valle (10 AM - 4 PM)
            - Fines de semana
            """)
    
    with tab3:
        st.header("📖 Guía de Uso")

        with st.expander("🎯 ¿Cómo funcionan las líneas de detección?", expanded=True):
            st.markdown("""
            **Concepto básico:**

            El sistema dibuja una línea virtual en el video y cuenta cada ciclista **solo cuando cruza** esa línea.
            Cada ciclista se cuenta **una sola vez** gracias al tracking de IDs únicos.

            ---

            **📐 Tipos de líneas:**

            **1. Línea Horizontal** (↔️)
            ```
            ┌─────────────────────┐
            │                     │
            │        ↓ 🚴         │  ← Ciclista moviéndose hacia abajo
            │═══════════════════  │  ← LÍNEA HORIZONTAL (amarilla)
            │        🚴 ↑         │  ← Ciclista moviéndose hacia arriba
            │                     │
            └─────────────────────┘
            ```
            - **Detecta:** Flujo vertical (arriba ↑ / abajo ↓)
            - **Uso ideal:** Calles horizontales, intersecciones este-oeste
            - **Posición:** Ajustable de 30% a 70% de la altura

            **2. Línea Vertical** (↕️)
            ```
            ┌──────────║─────────┐
            │          ║         │
            │  → 🚴   ║   🚴 ←  │
            │          ║         │
            │          ║         │
            │    LÍNEA VERTICAL  │
            │    (magenta)       │
            └──────────║─────────┘
            ```
            - **Detecta:** Flujo horizontal (izquierda ← / derecha →)
            - **Uso ideal:** Calles verticales, intersecciones norte-sur
            - **Posición:** Ajustable de 30% a 70% del ancho

            **3. Ambas Líneas** (✖️)
            ```
            ┌──────────║─────────┐
            │    ↑ 🚴  ║  🚴 ↓   │
            │═══════════════════  │ ← Línea horizontal
            │    → 🚴  ║  🚴 ←   │
            │          ║         │
            └──────────║─────────┘
                       ↑
                  Línea vertical
            ```
            - **Detecta:** Flujo en ambas direcciones simultáneamente
            - **Uso ideal:** Intersecciones complejas, rotondas
            - **Conteo:** IDs únicos (un ciclista no se cuenta dos veces)

            ---

            **💡 Consejos para colocar las líneas:**

            1. **Centro del flujo:** Coloca la línea donde pasan la mayoría de ciclistas
            2. **Evitar bordes:** No coloques en los extremos (30%-70% recomendado)
            3. **Zona de cruce claro:** Asegúrate que los ciclistas crucen completamente la línea
            4. **Probar diferentes posiciones:** Si no detecta bien, ajusta la posición en el panel lateral

            ---

            **📊 Ejemplo de conteo:**

            Si un ciclista con ID #5 se mueve así:
            ```
            Frame 1:  🚴 (arriba de línea)
            Frame 2:  🚴 (cruza línea) ← ✅ SE CUENTA AQUÍ
            Frame 3:  🚴 (abajo de línea)
            Frame 4:  🚴 (sigue abajo) ← NO se cuenta otra vez
            ```

            **Resultado:** ID #5 = 1 ciclista contado (dirección: abajo ↓)
            """)

        with st.expander("🎥 ¿Cómo grabar un buen video?"):
            st.markdown("""
            **Recomendaciones para captura:**
            
            1. **Posición de cámara:**
               - Vista elevada (poste, edificio)
               - Ángulo perpendicular a la vía
               - Altura mínima: 3-4 metros
            
            2. **Condiciones de grabación:**
               - Buena iluminación (evitar contraluz)
               - Cámara estática (sin movimiento)
               - Resolución mínima: 720p
            
            3. **Duración:**
               - Mínimo: 30 segundos
               - Óptimo: 1-2 minutos
               - Máximo recomendado: 5 minutos
            
            4. **Formato:**
               - MP4 (H.264)
               - 30 FPS o superior
            """)
        
        with st.expander("🔧 ¿Cómo interpretar las métricas?"):
            st.markdown("""
            **Métricas clave:**
            
            - **Total Ciclistas:** Conteo único (sin duplicados)
            - **Ciclistas/Minuto:** Flujo instantáneo durante el video
            - **Ciclistas/Hora:** Proyección basada en flujo medido
            - **Direccionalidad:** Distribución arriba/abajo
            
            **Interpretación de flujo/hora:**
            - 0-50: Bajo (no justifica infraestructura dedicada)
            - 50-150: Medio (considerar carril compartido)
            - 150+: Alto (priorizar ciclovía segregada)
            """)
        
        with st.expander("⚙️ ¿Qué configuración usar?"):
            st.markdown("""
            **Modelo:**
            - **YOLOv11n (Nano):** Para videos largos o procesamiento rápido
            - **YOLOv11s (Small):** Para máxima precisión
            
            **Confianza:**
            - 0.15-0.25: Más detecciones (puede incluir falsos positivos)
            - 0.25-0.35: Balance (recomendado)
            - 0.35-0.50: Menos detecciones (más conservador)
            
            **Línea de conteo:**
            - 0.5: Centro del frame (recomendado)
            - Ajustar según zona de interés en el video
            """)
        
        with st.expander("❓ Solución de problemas"):
            st.markdown("""
            **Problemas comunes:**
            
            1. **"No detecta ciclistas"**
               - ✅ Reducir umbral de confianza
               - ✅ Verificar que los ciclistas sean visibles
               - ✅ Asegurar buena iluminación
            
            2. **"Conteo incorrecto"**
               - ✅ Ajustar posición de línea de conteo
               - ✅ Verificar que ciclistas crucen la línea completamente
               - ✅ Usar modelo Small para mayor precisión
            
            3. **"Procesamiento muy lento"**
               - ✅ Usar modelo Nano
               - ✅ Aumentar "Procesar cada N frames"
               - ✅ Reducir duración del video
            """)


def process_video(uploaded_file, model_size, confidence, line_position, line_position_x, line_orientation, process_every_n, detect_persons):
    """
    Procesa el video subido y muestra resultados

    Args:
        uploaded_file: Archivo de video subido
        model_size: Tamaño del modelo ('n' o 's')
        confidence: Umbral de confianza
        line_position: Posición de línea de conteo horizontal
        line_position_x: Posición de línea de conteo vertical
        line_orientation: Orientación de línea ('horizontal', 'vertical', 'both')
        process_every_n: Procesar cada N frames
        detect_persons: Si True, detecta personas además de bicicletas
    """
    
    # Guardar archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        tmp_file.write(uploaded_file.read())
        video_path = tmp_file.name
    
    try:
        # Inicializar detector
        with st.spinner(f"🔧 Inicializando YOLOv11{model_size}..."):
            detector = CyclistDetector(
                model_size=model_size,
                conf_threshold=confidence,
                detect_persons=detect_persons
            )
        
        st.success(f"✅ Modelo YOLOv11{model_size} cargado")
        
        # Crear contenedores para progreso y logs
        progress_container = st.container()
        log_container = st.expander("📋 Logs de procesamiento (ver detalles)", expanded=False)
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Lista para capturar logs
        import io
        import sys
        log_capture = io.StringIO()
        
        # Función callback para actualizar progreso
        def update_progress(percent, message):
            progress_bar.progress(percent)
            status_text.text(message)
        
        status_text.text("🎬 Procesando video...")
        start_time = time.time()
        
        # Capturar logs
        old_stdout = sys.stdout
        sys.stdout = log_capture
        
        # Detectar y contar
        output_path, metrics = detector.detect_and_track(
            video_path=video_path,
            line_position=line_position,
            line_position_x=line_position_x,
            line_orientation=line_orientation,
            process_every_n_frames=process_every_n,
            progress_callback=update_progress
        )
        
        # Restaurar stdout
        sys.stdout = old_stdout
        
        # Mostrar logs capturados
        log_output = log_capture.getvalue()
        if log_output:
            with log_container:
                st.code(log_output, language="log")
        
        progress_bar.progress(100)
        processing_time = time.time() - start_time
        status_text.text(f"✅ Procesamiento completado en {processing_time:.1f} segundos")
        
        # Mostrar resultados
        st.success("🎉 ¡Análisis completado exitosamente!")
        
        # Alerta si no se detectaron ciclistas
        if metrics['total_cyclists'] == 0:
            st.error("⚠️ NO SE DETECTARON CICLISTAS en este video")
            st.warning(f"""
            **Posibles causas y soluciones:**
            
            1. **Umbral de confianza muy alto** (actual: {confidence:.2f})
               - 💡 Prueba reducir a 0.10 - 0.12 en el panel lateral
            
            2. **Ciclistas muy pequeños o lejanos en el video**
               - 💡 Usa un video con ciclistas más cercanos a la cámara
               - 💡 Cambia al modelo Small (más preciso) en vez de Nano
            
            3. **Iluminación o calidad del video**
               - 💡 Verifica que el video tenga buena iluminación
               - 💡 Asegúrate de que las bicicletas sean claramente visibles
            
            4. **YOLO detecta personas pero no bicicletas**
               - 💡 Habilita "Detectar personas" en Opciones Avanzadas (experimental)
               - ⚠️ Advertencia: puede causar falsos positivos con peatones
            
            5. **Los objetos no son reconocidos como bicicletas**
               - 💡 YOLO busca la forma típica de una bicicleta
               - 💡 Verifica el video procesado para ver qué detectó (si algo)
            
            **Revisa los logs de procesamiento arriba para más detalles.** 👆
            """)
        
        st.markdown("---")
        
        # Dashboard de métricas
        create_metrics_dashboard(metrics)
        
        st.markdown("---")
        
        # Videos lado a lado
        st.markdown("### 🎬 Videos Comparativos")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Video Original**")
            st.video(video_path)
        
        with col2:
            st.markdown("**Video con Detecciones**")
            if os.path.exists(output_path):
                # Verificar tamaño del archivo
                file_size = os.path.getsize(output_path)
                if file_size > 0:
                    try:
                        # Leer el video como bytes para mejor compatibilidad con Streamlit
                        with open(output_path, 'rb') as video_file:
                            video_bytes = video_file.read()
                            st.video(video_bytes)
                        st.caption(f"Tamaño: {file_size / (1024*1024):.2f} MB")
                    except Exception as e:
                        st.warning(f"⚠️ No se pudo mostrar el video en el navegador: {e}")
                        st.info("📥 Puedes descargar el video procesado más abajo en 'Exportar Resultados'")
                else:
                    st.error("El video procesado está vacío")
            else:
                st.error("No se pudo generar el video procesado")
        
        st.markdown("---")
        
        # Visualizaciones
        st.markdown("### 📊 Análisis Visual")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_direction = create_direction_chart(metrics)
            st.plotly_chart(fig_direction, use_container_width=True)
        
        with col2:
            fig_comparison = create_comparison_chart(metrics)
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Gauge de flujo
        st.markdown("### 🎯 Indicador de Flujo")
        fig_gauge = create_flow_gauge(metrics)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        st.markdown("---")
        
        # Recomendaciones
        recommendations = generate_recommendations(metrics)
        st.markdown(recommendations)
        
        st.markdown("---")
        
        # Detalles técnicos
        display_technical_details(metrics)
        
        # Exportar resultados
        st.markdown("---")
        st.markdown("### 💾 Exportar Resultados")
        
        df_summary = create_summary_dataframe(metrics)
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df_summary.to_csv(index=False)
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"analisis_ciclistas_{int(time.time())}.csv",
                mime="text/csv"
            )
        
        with col2:
            if os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    st.download_button(
                        label="📥 Descargar Video Procesado",
                        data=f,
                        file_name=f"video_procesado_{int(time.time())}.mp4",
                        mime="video/mp4"
                    )
        
    except Exception as e:
        st.error(f"❌ Error durante el procesamiento: {str(e)}")
        st.exception(e)
    
    finally:
        # Limpiar archivos temporales
        try:
            if os.path.exists(video_path):
                os.unlink(video_path)
            if 'output_path' in locals() and os.path.exists(output_path):
                # No eliminar el output inmediatamente para permitir descarga
                pass
        except Exception as e:
            st.warning(f"No se pudo limpiar archivos temporales: {e}")


# Ejecutar app
if __name__ == "__main__":
    main()
