"""
Web Scraper Pro - Aplicación principal para descarga de sitios web
Version: 1.0.0
Author: Alexander Oviedo Fadul
Website: https://alexanderoviedofadul.dev
GitHub: https://github.com/bladealex9848
"""

import streamlit as st
import os
import sys
import time
import json
import shutil
import logging
import platform
import threading
import validators
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from webscraper.scraper import WebScraper

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webscraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Versión y configuración
APP_VERSION = "1.0.0"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB

def format_size(size_in_bytes: float) -> str:
    """Formatea un tamaño en bytes a una representación legible."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"

def load_custom_css():
    """Carga estilos CSS personalizados para la interfaz."""
    st.markdown("""
        <style>
        /* Estilos generales */
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
            font-family: 'Inter', sans-serif;
        }
        
        /* Encabezados */
        h1 {
            color: #1E88E5;
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            margin-bottom: 1rem !important;
        }
        
        /* Botones */
        .stButton > button {
            width: 100%;
            background-color: #1E88E5;
            color: white;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            border: none;
            transition: all 0.3s ease;
        }
        
        /* Hover effects */
        .stButton > button:hover {
            background-color: #1565C0;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        /* Progress bar */
        .stProgress > div > div {
            background-color: #1E88E5;
            border-radius: 10px;
        }
        
        /* Cards */
        .metric-card {
            background-color: #FFFFFF;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }
        
        /* Messages */
        .success-message {
            background-color: #4CAF50;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .error-message {
            background-color: #F44336;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        /* File structure */
        .file-structure {
            font-family: 'JetBrains Mono', monospace;
            background-color: #F5F5F5;
            padding: 1rem;
            border-radius: 8px;
            font-size: 0.9rem;
        }
        </style>
    """, unsafe_allow_html=True)

def setup_page():
    """Configura la página de Streamlit con ajustes optimizados."""
    st.set_page_config(
        page_title="Web Scraper Pro",
        page_icon="🌐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    load_custom_css()

def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """Valida una URL y retorna su estado de validación y mensaje de error."""
    if not url:
        return False, "La URL no puede estar vacía"
        
    if not url.startswith(('http://', 'https://')):
        return False, "La URL debe comenzar con http:// o https://"
        
    if not validators.url(url):
        return False, "La URL no tiene un formato válido"
        
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return False, "La URL está incompleta"
    except Exception as e:
        return False, f"Error al analizar la URL: {str(e)}"
        
    return True, None

def show_stats(stats: Dict[str, Any]):
    """Muestra las estadísticas en un formato visual atractivo."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📁 Archivos",
            value=stats['archivos_procesados'],
            delta=None,
            help="Número total de archivos procesados"
        )
    
    with col2:
        st.metric(
            label="💾 Tamaño Total",
            value=format_size(stats['bytes_descargados']),
            delta=None,
            help="Cantidad total de datos descargados"
        )
    
    with col3:
        st.metric(
            label="⏱️ Tiempo Total",
            value=f"{stats['tiempo_total']:.2f}s",
            delta=None,
            help="Tiempo total de procesamiento"
        )
    
    with col4:
        st.metric(
            label="🔄 Velocidad",
            value=f"{format_size(stats['velocidad_promedio'])}/s",
            delta=None,
            help="Velocidad promedio de descarga"
        )

def show_file_structure(path: Path):
    """Muestra la estructura de archivos en formato jerárquico."""
    def get_tree(p: Path, prefix: str = "") -> str:
        if not p.is_dir():
            return ""
        
        tree = []
        items = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            node = "└──" if is_last else "├──"
            
            if item.is_file():
                size = format_size(item.stat().st_size)
                tree.append(f"{prefix}{node} 📄 {item.name} ({size})")
            else:
                tree.append(f"{prefix}{node} 📁 {item.name}/")
                nuevo_prefix = prefix + ("    " if is_last else "│   ")
                tree.append(get_tree(item, nuevo_prefix))
        
        return "\n".join(tree)
    
    estructura = get_tree(path)
    st.code(estructura, language="plaintext")

def main():
    """Función principal de la aplicación."""
    setup_page()

    st.title("Web Scraper Pro 🌐")
    st.markdown(
        """
        <p style='font-size: 1.2rem; color: #666; margin-bottom: 2rem;'>
        Herramienta profesional para la descarga y almacenamiento local de sitios web completos.
        </p>
        """,
        unsafe_allow_html=True
    )

    # Configuración en la barra lateral
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        mantener_estructura = st.checkbox(
            "📁 Mantener estructura de directorios",
            value=True,
            help="Preserva la estructura original del sitio"
        )
        
        incluir_imagenes = st.checkbox(
            "🖼️ Incluir imágenes",
            value=True,
            help="Descarga imágenes y recursos multimedia"
        )
        
        incluir_css = st.checkbox(
            "🎨 Incluir CSS",
            value=True,
            help="Descarga archivos de estilos"
        )
        
        incluir_js = st.checkbox(
            "⚡ Incluir JavaScript",
            value=True,
            help="Descarga archivos JavaScript"
        )
        
        st.markdown("---")
        
        with st.expander("🔧 Configuración Avanzada", expanded=False):
            max_profundidad = st.slider(
                "🔄 Profundidad máxima",
                min_value=1,
                max_value=5,
                value=3,
                help="Niveles de profundidad para la descarga"
            )
            
            timeout = st.slider(
                "⏱️ Timeout (segundos)",
                min_value=10,
                max_value=60,
                value=30,
                help="Tiempo máximo de espera por recurso"
            )
        
        if 'total_descargas' not in st.session_state:
            st.session_state.total_descargas = 0
        
        st.metric(
            "📊 Total de descargas",
            st.session_state.total_descargas,
            help="Número total de descargas realizadas"
        )

    # URL input y validación
    url = st.text_input(
        "🌐 URL del sitio web:",
        placeholder="https://ejemplo.com",
        help="Introduce la URL completa del sitio web a descargar"
    )
    
    url_valida, error_mensaje = validate_url(url) if url else (False, None)
    
    if error_mensaje:
        st.warning(f"⚠️ {error_mensaje}")

    # Botones de acción
    col1, col2 = st.columns(2)
    with col1:
        iniciar_descarga = st.button(
            "📥 Iniciar Descarga",
            disabled=not url_valida,
            help="Comenzar la descarga del sitio web"
        )
    
    with col2:
        limpiar_cache = st.button(
            "🧹 Limpiar Caché",
            help="Eliminar archivos temporales y caché"
        )

    # Proceso de limpieza de caché
    if limpiar_cache:
        try:
            if Path("temp_download").exists():
                shutil.rmtree("temp_download")
            st.success("✨ Caché limpiado correctamente")
        except Exception as e:
            st.error(f"❌ Error al limpiar caché: {str(e)}")

    # Proceso de descarga
    if iniciar_descarga and url_valida:
        try:
            # Preparar directorios
            carpeta_temp = Path("temp_download")
            if carpeta_temp.exists():
                shutil.rmtree(carpeta_temp)
            carpeta_temp.mkdir(parents=True)

            # Contenedores para progreso
            progress_container = st.empty()
            status_container = st.empty()

            with progress_container:
                progress_bar = st.progress(0)
                st.info("🚀 Iniciando proceso de descarga...")

            # Configurar scraper
            scraper = WebScraper(
                base_url=url,
                carpeta_destino=str(carpeta_temp),
                mantener_estructura=mantener_estructura,
                incluir_imagenes=incluir_imagenes,
                incluir_css=incluir_css,
                incluir_js=incluir_js,
                max_profundidad=max_profundidad,
                timeout=timeout
            )

            # Ejecutar descarga
            if scraper.descargar_pagina(progress_bar, status_container):
                # Actualizar contador
                st.session_state.total_descargas += 1
                
                # Obtener estadísticas
                stats = scraper.obtener_estadisticas()
                
                # Limpiar contenedores temporales
                progress_container.empty()
                status_container.empty()
                
                # Mostrar éxito
                st.success("✅ ¡Descarga completada exitosamente!")
                
                # Mostrar estadísticas
                show_stats(stats)
                
                # Mostrar estructura
                with st.expander("📂 Estructura de archivos", expanded=True):
                    show_file_structure(carpeta_temp)

                # Preparar ZIP
                try:
                    zip_path = "sitio_web.zip"
                    shutil.make_archive(
                        zip_path.replace('.zip', ''),
                        'zip',
                        carpeta_temp
                    )
                    
                    # Botón de descarga
                    with open(zip_path, "rb") as fp:
                        st.download_button(
                            label="📦 Descargar ZIP",
                            data=fp,
                            file_name=zip_path,
                            mime="application/zip",
                            help="Descargar el sitio web completo en formato ZIP"
                        )
                except Exception as e:
                    st.error(f"❌ Error al crear archivo ZIP: {str(e)}")
                
                # Guardar log
                try:
                    log_entry = {
                        "fecha": datetime.now().isoformat(),
                        "url": url,
                        "configuracion": {
                            "mantener_estructura": mantener_estructura,
                            "incluir_imagenes": incluir_imagenes,
                            "incluir_css": incluir_css,
                            "incluir_js": incluir_js,
                            "max_profundidad": max_profundidad,
                            "timeout": timeout
                        },
                        "estadisticas": {
                            "archivos_procesados": stats['archivos_procesados'],
                            "bytes_descargados": stats['bytes_descargados'],
                            "tiempo_total": stats['tiempo_total'],
                            "velocidad_promedio": stats['velocidad_promedio'],
                            "errores": stats.get('errores', 0)
                        },
                        "sistema": {
                            "version_app": APP_VERSION,
                            "python_version": platform.python_version(),
                            "sistema_operativo": platform.system(),
                            "arquitectura": platform.machine(),
                            "encoding": sys.getfilesystemencoding(),
                            "timestamp": int(time.time()),
                            "memoria_disponible": format_size(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')),
                            "tiempo_ejecucion": time.time() - stats.get('inicio', 0)
                        }
                    }

                    # Gestión de rotación de logs
                    log_file = Path("descargas.log")
                    if log_file.exists() and log_file.stat().st_size > MAX_LOG_SIZE:
                        # Crear backup del log actual
                        backup_name = f"descargas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                        shutil.move("descargas.log", backup_name)

                    # Guardar log con manejo de errores de escritura
                    try:
                        with open("descargas.log", "a", encoding='utf-8') as f:
                            json.dump(log_entry, f, ensure_ascii=False)
                            f.write("\n")
                    except PermissionError:
                        st.warning("⚠️ No se pudo guardar el registro por falta de permisos")
                        logger.warning("Error de permisos al escribir el log")
                    except Exception as e:
                        logger.error(f"Error guardando log: {str(e)}")

                except Exception as e:
                    logger.error(f"Error preparando entrada de log: {str(e)}")

            else:
                st.error("❌ Error durante la descarga del sitio")

        except Exception as e:
            st.error(f"❌ Error durante el proceso: {str(e)}")
            logger.error(f"Error en proceso de descarga: {str(e)}")
        
        finally:
            # Limpieza y liberación de recursos
            if 'progress_container' in locals():
                progress_container.empty()
            if 'status_container' in locals():
                status_container.empty()
            
            # Limpiar archivos temporales si es necesario
            try:
                if os.path.exists("sitio_web.zip"):
                    os.remove("sitio_web.zip")
            except Exception as e:
                logger.error(f"Error limpiando archivos temporales: {str(e)}")

    # Footer con información y enlaces
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center'>
            <p style='color: #666; font-size: 0.9rem;'>
                Desarrollado con ❤️ por 
                <a href="https://alexanderoviedofadul.dev" target="_blank" 
                style='color: #1E88E5; text-decoration: none; font-weight: bold;'>
                Alexander Oviedo Fadul
                </a>
            </p>
            <div style='display: flex; justify-content: center; gap: 1rem; margin: 1rem 0;'>
                <a href="https://github.com/bladealex9848/web-scraper-pro" target="_blank" 
                style='color: #1E88E5; text-decoration: none;'>
                    <span style='display: flex; align-items: center; gap: 0.5rem;'>
                        <i class="fab fa-github"></i> GitHub
                    </span>
                </a>
                <a href="https://alexanderoviedofadul.dev" target="_blank" 
                style='color: #1E88E5; text-decoration: none;'>
                    <span style='display: flex; align-items: center; gap: 0.5rem;'>
                        <i class="fas fa-globe"></i> Website
                    </span>
                </a>
                <a href="https://github.com/bladealex9848/web-scraper-pro/issues" target="_blank" 
                style='color: #1E88E5; text-decoration: none;'>
                    <span style='display: flex; align-items: center; gap: 0.5rem;'>
                        <i class="fas fa-bug"></i> Reportar Bug
                    </span>
                </a>
            </div>
            <p style='color: #666; font-size: 0.8rem; margin-top: 1rem;'>
                Versión {APP_VERSION} | © {datetime.now().year}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Error crítico en la aplicación: {str(e)}")
        logger.critical(f"Error crítico: {str(e)}")
        
        # Información de debugging en modo desarrollo
        if os.getenv('WEBSCRAPER_DEBUG'):
            st.error("Información de debugging:")
            st.code(f"""
            Python: {sys.version}
            Platform: {platform.platform()}
            Working Directory: {os.getcwd()}
            Exception Type: {type(e).__name__}
            Exception Args: {e.args}
            Memoria Disponible: {format_size(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES'))}
            """)

            # Registro detallado del error
            logger.exception("Error detallado:")