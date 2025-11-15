"""
Funciones auxiliares para visualización y análisis
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict
import streamlit as st


def create_metrics_dashboard(metrics: Dict) -> None:
    """
    Crea dashboard de métricas con Streamlit
    
    Args:
        metrics: Diccionario con métricas calculadas
    """
    st.markdown("### 📊 Métricas del Análisis")
    
    # Métricas principales en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🚴 Total Ciclistas",
            value=metrics['total_cyclists']
        )
    
    with col2:
        st.metric(
            label="📈 Ciclistas/Minuto",
            value=f"{metrics['cyclists_per_minute']:.2f}"
        )
    
    with col3:
        st.metric(
            label="⏱️ Duración Video",
            value=f"{metrics['duration_minutes']:.1f} min"
        )
    
    with col4:
        st.metric(
            label="🎯 Modelo",
            value=metrics['model_used']
        )
    
    # Segunda fila de métricas
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric(
            label="↑ Hacia Arriba",
            value=metrics['cyclists_up']
        )
    
    with col6:
        st.metric(
            label="↓ Hacia Abajo", 
            value=metrics['cyclists_down']
        )
    
    with col7:
        st.metric(
            label="📊 Proyección/Hora",
            value=f"{metrics['cyclists_per_hour']:.0f}"
        )
    
    with col8:
        st.metric(
            label="🎬 FPS",
            value=metrics['fps']
        )


def create_direction_chart(metrics: Dict) -> go.Figure:
    """
    Crea gráfico de barras de dirección de ciclistas
    
    Args:
        metrics: Diccionario con métricas
        
    Returns:
        Figura de Plotly
    """
    data = {
        'Dirección': ['Hacia Arriba ↑', 'Hacia Abajo ↓'],
        'Cantidad': [metrics['cyclists_up'], metrics['cyclists_down']],
        'Color': ['#00CC96', '#EF553B']
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=data['Dirección'],
            y=data['Cantidad'],
            marker_color=data['Color'],
            text=data['Cantidad'],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Distribución por Dirección",
        xaxis_title="Dirección",
        yaxis_title="Número de Ciclistas",
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig


def create_flow_gauge(metrics: Dict) -> go.Figure:
    """
    Crea indicador de flujo de ciclistas/hora
    
    Args:
        metrics: Diccionario con métricas
        
    Returns:
        Figura de Plotly con gauge
    """
    cyclists_per_hour = metrics['cyclists_per_hour']
    
    # Determinar color basado en flujo
    if cyclists_per_hour < 50:
        color = "#EF553B"  # Rojo - Bajo flujo
        category = "Bajo Flujo"
    elif cyclists_per_hour < 150:
        color = "#FFA15A"  # Naranja - Flujo medio
        category = "Flujo Medio"
    else:
        color = "#00CC96"  # Verde - Alto flujo
        category = "Alto Flujo"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=cyclists_per_hour,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Flujo Proyectado<br><span style='font-size:0.8em;color:gray'>{category}</span>"},
        delta={'reference': 100},
        gauge={
            'axis': {'range': [None, 300]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 50], 'color': "rgba(239, 85, 59, 0.2)"},
                {'range': [50, 150], 'color': "rgba(255, 161, 90, 0.2)"},
                {'range': [150, 300], 'color': "rgba(0, 204, 150, 0.2)"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': 150
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig


def create_comparison_chart(metrics: Dict) -> go.Figure:
    """
    Crea gráfico comparativo de métricas temporales
    
    Args:
        metrics: Diccionario con métricas
        
    Returns:
        Figura de Plotly
    """
    data = {
        'Métrica': ['Por Minuto', 'Por Hora (Proyección)'],
        'Ciclistas': [
            metrics['cyclists_per_minute'],
            metrics['cyclists_per_hour']
        ]
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=data['Métrica'],
            y=data['Ciclistas'],
            marker_color=['#636EFA', '#00CC96'],
            text=[f"{val:.1f}" for val in data['Ciclistas']],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Flujo Temporal de Ciclistas",
        xaxis_title="Período de Tiempo",
        yaxis_title="Número de Ciclistas",
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig


def generate_recommendations(metrics: Dict) -> str:
    """
    Genera recomendaciones basadas en métricas
    
    Args:
        metrics: Diccionario con métricas
        
    Returns:
        String con recomendaciones en Markdown
    """
    cyclists_per_hour = metrics['cyclists_per_hour']
    total = metrics['total_cyclists']
    
    recommendations = "### 💡 Recomendaciones para Planificación Urbana\n\n"
    
    if cyclists_per_hour < 50:
        recommendations += f"""
**Flujo Bajo** ({cyclists_per_hour:.0f} ciclistas/hora proyectados)

- ⚠️ El flujo de ciclistas es bajo para justificar infraestructura dedicada
- 📍 Considerar señalización compartida con vehículos
- 📊 Recopilar datos en diferentes horarios para análisis completo
- 🎯 Evaluar campañas de promoción de movilidad en bicicleta
"""
    elif cyclists_per_hour < 150:
        recommendations += f"""
**Flujo Medio** ({cyclists_per_hour:.0f} ciclistas/hora proyectados)

- ✅ Flujo suficiente para considerar ciclovía compartida
- 🚦 Implementar señalización específica para ciclistas
- 🛣️ Considerar carril compartido con buses (si aplica)
- 📈 Monitorear crecimiento en próximos meses
"""
    else:
        recommendations += f"""
**Flujo Alto** ({cyclists_per_hour:.0f} ciclistas/hora proyectados)

- 🎯 **Prioridad Alta**: Implementar ciclovía segregada
- 🚴‍♂️ Infraestructura justifica inversión en carril exclusivo
- 🔒 Considerar estacionamientos seguros para bicicletas
- 📊 Evaluar necesidad de semáforos específicos para ciclistas
"""
    
    # Análisis de dirección
    up_ratio = metrics['cyclists_up'] / total if total > 0 else 0
    down_ratio = metrics['cyclists_down'] / total if total > 0 else 0
    
    recommendations += f"\n**Análisis de Direccionalidad:**\n\n"
    
    if abs(up_ratio - down_ratio) > 0.3:
        dominant_dir = "Arriba ↑" if up_ratio > down_ratio else "Abajo ↓"
        recommendations += f"- 📊 Flujo predominante hacia **{dominant_dir}** ({max(up_ratio, down_ratio)*100:.0f}%)\n"
        recommendations += f"- 🎯 Considerar optimización unidireccional en horas pico\n"
    else:
        recommendations += f"- ✅ Flujo bidireccional equilibrado\n"
        recommendations += f"- 🎯 Diseño debe considerar tráfico en ambas direcciones\n"
    
    return recommendations


def display_technical_details(metrics: Dict) -> None:
    """
    Muestra detalles técnicos en un expander
    
    Args:
        metrics: Diccionario con métricas
    """
    with st.expander("🔧 Detalles Técnicos del Análisis"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
**Parámetros del Modelo:**
- Modelo: {metrics['model_used']}
- Confianza: {metrics['confidence_threshold']}
- Tracking: BoT-SORT

**Información del Video:**
- Duración: {metrics['duration_seconds']:.2f} segundos
- FPS: {metrics['fps']}
- Frames totales: {metrics['total_frames']}
- Frames procesados: {metrics['processed_frames']}
            """)
        
        with col2:
            st.markdown(f"""
**Resultados de Detección:**
- Total detectado: {metrics['total_cyclists']}
- Dirección arriba: {metrics['cyclists_up']}
- Dirección abajo: {metrics['cyclists_down']}

**Métricas de Flujo:**
- Por minuto: {metrics['cyclists_per_minute']:.2f}
- Por hora: {metrics['cyclists_per_hour']:.2f}
            """)


def create_summary_dataframe(metrics: Dict) -> pd.DataFrame:
    """
    Crea DataFrame resumen para exportar
    
    Args:
        metrics: Diccionario con métricas
        
    Returns:
        DataFrame con resumen
    """
    data = {
        'Métrica': [
            'Total Ciclistas',
            'Ciclistas hacia Arriba',
            'Ciclistas hacia Abajo',
            'Ciclistas por Minuto',
            'Ciclistas por Hora (Proyección)',
            'Duración Video (min)',
            'Modelo Utilizado',
            'Confianza Mínima'
        ],
        'Valor': [
            metrics['total_cyclists'],
            metrics['cyclists_up'],
            metrics['cyclists_down'],
            f"{metrics['cyclists_per_minute']:.2f}",
            f"{metrics['cyclists_per_hour']:.2f}",
            f"{metrics['duration_minutes']:.2f}",
            metrics['model_used'],
            metrics['confidence_threshold']
        ]
    }
    
    return pd.DataFrame(data)
