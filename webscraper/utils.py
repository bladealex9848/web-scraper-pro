"""
Utilidades y funciones auxiliares para el Web Scraper Pro.
Proporciona funcionalidades comunes utilizadas en todo el proyecto.
"""

import os
import re
import hashlib
import mimetypes
from pathlib import Path
from typing import Union, Optional, Dict, List
from urllib.parse import urlparse, urljoin
import logging
from datetime import datetime
import json
from .config import SecurityConfig, ScraperConfig
from .exceptions import WebScraperError

logger = logging.getLogger(__name__)

def validar_url(url: str) -> bool:
    """
    Valida que una URL sea segura y tenga un formato válido.
    
    Args:
        url (str): URL a validar
        
    Returns:
        bool: True si la URL es válida, False en caso contrario
    """
    try:
        parsed = urlparse(url)
        return all([
            parsed.scheme in ScraperConfig.VALID_SCHEMES,
            parsed.netloc,
            not any(c in SecurityConfig.INVALID_CHARS for c in url),
            len(url) <= 2048  # Longitud máxima estándar
        ])
    except Exception as e:
        logger.error(f"Error validando URL {url}: {str(e)}")
        return False

def sanitizar_nombre_archivo(nombre: str) -> str:
    """
    Limpia y sanitiza un nombre de archivo para uso seguro en el sistema de archivos.
    
    Args:
        nombre (str): Nombre de archivo original
        
    Returns:
        str: Nombre de archivo sanitizado
    """
    # Eliminar caracteres no permitidos
    nombre_limpio = re.sub(f'[{SecurityConfig.INVALID_CHARS}]', '_', nombre)
    
    # Limitar longitud
    if len(nombre_limpio) > 255:
        base, ext = os.path.splitext(nombre_limpio)
        nombre_limpio = base[:255-len(ext)] + ext
    
    return nombre_limpio.strip('._')

def obtener_extension_segura(url: str) -> Optional[str]:
    """
    Obtiene la extensión de archivo de una URL de forma segura.
    
    Args:
        url (str): URL del recurso
        
    Returns:
        Optional[str]: Extensión del archivo o None si no es válida
    """
    try:
        _, ext = os.path.splitext(urlparse(url).path)
        ext = ext.lower()
        
        if ext in SecurityConfig.BLOCKED_EXTENSIONS:
            logger.warning(f"Extensión bloqueada: {ext}")
            return None
            
        if ext in ScraperConfig.SUPPORTED_EXTENSIONS:
            return ext
            
        return None
    except Exception as e:
        logger.error(f"Error obteniendo extensión: {str(e)}")
        return None

def generar_hash_archivo(contenido: bytes) -> str:
    """
    Genera un hash SHA-256 del contenido de un archivo.
    
    Args:
        contenido (bytes): Contenido del archivo
        
    Returns:
        str: Hash SHA-256 en formato hexadecimal
    """
    return hashlib.sha256(contenido).hexdigest()

def formatear_tamano(bytes: int) -> str:
    """
    Formatea un tamaño en bytes a una representación legible.
    
    Args:
        bytes (int): Tamaño en bytes
        
    Returns:
        str: Tamaño formateado (ej: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"

def crear_estructura_directorios(ruta: Union[str, Path]) -> None:
    """
    Crea una estructura de directorios de forma segura.
    
    Args:
        ruta (Union[str, Path]): Ruta a crear
    
    Raises:
        WebScraperError: Si hay un error creando los directorios
    """
    try:
        Path(ruta).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise WebScraperError(f"Error creando directorios: {str(e)}")

def obtener_tipo_mime(ruta: Union[str, Path]) -> str:
    """
    Obtiene el tipo MIME de un archivo de forma segura.
    
    Args:
        ruta (Union[str, Path]): Ruta al archivo
        
    Returns:
        str: Tipo MIME del archivo
    """
    tipo, _ = mimetypes.guess_type(str(ruta))
    return tipo or 'application/octet-stream'

def es_archivo_seguro(nombre: str, tamano: int) -> bool:
    """
    Verifica si un archivo cumple con las políticas de seguridad.
    
    Args:
        nombre (str): Nombre del archivo
        tamano (int): Tamaño en bytes
        
    Returns:
        bool: True si el archivo es seguro, False en caso contrario
    """
    extension = obtener_extension_segura(nombre)
    return all([
        extension is not None,
        tamano <= SecurityConfig.MAX_FILE_SIZE,
        not any(c in nombre for c in SecurityConfig.INVALID_CHARS)
    ])

def guardar_estadisticas(stats: Dict) -> None:
    """
    Guarda estadísticas de uso en un archivo JSON.
    
    Args:
        stats (Dict): Diccionario con estadísticas
    """
    try:
        stats['timestamp'] = datetime.now().isoformat()
        with open('stats.json', 'a') as f:
            json.dump(stats, f)
            f.write('\n')
    except Exception as e:
        logger.error(f"Error guardando estadísticas: {str(e)}")

def mostrar_estructura_directorio(path: Union[str, Path], prefix: str = "") -> List[str]:
    """
    Genera una representación en texto de la estructura de directorios.
    
    Args:
        path (Union[str, Path]): Ruta a mostrar
        prefix (str): Prefijo para la indentación
        
    Returns:
        List[str]: Lista de líneas representando la estructura
    """
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