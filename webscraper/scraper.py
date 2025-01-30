import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
from urllib.parse import urljoin, urlparse
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class WebScraper:
    def __init__(self, base_url, carpeta_destino, **kwargs):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.carpeta_destino = carpeta_destino
        self.session = requests.Session()
        self.archivos_descargados = set()
        self.total_archivos = 0
        self.tamano_total = 0
        self.tiempo_total = 0
        
        # Configuraciones
        self.mantener_estructura = kwargs.get('mantener_estructura', True)
        self.incluir_imagenes = kwargs.get('incluir_imagenes', True)
        self.incluir_css = kwargs.get('incluir_css', True)
        self.incluir_js = kwargs.get('incluir_js', True)
        
        # Headers para simular un navegador
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        })

    def obtener_ruta_relativa(self, url):
        """Convierte una URL en una ruta de archivo relativa"""
        if not url:
            return None
        
        try:
            # Manejar URLs relativas
            url_completa = urljoin(self.base_url, url)
            parsed = urlparse(url_completa)
            
            # Solo procesar recursos del mismo dominio
            if parsed.netloc and parsed.netloc != self.domain:
                return None
                
            path = parsed.path
            if not path or path == '/':
                path = 'index.html'
            elif path.endswith('/'):
                path += 'index.html'
            
            # Limpiar la ruta
            return path.lstrip('/')
        except Exception as e:
            logging.error(f"Error procesando URL {url}: {str(e)}")
            return None

    def descargar_recurso(self, url, ruta_destino):
        """Descarga un recurso y lo guarda en la ruta especificada"""
        if not url or url in self.archivos_descargados:
            return None
            
        try:
            response = self.session.get(urljoin(self.base_url, url), stream=True)
            response.raise_for_status()
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
            
            # Guardar archivo
            tamano = 0
            with open(ruta_destino, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tamano += len(chunk)
                        f.write(chunk)
            
            self.archivos_descargados.add(url)
            self.total_archivos += 1
            self.tamano_total += tamano / (1024 * 1024)  # Convertir a MB
            
            return True
        except Exception as e:
            logging.error(f"Error descargando {url}: {str(e)}")
            return False

    def descargar_pagina(self, progress_bar=None, status_text=None):
        """Descarga una página web completa y sus recursos"""
        tiempo_inicio = time.time()
        
        try:
            # Descargar página principal
            response = self.session.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Definir elementos a procesar según configuración
            elementos_a_procesar = {}
            if self.incluir_imagenes:
                elementos_a_procesar.update({
                    'img': ['src', 'data-src'],
                    'source': ['src', 'srcset'],
                })
            if self.incluir_css:
                elementos_a_procesar['link'] = ['href']
            if self.incluir_js:
                elementos_a_procesar['script'] = ['src']

            # Contar total de elementos
            total_elementos = sum(
                len(soup.find_all(tag)) 
                for tag in elementos_a_procesar
            )
            elementos_procesados = 0

            # Procesar elementos
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                
                for tag, atributos in elementos_a_procesar.items():
                    for elemento in soup.find_all(tag):
                        for attr in atributos:
                            if elemento.has_attr(attr):
                                url = elemento[attr]
                                ruta_relativa = self.obtener_ruta_relativa(url)
                                
                                if ruta_relativa:
                                    ruta_completa = os.path.join(
                                        self.carpeta_destino, 
                                        ruta_relativa
                                    )
                                    futures.append(
                                        executor.submit(
                                            self.descargar_recurso, 
                                            url, 
                                            ruta_completa
                                        )
                                    )
                                    elemento[attr] = ruta_relativa

                # Esperar completación y actualizar progreso
                for future in as_completed(futures):
                    elementos_procesados += 1
                    if progress_bar:
                        progress_bar.progress(elementos_procesados / total_elementos)
                    if status_text:
                        status_text.text(
                            f"Procesando: {elementos_procesados}/{total_elementos} elementos"
                        )

            # Guardar HTML final
            ruta_index = os.path.join(self.carpeta_destino, 'index.html')
            with open(ruta_index, 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()))

            self.tiempo_total = time.time() - tiempo_inicio
            return True

        except Exception as e:
            logging.error(f"Error al descargar la página: {str(e)}")
            return False
