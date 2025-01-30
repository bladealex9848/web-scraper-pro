"""
Configuración centralizada para el Web Scraper Pro.
Contiene todas las constantes y configuraciones del sistema.
"""

import os
from pathlib import Path
from typing import Dict, Set

# Versión del software
VERSION = "1.0.0"

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent
TEMP_DIR = BASE_DIR / "temp_download"
LOGS_DIR = BASE_DIR / "logs"

# Asegurar que los directorios existan
TEMP_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Configuración del scraper
class ScraperConfig:
    """Configuraciones principales del Web Scraper"""
    
    # Timeouts y límites
    REQUEST_TIMEOUT = 30  # segundos
    MAX_RETRIES = 3
    CHUNK_SIZE = 8192  # bytes
    MAX_WORKERS = 5
    CACHE_EXPIRY = 3600  # 1 hora en segundos
    
    # Headers por defecto para requests
    DEFAULT_HEADERS: Dict[str, str] = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # Esquemas permitidos
    VALID_SCHEMES: Set[str] = {'http', 'https'}
    
    # Tipos de archivos soportados
    SUPPORTED_EXTENSIONS: Set[str] = {
        # Imágenes
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp',
        # Documentos
        '.html', '.htm',
        # Estilos
        '.css',
        # Scripts
        '.js',
        # Fuentes
        '.woff', '.woff2', '.ttf', '.eot',
        # Media
        '.mp4', '.webm', '.mp3', '.wav'
    }

# Configuración de logging
class LogConfig:
    """Configuración del sistema de logging"""
    
    LEVEL = "INFO"
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # Archivo de log principal
    LOG_FILE = LOGS_DIR / "webscraper.log"
    
    # Archivo de log para errores
    ERROR_LOG = LOGS_DIR / "error.log"
    
    # Rotación de logs
    MAX_BYTES = 10_000_000  # 10MB
    BACKUP_COUNT = 5

# Configuración de caché
class CacheConfig:
    """Configuración del sistema de caché"""
    
    ENABLED = True
    MAX_SIZE = 100_000_000  # 100MB
    EXPIRE_AFTER = 3600  # 1 hora
    CACHE_DIR = TEMP_DIR / "cache"

# Configuración de seguridad
class SecurityConfig:
    """Configuraciones de seguridad"""
    
    # Caracteres no permitidos en nombres de archivo
    INVALID_CHARS = '<>:"/\\|?*'
    
    # Extensiones bloqueadas
    BLOCKED_EXTENSIONS = {'.php', '.asp', '.aspx', '.jsp', '.exe'}
    
    # Límites de tamaño
    MAX_FILE_SIZE = 50_000_000  # 50MB
    MAX_TOTAL_SIZE = 500_000_000  # 500MB

# Variables de entorno
ENV = os.getenv('WEBSCRAPER_ENV', 'development')
DEBUG = ENV == 'development'

# Mensajes de error personalizados
ERROR_MESSAGES = {
    'invalid_url': "URL no válida o no soportada",
    'connection_error': "Error de conexión al servidor",
    'timeout_error': "Tiempo de espera agotado",
    'file_too_large': "El archivo excede el tamaño máximo permitido",
    'total_size_exceeded': "Se ha excedido el tamaño total permitido",
    'invalid_file_type': "Tipo de archivo no soportado",
    'permission_error': "Error de permisos al escribir archivo",
    'cache_error': "Error en el sistema de caché"
}