"""
Excepciones personalizadas para el Web Scraper Pro.
Define una jerarquía de excepciones específicas para manejar diferentes tipos de errores.
"""

class WebScraperError(Exception):
    """Clase base para excepciones del Web Scraper."""
    def __init__(self, message: str = None, *args, **kwargs):
        self.message = message or "Error en Web Scraper"
        super().__init__(self.message, *args)

class URLError(WebScraperError):
    """Excepción para errores relacionados con URLs."""
    def __init__(self, url: str, reason: str = None):
        self.url = url
        self.reason = reason
        message = f"Error en URL '{url}': {reason}" if reason else f"URL inválida: {url}"
        super().__init__(message)

class DownloadError(WebScraperError):
    """Excepción para errores durante la descarga de recursos."""
    def __init__(self, url: str, status_code: int = None, reason: str = None):
        self.url = url
        self.status_code = status_code
        self.reason = reason
        message = f"Error descargando '{url}'"
        if status_code:
            message += f" (Status: {status_code})"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class FileSystemError(WebScraperError):
    """Excepción para errores de sistema de archivos."""
    def __init__(self, path: str, operation: str, reason: str = None):
        self.path = path
        self.operation = operation
        self.reason = reason
        message = f"Error de sistema de archivos en '{path}' durante {operation}"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class SecurityError(WebScraperError):
    """Excepción para violaciones de seguridad."""
    def __init__(self, reason: str, resource: str = None):
        self.reason = reason
        self.resource = resource
        message = f"Error de seguridad: {reason}"
        if resource:
            message += f" (Recurso: {resource})"
        super().__init__(message)

class ConfigurationError(WebScraperError):
    """Excepción para errores de configuración."""
    def __init__(self, parameter: str, reason: str = None):
        self.parameter = parameter
        self.reason = reason
        message = f"Error de configuración en '{parameter}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class ResourceError(WebScraperError):
    """Excepción para errores relacionados con recursos específicos."""
    def __init__(self, resource_type: str, identifier: str, reason: str = None):
        self.resource_type = resource_type
        self.identifier = identifier
        self.reason = reason
        message = f"Error en recurso {resource_type} '{identifier}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class CacheError(WebScraperError):
    """Excepción para errores del sistema de caché."""
    def __init__(self, operation: str, reason: str = None):
        self.operation = operation
        self.reason = reason
        message = f"Error de caché durante {operation}"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class ValidationError(WebScraperError):
    """Excepción para errores de validación."""
    def __init__(self, field: str, value: str, reason: str = None):
        self.field = field
        self.value = value
        self.reason = reason
        message = f"Error de validación en campo '{field}' con valor '{value}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class RateLimitError(WebScraperError):
    """Excepción para errores de límite de tasa."""
    def __init__(self, limit: int, period: str, reset_time: str = None):
        self.limit = limit
        self.period = period
        self.reset_time = reset_time
        message = f"Límite de tasa excedido ({limit} peticiones por {period})"
        if reset_time:
            message += f". Reinicio en {reset_time}"
        super().__init__(message)