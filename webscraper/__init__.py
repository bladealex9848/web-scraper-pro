"""
Web Scraper Pro - Módulo principal para descarga y procesamiento de sitios web.

Este módulo proporciona funcionalidades para la descarga completa de sitios web,
incluyendo recursos estáticos y manteniendo la estructura original del sitio.
"""

import logging
from pathlib import Path
from typing import Dict, Any
from .config import VERSION, LogConfig, ENV
from .exceptions import WebScraperError
from .scraper import WebScraper

# Configuración del logging
def setup_logging() -> None:
    """Configura el sistema de logging con los parámetros definidos."""
    logging.basicConfig(
        level=getattr(logging, LogConfig.LEVEL),
        format=LogConfig.FORMAT,
        datefmt=LogConfig.DATE_FORMAT,
        handlers=[
            logging.FileHandler(LogConfig.LOG_FILE),
            logging.StreamHandler()
        ]
    )

    # Configurar logger de errores
    error_handler = logging.FileHandler(LogConfig.ERROR_LOG)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LogConfig.FORMAT))
    
    # Agregar handler al logger raíz
    logging.getLogger('').addHandler(error_handler)

# Inicialización del módulo
setup_logging()
logger = logging.getLogger(__name__)

logger.info(f"Iniciando Web Scraper Pro v{VERSION} en modo {ENV}")

# Validación del entorno
def validate_environment() -> Dict[str, Any]:
    """
    Valida el entorno de ejecución y retorna la configuración del sistema.
    
    Returns:
        Dict[str, Any]: Diccionario con la configuración del entorno
    
    Raises:
        WebScraperError: Si hay problemas con la configuración del entorno
    """
    try:
        env_config = {
            'version': VERSION,
            'environment': ENV,
            'python_version': platform.python_version(),
            'system': platform.system(),
            'encoding': sys.getfilesystemencoding()
        }
        
        # Verificar permisos de directorios
        paths_to_check = [
            LogConfig.LOG_FILE.parent,
            LogConfig.ERROR_LOG.parent
        ]
        
        for path in paths_to_check:
            if not os.access(path, os.W_OK):
                raise WebScraperError(f"Sin permisos de escritura en {path}")
        
        return env_config
        
    except Exception as e:
        logger.critical(f"Error en la validación del entorno: {str(e)}")
        raise WebScraperError(f"Error de inicialización: {str(e)}")

# Exportar clases y funciones principales
__all__ = [
    'WebScraper',
    'WebScraperError',
    'VERSION',
    'setup_logging',
    'validate_environment'
]

# Metadatos del paquete
__version__ = VERSION
__author__ = "Alexander Oviedo Fadul"
__email__ = "info@alexanderoviedofadul.dev"
__license__ = "MIT"
__description__ = "Herramienta profesional para la descarga y procesamiento de sitios web completos"

# Validación inicial del entorno
try:
    env_info = validate_environment()
    logger.info(f"Configuración del entorno: {env_info}")
except WebScraperError as e:
    logger.critical(f"Error crítico durante la inicialización: {str(e)}")
    raise