"""
Módulo de detección y tracking de ciclistas usando YOLOv11
"""
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple, Dict
import logging
import os
import subprocess
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_video_to_h264(input_path: str, output_path: str = None) -> str:
    """
    Convierte un video a formato H.264 compatible con navegadores web usando FFmpeg.

    Esta función es esencial para Streamlit Cloud, donde el reproductor de video
    del navegador solo soporta H.264, no mp4v ni otros codecs de OpenCV.

    Args:
        input_path: Ruta al video de entrada
        output_path: Ruta al video de salida (si None, se usa input_path_h264.mp4)

    Returns:
        Ruta al video convertido

    Raises:
        RuntimeError: Si FFmpeg no está disponible o falla la conversión
    """
    # Verificar si ffmpeg está disponible
    if not shutil.which('ffmpeg'):
        logger.warning("⚠️ FFmpeg no está disponible. El video podría no reproducirse en Streamlit Cloud.")
        return input_path

    # Determinar ruta de salida
    if output_path is None:
        base_path = input_path.replace('_processed.mp4', '')
        output_path = f"{base_path}_processed_h264.mp4"

    try:
        logger.info(f"🔄 Convirtiendo video a H.264 para compatibilidad web...")

        # Comando FFmpeg optimizado para web
        # -c:v libx264: codec H.264
        # -preset fast: velocidad de encoding
        # -crf 23: calidad (18-28, menor = mejor calidad)
        # -pix_fmt yuv420p: formato de pixel compatible con navegadores
        # -movflags +faststart: optimiza para streaming web
        # -c:a copy: copiar audio sin recodificar (si existe)
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            '-c:a', 'aac',  # codec de audio compatible
            '-b:a', '128k',  # bitrate de audio
            '-y',  # sobrescribir si existe
            output_path
        ]

        # Ejecutar FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # timeout de 5 minutos
        )

        if result.returncode != 0:
            logger.error(f"❌ Error en FFmpeg: {result.stderr}")
            logger.warning("⚠️ Usando video original sin conversión")
            return input_path

        # Verificar que el archivo se creó
        if not os.path.exists(output_path):
            logger.warning("⚠️ El video convertido no se creó. Usando original.")
            return input_path

        file_size = os.path.getsize(output_path) / (1024*1024)
        logger.info(f"✅ Video convertido a H.264: {output_path} ({file_size:.2f} MB)")

        # Eliminar el video temporal original
        try:
            os.remove(input_path)
            logger.debug(f"🗑️ Video temporal eliminado: {input_path}")
        except Exception as e:
            logger.debug(f"No se pudo eliminar video temporal: {e}")

        return output_path

    except subprocess.TimeoutExpired:
        logger.error("❌ FFmpeg timeout - el video es muy largo")
        return input_path
    except Exception as e:
        logger.error(f"❌ Error convirtiendo video: {e}")
        return input_path


class CyclistDetector:
    """
    Detector de ciclistas usando YOLOv11 con tracking BoT-SORT
    """
    
    # Clases en COCO dataset
    PERSON_CLASS_ID = 0
    BICYCLE_CLASS_ID = 1
    
    def __init__(self, model_size: str = "n", conf_threshold: float = 0.15, detect_persons: bool = False):
        """
        Inicializa el detector
        
        Args:
            model_size: 'n' (nano) o 's' (small)
            conf_threshold: Umbral de confianza (0-1) - 0.15 recomendado
            detect_persons: Si True, detecta personas además de bicicletas (puede causar falsos positivos)
        """
        self.model_size = model_size
        self.conf_threshold = conf_threshold
        self.detect_persons = detect_persons
        
        # Configurar clases a detectar
        if detect_persons:
            self.detection_classes = [self.PERSON_CLASS_ID, self.BICYCLE_CLASS_ID]
            logger.info("⚠️  Detectando PERSONAS + BICICLETAS (puede causar falsos positivos)")
        else:
            self.detection_classes = [self.BICYCLE_CLASS_ID]
            logger.info("✅ Detectando solo BICICLETAS (recomendado)")
        
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """Carga el modelo YOLOv11"""
        try:
            model_name = f"yolo11{self.model_size}.pt"
            logger.info(f"Cargando modelo: {model_name}")
            self.model = YOLO(model_name)
            logger.info(f"✅ Modelo {model_name} cargado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
            raise
    
    def detect_and_track(
        self,
        video_path: str,
        line_position: float = 0.5,
        line_position_x: float = 0.5,
        line_orientation: str = "horizontal",
        process_every_n_frames: int = 1,
        progress_callback=None
    ) -> Tuple[str, Dict]:
        """
        Detecta y rastrea ciclistas en video

        Args:
            video_path: Ruta al video
            line_position: Posición de línea de conteo horizontal (0-1, fracción de altura)
            line_position_x: Posición de línea de conteo vertical (0-1, fracción de ancho)
            line_orientation: "horizontal", "vertical" o "both"
            process_every_n_frames: Procesar cada N frames (para velocidad)
            progress_callback: Función callback(progress_percent, status_message)

        Returns:
            Tupla de (ruta_video_procesado, diccionario_metricas)
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"No se puede abrir el video: {video_path}")
        
        # Propiedades del video
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Líneas de conteo
        line_y = int(height * line_position)  # Línea horizontal
        line_x = int(width * line_position_x)  # Línea vertical

        # Video de salida temporal - usar mp4v (compatible con OpenCV)
        # Nota: Este video será convertido a H.264 con FFmpeg al final para
        # compatibilidad con navegadores web y Streamlit Cloud
        output_path = video_path.replace('.mp4', '_processed.mp4')

        # Usar mp4v como codec temporal (será convertido a H.264 después)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Verificar que se haya creado correctamente
        if not out.isOpened():
            logger.error("❌ No se pudo crear el VideoWriter con codec mp4v")
            # Intentar con MJPG como alternativa
            logger.warning("⚠️ Intentando con codec MJPEG...")
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            if not out.isOpened():
                raise ValueError("Error al crear el archivo de video de salida")

        logger.info(f"✅ VideoWriter creado con OpenCV (será convertido a H.264)")

        # Tracking de objetos que cruzaron las líneas
        # Para línea horizontal
        tracked_ids_up = set()    # IDs que cruzaron hacia arriba
        tracked_ids_down = set()  # IDs que cruzaron hacia abajo
        # Para línea vertical
        tracked_ids_left = set()   # IDs que cruzaron hacia la izquierda
        tracked_ids_right = set()  # IDs que cruzaron hacia la derecha
        previous_positions = {}    # {track_id: (x, y)}
        
        frame_count = 0
        processed_frames = 0
        
        logger.info(f"Procesando video: {total_frames} frames @ {fps} FPS")
        logger.info(f"Detectando clases: {self.detection_classes} (1=bicycle" + (", 0=person" if self.detect_persons else "") + ")")
        logger.info(f"Umbral de confianza: {self.conf_threshold}")
        
        # Callback inicial
        if progress_callback:
            progress_callback(0, "Iniciando procesamiento...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Procesar cada N frames para velocidad
            if frame_count % process_every_n_frames != 0:
                out.write(frame)
                continue
            
            processed_frames += 1
            
            # Detección y tracking con BoT-SORT
            results = self.model.track(
                frame,
                persist=True,
                conf=self.conf_threshold,
                classes=self.detection_classes,  # Solo bicycle por defecto, o person+bicycle si se habilita
                tracker="botsort.yaml",
                verbose=False
            )
            
            # Callback de progreso mejorado (actualiza más frecuentemente)
            if progress_callback and processed_frames % 5 == 0:
                progress_percent = int((frame_count / total_frames) * 100)
                elapsed_time = (frame_count / fps) if fps > 0 else 0
                frames_per_sec = frame_count / max(elapsed_time, 0.1)

                # Calcular total detectados según orientación
                if line_orientation == "horizontal":
                    total_detected = len(tracked_ids_up) + len(tracked_ids_down)
                    status_msg = f"Frame {frame_count}/{total_frames} ({progress_percent}%) | Detectados: {total_detected} | FPS: {frames_per_sec:.1f}"
                elif line_orientation == "vertical":
                    total_detected = len(tracked_ids_left) + len(tracked_ids_right)
                    status_msg = f"Frame {frame_count}/{total_frames} ({progress_percent}%) | Detectados: {total_detected} | FPS: {frames_per_sec:.1f}"
                else:  # both
                    total_h = len(tracked_ids_up) + len(tracked_ids_down)
                    total_v = len(tracked_ids_left) + len(tracked_ids_right)
                    status_msg = f"Frame {frame_count}/{total_frames} ({progress_percent}%) | H:{total_h} V:{total_v} | FPS: {frames_per_sec:.1f}"

                progress_callback(progress_percent, status_msg)
            
            # Dibujar línea(s) de conteo según orientación
            if line_orientation in ["horizontal", "both"]:
                cv2.line(frame, (0, line_y), (width, line_y), (0, 255, 255), 3)
                cv2.putText(
                    frame,
                    "LINEA HORIZONTAL",
                    (10, line_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2
                )

            if line_orientation in ["vertical", "both"]:
                cv2.line(frame, (line_x, 0), (line_x, height), (255, 0, 255), 3)
                cv2.putText(
                    frame,
                    "LINEA VERTICAL",
                    (line_x + 10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 0, 255),
                    2
                )
            
            # Procesar detecciones
            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                track_ids = results[0].boxes.id.cpu().numpy().astype(int)
                confidences = results[0].boxes.conf.cpu().numpy()
                classes = results[0].boxes.cls.cpu().numpy().astype(int)
                
                # Log para debugging (solo primeras detecciones)
                if processed_frames == 1:
                    logger.info(f"✅ Primera detección: {len(boxes)} objetos encontrados")
                    for i, cls in enumerate(classes):
                        cls_name = "person" if cls == 0 else "bicycle"
                        logger.info(f"   Objeto {i+1}: {cls_name} (confianza: {confidences[i]:.2f})")
                
                for box, track_id, conf, cls in zip(boxes, track_ids, confidences, classes):
                    x1, y1, x2, y2 = box
                    cx = int((x1 + x2) / 2)  # Centro X
                    cy = int((y1 + y2) / 2)  # Centro Y

                    # Verificar cruce de línea(s)
                    if track_id in previous_positions:
                        prev_cx, prev_cy = previous_positions[track_id]

                        # Verificar cruce de línea HORIZONTAL
                        if line_orientation in ["horizontal", "both"]:
                            # Cruce hacia arriba
                            if prev_cy > line_y and cy <= line_y:
                                if track_id not in tracked_ids_up:
                                    tracked_ids_up.add(track_id)
                                    logger.info(f"🚴 Ciclista #{track_id} cruzó ARRIBA (línea horizontal)")

                            # Cruce hacia abajo
                            elif prev_cy < line_y and cy >= line_y:
                                if track_id not in tracked_ids_down:
                                    tracked_ids_down.add(track_id)
                                    logger.info(f"🚴 Ciclista #{track_id} cruzó ABAJO (línea horizontal)")

                        # Verificar cruce de línea VERTICAL
                        if line_orientation in ["vertical", "both"]:
                            # Cruce hacia la izquierda
                            if prev_cx > line_x and cx <= line_x:
                                if track_id not in tracked_ids_left:
                                    tracked_ids_left.add(track_id)
                                    logger.info(f"🚴 Ciclista #{track_id} cruzó IZQUIERDA (línea vertical)")

                            # Cruce hacia la derecha
                            elif prev_cx < line_x and cx >= line_x:
                                if track_id not in tracked_ids_right:
                                    tracked_ids_right.add(track_id)
                                    logger.info(f"🚴 Ciclista #{track_id} cruzó DERECHA (línea vertical)")

                    # Actualizar posición
                    previous_positions[track_id] = (cx, cy)
                    
                    # Dibujar bounding box
                    color = (0, 255, 0)
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    
                    # Label
                    label = f"ID:{track_id} {conf:.2f}"
                    cv2.putText(
                        frame,
                        label,
                        (int(x1), int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        color,
                        2
                    )
                    
                    # Punto central
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            
            # Mostrar contadores según orientación
            info_text = []

            if line_orientation == "horizontal":
                total_count = len(tracked_ids_up) + len(tracked_ids_down)
                info_text = [
                    f"Total: {total_count}",
                    f"Arriba: {len(tracked_ids_up)}",
                    f"Abajo: {len(tracked_ids_down)}",
                    f"Frame: {frame_count}/{total_frames}"
                ]
            elif line_orientation == "vertical":
                total_count = len(tracked_ids_left) + len(tracked_ids_right)
                info_text = [
                    f"Total: {total_count}",
                    f"Izquierda: {len(tracked_ids_left)}",
                    f"Derecha: {len(tracked_ids_right)}",
                    f"Frame: {frame_count}/{total_frames}"
                ]
            else:  # both
                total_h = len(tracked_ids_up) + len(tracked_ids_down)
                total_v = len(tracked_ids_left) + len(tracked_ids_right)
                info_text = [
                    f"Horizontal: {total_h} (Arr:{len(tracked_ids_up)} Aba:{len(tracked_ids_down)})",
                    f"Vertical: {total_v} (Izq:{len(tracked_ids_left)} Der:{len(tracked_ids_right)})",
                    f"Total Unico: {len(set(list(tracked_ids_up) + list(tracked_ids_down) + list(tracked_ids_left) + list(tracked_ids_right)))}",
                    f"Frame: {frame_count}/{total_frames}"
                ]

            y_offset = 30
            for i, text in enumerate(info_text):
                cv2.putText(
                    frame,
                    text,
                    (10, y_offset + i * 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA
                )
            
            out.write(frame)
            
            # Progress
            if processed_frames % 30 == 0:
                progress = (frame_count / total_frames) * 100
                logger.info(f"Progreso: {progress:.1f}%")
        
        cap.release()
        out.release()

        # Asegurar que el archivo se haya escrito correctamente
        if not os.path.exists(output_path):
            logger.error(f"❌ El archivo de salida no se creó: {output_path}")
            raise ValueError("No se pudo crear el video procesado")

        file_size = os.path.getsize(output_path)
        if file_size == 0:
            logger.error(f"❌ El archivo de salida está vacío: {output_path}")
            raise ValueError("El video procesado está vacío")

        logger.info(f"✅ Video procesado guardado: {output_path} ({file_size / (1024*1024):.2f} MB)")

        # Validar que el video se puede leer correctamente
        try:
            test_cap = cv2.VideoCapture(output_path)
            if not test_cap.isOpened():
                logger.warning("⚠️ El video generado no se puede abrir, pero el archivo existe")
            else:
                test_frames = int(test_cap.get(cv2.CAP_PROP_FRAME_COUNT))
                logger.info(f"✅ Video validado: {test_frames} frames")
                test_cap.release()
        except Exception as e:
            logger.warning(f"⚠️ No se pudo validar el video: {e}")

        # Callback final
        if progress_callback:
            progress_callback(100, "Procesamiento completado!")
        
        # Calcular métricas
        duration_seconds = total_frames / fps
        duration_minutes = duration_seconds / 60

        # Calcular totales según orientación de línea
        if line_orientation == "horizontal":
            total_cyclists = len(tracked_ids_up) + len(tracked_ids_down)
        elif line_orientation == "vertical":
            total_cyclists = len(tracked_ids_left) + len(tracked_ids_right)
        else:  # both - contar IDs únicos
            all_ids = set(list(tracked_ids_up) + list(tracked_ids_down) + list(tracked_ids_left) + list(tracked_ids_right))
            total_cyclists = len(all_ids)

        cyclists_per_minute = total_cyclists / duration_minutes if duration_minutes > 0 else 0
        cyclists_per_hour = cyclists_per_minute * 60

        metrics = {
            'total_cyclists': total_cyclists,
            'cyclists_up': len(tracked_ids_up),
            'cyclists_down': len(tracked_ids_down),
            'cyclists_left': len(tracked_ids_left),
            'cyclists_right': len(tracked_ids_right),
            'cyclists_per_minute': round(cyclists_per_minute, 2),
            'cyclists_per_hour': round(cyclists_per_hour, 2),
            'duration_seconds': round(duration_seconds, 2),
            'duration_minutes': round(duration_minutes, 2),
            'fps': fps,
            'total_frames': total_frames,
            'processed_frames': processed_frames,
            'model_used': f"YOLOv11{self.model_size}",
            'confidence_threshold': self.conf_threshold,
            'line_orientation': line_orientation
        }
        
        logger.info("=" * 50)
        logger.info("RESULTADOS FINALES:")
        if total_cyclists == 0:
            logger.warning("⚠️  NO SE DETECTARON CICLISTAS")
            logger.info("💡 Sugerencias:")
            logger.info("   - Reducir umbral de confianza (actual: {:.2f})".format(self.conf_threshold))
            logger.info("   - Verificar que el video contenga ciclistas visibles")
            logger.info("   - Usar modelo Small (más preciso) en vez de Nano")
        else:
            logger.info(f"✅ Total ciclistas: {total_cyclists}")
            if line_orientation in ["horizontal", "both"]:
                logger.info(f"↑ Hacia arriba: {len(tracked_ids_up)}")
                logger.info(f"↓ Hacia abajo: {len(tracked_ids_down)}")
            if line_orientation in ["vertical", "both"]:
                logger.info(f"← Hacia izquierda: {len(tracked_ids_left)}")
                logger.info(f"→ Hacia derecha: {len(tracked_ids_right)}")
            logger.info(f"📊 Ciclistas/minuto: {cyclists_per_minute:.2f}")
            logger.info(f"📊 Ciclistas/hora (proyección): {cyclists_per_hour:.2f}")
        logger.info("=" * 50)

        # Convertir video a H.264 para compatibilidad con Streamlit Cloud
        logger.info("🎬 Convirtiendo video a formato compatible con navegadores web...")
        output_path = convert_video_to_h264(output_path)

        return output_path, metrics
