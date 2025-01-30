"""
Web Scraper Pro - Módulo principal
"""

import logging
from pathlib import Path
import os
import sys
from typing import Dict, Any
import platform

# Configuración de versión
VERSION = "1.0.0"

# Configuración de rutas base
BASE_DIR = Path(__file__).parent.parent
TEMP_DIR = BASE_DIR / "temp_download"
LOGS_DIR = BASE_DIR / "logs"

# Asegurar que los directorios existan
TEMP_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Configuración del logging
def setup_logging() -> None:
    """Configura el sistema de logging."""
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOGS_DIR / "webscraper.log"),
                logging.StreamHandler()
            ]
        )
    except Exception as e:
        print(f"Error configurando logging: {str(e)}")
        # Configuración fallback
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

# Inicialización del logger
setup_logging()
logger = logging.getLogger(__name__)

# Log de inicio
logger.info(f"Iniciando Web Scraper Pro v{VERSION}")

# Validación simple del entorno
def get_environment_info() -> Dict[str, Any]:
    """
    Recopila información básica del entorno.
    
    Returns:
        Dict[str, Any]: Diccionario con información del entorno
    """
    return {
        'version': VERSION,
        'python_version': platform.python_version(),
        'system': platform.system(),
        'machine': platform.machine(),
        'encoding': sys.getfilesystemencoding(),
        'temp_dir': str(TEMP_DIR),
        'logs_dir': str(LOGS_DIR)
    }

# Exportar elementos principales
from .scraper import WebScraper

__all__ = ['WebScraper', 'VERSION', 'get_environment_info']

# Metadata del paquete
__version__ = VERSION
__author__ = "Alexander Oviedo Fadul"
__email__ = "info@alexanderoviedofadul.dev"
__license__ = "MIT"

# Registro de información del entorno
try:
    env_info = get_environment_info()
    logger.info(f"Información del entorno: {env_info}")
except Exception as e:
    logger.warning(f"No se pudo obtener información completa del entorno: {str(e)}")