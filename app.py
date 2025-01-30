import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import shutil
from pathlib import Path
import concurrent.futures
import logging
from urllib.parse import urljoin, urlparse
import zipfile
import time
import json
from datetime import datetime
import threading
from typing import Optional, Dict, List, Union
import hashlib
import mimetypes
import re

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webscraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebScraperConfig:
    """Configuración centralizada para el Web Scraper"""
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }
    CHUNK_SIZE = 8192
    MAX_WORKERS = 5
    TIMEOUT = 30
    VALID_SCHEMES = {'http', 'https'}
    CACHE_EXPIRY = 3600  # 1 hora en segundos

class ResourceManager:
    """Gestiona la descarga y almacenamiento de recursos"""
    def __init__(self, session: requests.Session, base_url: str):
        self.session = session
        self.base_url = base_url
        self._cache = {}
        self._lock = threading.Lock()

    def get_resource(self, url: str) -> Optional[bytes]:
        """Obtiene un recurso con caché"""
        cache_key = self._get_cache_key(url)
        
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached and time.time() - cached['timestamp'] < WebScraperConfig.CACHE_EXPIRY:
                return cached['data']

        try:
            response = self.session.get(
                url, 
                timeout=WebScraperConfig.TIMEOUT,
                stream=True
            )
            response.raise_for_status()
            
            data = b''.join(response.iter_content(chunk_size=WebScraperConfig.CHUNK_SIZE))
            
            with self._lock:
                self._cache[cache_key] = {
                    'data': data,
                    'timestamp': time.time()
                }
            
            return data
        except Exception as e:
            logger.error(f"Error descargando recurso {url}: {str(e)}")
            return None

    def _get_cache_key(self, url: str) -> str:
        """Genera una clave única para caché"""
        return hashlib.md5(url.encode()).hexdigest()

class WebScraper:
    """Clase principal para el scraping de sitios web"""
    def __init__(self, base_url: str, carpeta_destino: str, **kwargs):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.carpeta_destino = Path(carpeta_destino)
        self.session = self._configurar_session()
        self.resource_manager = ResourceManager(self.session, base_url)
        self.archivos_descargados = set()
        self.estadisticas = {
            'inicio': time.time(),
            'archivos_procesados': 0,
            'bytes_descargados': 0,
            'errores': 0
        }
        
        # Configuraciones
        self.config = {
            'mantener_estructura': kwargs.get('mantener_estructura', True),
            'incluir_imagenes': kwargs.get('incluir_imagenes', True),
            'incluir_css': kwargs.get('incluir_css', True),
            'incluir_js': kwargs.get('incluir_js', True),
            'max_profundidad': kwargs.get('max_profundidad', 1),
            'timeout': kwargs.get('timeout', WebScraperConfig.TIMEOUT)
        }

    def _configurar_session(self) -> requests.Session:
        """Configura la sesión HTTP con opciones optimizadas"""
        session = requests.Session()
        session.headers.update(WebScraperConfig.DEFAULT_HEADERS)
        return session

    def validar_url(self, url: str) -> bool:
        """Valida que la URL sea segura y accesible"""
        try:
            parsed = urlparse(url)
            return all([
                parsed.scheme in WebScraperConfig.VALID_SCHEMES,
                parsed.netloc,
                not any(c in url for c in '<>"\'{}|\\^[]`')
            ])
        except Exception:
            return False

    def obtener_ruta_relativa(self, url: str) -> Optional[str]:
        """Convierte una URL en una ruta de archivo relativa segura"""
        if not url:
            return None
        
        try:
            url_completa = urljoin(self.base_url, url)
            parsed = urlparse(url_completa)
            
            if parsed.netloc and parsed.netloc != self.domain:
                return None
                
            path = parsed.path
            if not path or path == '/':
                path = 'index.html'
            elif path.endswith('/'):
                path += 'index.html'
            
            # Sanitizar nombre de archivo
            path = re.sub(r'[<>:"/\\|?*]', '_', path)
            return path.lstrip('/')
            
        except Exception as e:
            logger.error(f"Error procesando URL {url}: {str(e)}")
            return None

    def descargar_recurso(self, url: str) -> Optional[str]:
        """Descarga un recurso y lo guarda en el sistema de archivos"""
        if not url or url in self.archivos_descargados:
            return None
            
        try:
            if not self.validar_url(url):
                logger.warning(f"URL no válida: {url}")
                return None
                
            ruta_relativa = self.obtener_ruta_relativa(url)
            if not ruta_relativa:
                return None
                
            ruta_completa = self.carpeta_destino / ruta_relativa
            
            # Crear directorio si no existe
            ruta_completa.parent.mkdir(parents=True, exist_ok=True)
            
            # Descargar recurso
            contenido = self.resource_manager.get_resource(urljoin(self.base_url, url))
            if contenido:
                with open(ruta_completa, 'wb') as f:
                    f.write(contenido)
                
                self.archivos_descargados.add(url)
                self.estadisticas['archivos_procesados'] += 1
                self.estadisticas['bytes_descargados'] += len(contenido)
                return ruta_relativa
                
        except Exception as e:
            logger.error(f"Error al descargar {url}: {str(e)}")
            self.estadisticas['errores'] += 1
            return None

    def procesar_elemento(self, elemento: BeautifulSoup, atributos: List[str]) -> None:
        """Procesa un elemento HTML y sus atributos"""
        for attr in atributos:
            if elemento.has_attr(attr):
                url = elemento[attr]
                ruta_relativa = self.descargar_recurso(url)
                if ruta_relativa:
                    elemento[attr] = ruta_relativa

    def descargar_pagina(self, progress_bar=None, status_text=None) -> bool:
        """Descarga una página web completa y sus recursos"""
        try:
            # Validar URL inicial
            if not self.validar_url(self.base_url):
                raise ValueError("URL base no válida")

            # Descargar página principal
            response = self.session.get(self.base_url, timeout=self.config['timeout'])
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Definir elementos a procesar según configuración
            elementos_a_procesar = {}
            if self.config['incluir_imagenes']:
                elementos_a_procesar.update({
                    'img': ['src', 'data-src'],
                    'source': ['src', 'srcset'],
                    'video': ['src', 'poster'],
                    'audio': ['src'],
                })
            if self.config['incluir_css']:
                elementos_a_procesar['link'] = ['href']
            if self.config['incluir_js']:
                elementos_a_procesar['script'] = ['src']

            # Contar elementos totales
            total_elementos = sum(len(soup.find_all(tag)) for tag in elementos_a_procesar)
            elementos_procesados = 0

            # Procesar elementos con ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=WebScraperConfig.MAX_WORKERS) as executor:
                futures = []
                
                for tag, atributos in elementos_a_procesar.items():
                    for elemento in soup.find_all(tag):
                        futures.append(
                            executor.submit(self.procesar_elemento, elemento, atributos)
                        )
                        
                        elementos_procesados += 1
                        if progress_bar:
                            progress_bar.progress(elementos_procesados / total_elementos)
                        if status_text:
                            status_text.text(f"Procesando: {elementos_procesados}/{total_elementos}")

            # Guardar HTML final
            ruta_index = self.carpeta_destino / 'index.html'
            with open(ruta_index, 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()))

            # Actualizar estadísticas finales
            self.estadisticas['tiempo_total'] = time.time() - self.estadisticas['inicio']
            return True

        except Exception as e:
            logger.error(f"Error al descargar la página: {str(e)}")
            self.estadisticas['errores'] += 1
            return False

    def obtener_estadisticas(self) -> Dict[str, Union[int, float]]:
        """Retorna estadísticas del proceso de descarga"""
        return {
            'archivos_procesados': self.estadisticas['archivos_procesados'],
            'bytes_descargados': self.estadisticas['bytes_descargados'],
            'errores': self.estadisticas['errores'],
            'tiempo_total': self.estadisticas.get('tiempo_total', 0),
            'velocidad_promedio': (
                self.estadisticas['bytes_descargados'] / 
                (time.time() - self.estadisticas['inicio'])
            ) if self.estadisticas['bytes_descargados'] > 0 else 0
        }

def comprimir_carpeta(carpeta_origen: Union[str, Path], archivo_zip: str) -> None:
    """Comprime una carpeta en un archivo ZIP"""
    carpeta_origen = Path(carpeta_origen)
    with zipfile.ZipFile(archivo_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in carpeta_origen.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(carpeta_origen)
                zipf.write(file_path, arcname)

def mostrar_estructura_directorio(path: Union[str, Path], prefix: str = "") -> List[str]:
    """Genera una representación en texto de la estructura de directorios"""
    path = Path(path)
    if not path.is_dir():
        return []
    
    output = []
    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
    
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        node = "└──" if is_last else "├──"
        output.append(f"{prefix}{node} {item.name}")
        
        if item.is_dir():
            nuevo_prefix = prefix + ("    " if is_last else "│   ")
            output.extend(mostrar_estructura_directorio(item, nuevo_prefix))
    
    return output

def formatear_tamano(bytes: int) -> str:
    """Formatea un tamaño en bytes a una representación legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"

def configurar_pagina():
    """Configura la página de Streamlit"""
    st.set_page_config(
        page_title="Web Scraper Pro",
        page_icon="🌐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Cargar CSS personalizado
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .stProgress > div > div {
            background-color: #00acee;
        }
        .stButton > button {
            width: 100%;
            background-color: #00acee;
            color: white;
        }
        .success-message {
            padding: 1rem;
            background-color: #d4edda;
            color: #155724;
            border-radius: 0.25rem;
            margin: 1rem 0;
        }
        .error-message {
            padding: 1rem;
            background-color: #f8d7da;
            color: #721c24;
            border-radius: 0.25rem;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    """Función principal de la aplicación"""
    configurar_pagina()
    
    st.title("Web Scraper Pro 🌐")
    st.write("Herramienta profesional para la descarga y almacenamiento local de sitios web completos.")

    # Configuración en la barra lateral
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        mantener_estructura = st.checkbox("📁 Mantener estructura de directorios", value=True)
        incluir_imagenes = st.checkbox("🖼️ Incluir imágenes", value=True)
        incluir_css = st.checkbox("🎨 Incluir CSS", value=True)
        incluir_js = st.checkbox("⚡ Incluir JavaScript", value=True)
        
        st.header("🔧 Configuración Avanzada")
        max_profundidad = st.slider(
            "🔄 Profundidad máxima", 
            min_value=1, 
            max_value=5, 
            value=1,
            help="Número máximo de niveles de profundidad para la descarga"
        )
        timeout = st.slider(
            "⏱️ Timeout (segundos)", 
            min_value=10, 
            max_value=60, 
            value=30,
            help="Tiempo máximo de espera para cada recurso"
        )
        
        st.markdown("---")
        st.markdown("### 📊 Estadísticas de uso")
        if 'total_descargas' not in st.session_state:
            st.session_state.total_descargas = 0
        st.metric("Total de descargas", st.session_state.total_descargas)

    # Contenedor principal
    with st.container():
        # Entrada de URL con validación
        url = st.text_input(
            "🌐 URL del sitio web:",
            placeholder="https://ejemplo.com",
            help="Introduce la URL completa del sitio web a descargar"
        )
        
        # Validación básica de URL
        url_valida = False
        if url:
            if not url.startswith(('http://', 'https://')):
                st.warning("⚠️ La URL debe comenzar con http:// o https://")
            else:
                url_valida = True

        # Columnas para botones de acción
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

        if limpiar_cache:
            try:
                shutil.rmtree('temp_download', ignore_errors=True)
                st.success("🧹 Caché limpiado correctamente")
            except Exception as e:
                st.error(f"❌ Error al limpiar caché: {str(e)}")

        if iniciar_descarga and url_valida:
            try:
                # Crear carpeta temporal
                carpeta_temp = Path("temp_download")
                if carpeta_temp.exists():
                    shutil.rmtree(carpeta_temp)
                carpeta_temp.mkdir(parents=True)

                # Configurar contenedores para progreso y estado
                progress_container = st.empty()
                status_container = st.empty()
                stats_container = st.empty()

                with progress_container:
                    progress_bar = st.progress(0)

                # Iniciar proceso de descarga
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

                # Mostrar estado inicial
                status_container.info("🚀 Iniciando descarga...")

                # Ejecutar descarga
                if scraper.descargar_pagina(progress_bar, status_container):
                    # Actualizar contador de descargas
                    st.session_state.total_descargas += 1
                    
                    # Obtener estadísticas
                    stats = scraper.obtener_estadisticas()
                    
                    # Mostrar resumen
                    st.success("✅ ¡Descarga completada exitosamente!")
                    
                    # Mostrar estadísticas en columnas
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(
                            "📁 Archivos",
                            stats['archivos_procesados']
                        )
                    with col2:
                        st.metric(
                            "💾 Tamaño Total",
                            formatear_tamano(stats['bytes_descargados'])
                        )
                    with col3:
                        st.metric(
                            "⏱️ Tiempo Total",
                            f"{stats['tiempo_total']:.2f}s"
                        )
                    with col4:
                        st.metric(
                            "🔄 Velocidad",
                            f"{formatear_tamano(stats['velocidad_promedio'])}/s"
                        )

                    # Mostrar estructura de directorios
                    with st.expander("📂 Estructura de archivos", expanded=True):
                        estructura = mostrar_estructura_directorio(carpeta_temp)
                        st.code("\n".join(estructura))

                    # Crear y ofrecer descarga del ZIP
                    nombre_zip = "sitio_web.zip"
                    comprimir_carpeta(carpeta_temp, nombre_zip)
                    
                    with open(nombre_zip, "rb") as fp:
                        st.download_button(
                            label="📦 Descargar ZIP",
                            data=fp,
                            file_name=nombre_zip,
                            mime="application/zip",
                            help="Descargar el sitio web completo en formato ZIP"
                        )
                        
                    # Guardar log de la descarga
                    log_entry = {
                        "fecha": datetime.now().isoformat(),
                        "url": url,
                        "estadisticas": stats
                    }
                    
                    with open("descargas.log", "a") as f:
                        json.dump(log_entry, f)
                        f.write("\n")
                else:
                    st.error("❌ Error durante la descarga del sitio")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.error(f"Error en la aplicación: {str(e)}")
                
            finally:
                # Limpiar contenedores temporales
                progress_container.empty()
                status_container.empty()

    # Pie de página
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
        <p>Desarrollado por <a href="https://github.com/bladealex9848">Alexander Oviedo Fadul</a> 
        | <a href="https://github.com/bladealex9848/web-scraper-pro">GitHub</a> 
        | <a href="https://alexanderoviedofadul.dev">Website</a></p>
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
