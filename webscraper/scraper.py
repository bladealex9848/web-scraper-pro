"""
Módulo principal del Web Scraper Pro con soporte para descarga recursiva multinivel.
"""

import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
from pathlib import Path
import threading
import logging
from urllib.parse import urljoin, urlparse
import concurrent.futures
import time
from typing import Optional, Dict, Set, List
import hashlib
from dataclasses import dataclass, field
from queue import Queue
import re

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PageContext:
    """Contexto de una página para descarga recursiva."""
    url: str
    nivel: int
    ruta_destino: Path
    urls_procesadas: Set[str] = field(default_factory=set)

class WebScraper:
    """Clase principal para el scraping de sitios web con soporte multinivel."""
    
    def __init__(self, base_url: str, carpeta_destino: str, **kwargs):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.carpeta_destino = Path(carpeta_destino)
        self.session = self._configurar_session()
        self.archivos_descargados = set()
        self.urls_procesadas = set()
        self.lock = threading.Lock()
        
        # Estadísticas
        self.estadisticas = {
            'inicio': time.time(),
            'archivos_procesados': 0,
            'bytes_descargados': 0,
            'errores': 0,
            'tiempo_total': 0
        }
        
        # Configuración
        self.config = {
            'mantener_estructura': kwargs.get('mantener_estructura', True),
            'incluir_imagenes': kwargs.get('incluir_imagenes', True),
            'incluir_css': kwargs.get('incluir_css', True),
            'incluir_js': kwargs.get('incluir_js', True),
            'max_profundidad': kwargs.get('max_profundidad', 1),
            'timeout': kwargs.get('timeout', 30)
        }
        
        # Cola de procesamiento para URLs
        self.cola_urls = Queue()

    def _configurar_session(self) -> requests.Session:
        """Configura la sesión HTTP con opciones optimizadas."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        return session

    def es_url_interna(self, url: str) -> bool:
        """Verifica si una URL pertenece al mismo dominio."""
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.domain or not parsed.netloc
        except Exception:
            return False

    def obtener_ruta_relativa(self, url: str, nivel: int = 0) -> Optional[str]:
        """Convierte una URL en una ruta de archivo relativa."""
        if not url:
            return None
            
        try:
            url_completa = urljoin(self.base_url, url)
            parsed = urlparse(url_completa)
            
            if parsed.netloc and parsed.netloc != self.domain:
                return None
                
            # Limpiar y procesar la ruta
            path = parsed.path
            if not path or path == '/':
                path = 'index.html'
            elif path.endswith('/'):
                path += 'index.html'
            elif not any(path.lower().endswith(ext) for ext in ['.html', '.htm', '.php', '.asp', '.aspx']):
                path = os.path.join(path, 'index.html')
            
            # Sanitizar el nombre del archivo
            path = re.sub(r'[<>:"/\\|?*]', '_', path.lstrip('/'))
            
            if nivel > 0:
                # Crear estructura de directorios para niveles
                partes = path.split('/')
                if len(partes) > 1:
                    path = os.path.join(f"nivel_{nivel}", *partes)
                else:
                    path = os.path.join(f"nivel_{nivel}", path)
            
            return path
            
        except Exception as e:
            logger.error(f"Error procesando URL {url}: {str(e)}")
            return None

    def descargar_recurso(self, url: str, nivel: int = 0) -> Optional[str]:
        """Descarga un recurso y lo guarda en el sistema de archivos."""
        if not url or url in self.archivos_descargados:
            return None
            
        try:
            ruta_relativa = self.obtener_ruta_relativa(url, nivel)
            if not ruta_relativa:
                return None
                
            ruta_completa = self.carpeta_destino / ruta_relativa
            
            # Crear directorio si no existe
            ruta_completa.parent.mkdir(parents=True, exist_ok=True)
            
            # Descargar el recurso
            response = self.session.get(
                urljoin(self.base_url, url),
                stream=True,
                timeout=self.config['timeout']
            )
            response.raise_for_status()
            
            with open(ruta_completa, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        with self.lock:
                            self.estadisticas['bytes_descargados'] += len(chunk)
            
            with self.lock:
                self.archivos_descargados.add(url)
                self.estadisticas['archivos_procesados'] += 1
            
            return ruta_relativa
            
        except Exception as e:
            logger.error(f"Error al descargar {url}: {str(e)}")
            with self.lock:
                self.estadisticas['errores'] += 1
            return None

    def procesar_enlaces(self, soup: BeautifulSoup, nivel_actual: int) -> List[str]:
        """Procesa y extrae enlaces válidos de una página."""
        enlaces = []
        if nivel_actual >= self.config['max_profundidad']:
            return enlaces

        for a in soup.find_all('a', href=True):
            href = a['href']
            url_completa = urljoin(self.base_url, href)
            
            if (self.es_url_interna(url_completa) and 
                url_completa not in self.urls_procesadas):
                enlaces.append(url_completa)
                
        return enlaces

    def procesar_pagina(self, url: str, nivel: int) -> None:
        """Procesa una página y sus recursos."""
        if url in self.urls_procesadas:
            return

        try:
            with self.lock:
                self.urls_procesadas.add(url)

            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Procesar recursos según configuración
            if self.config['incluir_imagenes']:
                for img in soup.find_all('img', src=True):
                    self.descargar_recurso(img['src'], nivel)

            if self.config['incluir_css']:
                for css in soup.find_all('link', rel='stylesheet'):
                    if css.get('href'):
                        self.descargar_recurso(css['href'], nivel)

            if self.config['incluir_js']:
                for js in soup.find_all('script', src=True):
                    self.descargar_recurso(js['src'], nivel)

            # Guardar la página actual
            ruta_relativa = self.obtener_ruta_relativa(url, nivel)
            if ruta_relativa:
                ruta_completa = self.carpeta_destino / ruta_relativa
                ruta_completa.parent.mkdir(parents=True, exist_ok=True)
                with open(ruta_completa, 'w', encoding='utf-8') as f:
                    f.write(str(soup.prettify()))

            # Procesar enlaces para el siguiente nivel
            if nivel < self.config['max_profundidad']:
                enlaces = self.procesar_enlaces(soup, nivel)
                for enlace in enlaces:
                    if enlace not in self.urls_procesadas:
                        self.cola_urls.put((enlace, nivel + 1))

        except Exception as e:
            logger.error(f"Error procesando página {url}: {str(e)}")
            with self.lock:
                self.estadisticas['errores'] += 1

    def descargar_pagina(self, progress_bar=None, status_text=None) -> bool:
        """Inicia el proceso de descarga recursiva del sitio web."""
        try:
            self.cola_urls.put((self.base_url, 0))
            total_procesado = 0

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                
                while not self.cola_urls.empty():
                    url, nivel = self.cola_urls.get()
                    if url not in self.urls_procesadas:
                        futures.append(
                            executor.submit(self.procesar_pagina, url, nivel)
                        )
                        
                        if status_text:
                            status_text.text(f"Procesando nivel {nivel}: {url}")

                    total_procesado += 1
                    if progress_bar:
                        progress_bar.progress(min(total_procesado / (total_procesado + self.cola_urls.qsize()), 1.0))

                concurrent.futures.wait(futures)

            self.estadisticas['tiempo_total'] = time.time() - self.estadisticas['inicio']
            return True

        except Exception as e:
            logger.error(f"Error en la descarga: {str(e)}")
            return False

    def obtener_estadisticas(self) -> Dict:
        """Retorna las estadísticas de la descarga."""
        return {
            'archivos_procesados': self.estadisticas['archivos_procesados'],
            'bytes_descargados': self.estadisticas['bytes_descargados'],
            'errores': self.estadisticas['errores'],
            'tiempo_total': self.estadisticas['tiempo_total'],
            'paginas_procesadas': len(self.urls_procesadas),
            'velocidad_promedio': (
                self.estadisticas['bytes_descargados'] / 
                max(self.estadisticas['tiempo_total'], 0.001)
            )
        }