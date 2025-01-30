# Documentación API - Web Scraper Pro

## Índice
1. [Visión General](#visión-general)
2. [Componentes Principales](#componentes-principales)
3. [Guía de Uso](#guía-de-uso)
4. [Referencia API](#referencia-api)
5. [Consideraciones Técnicas](#consideraciones-técnicas)
6. [Ejemplos](#ejemplos)

## Visión General

Web Scraper Pro proporciona una API robusta para la descarga y procesamiento de sitios web completos. La arquitectura está diseñada con énfasis en:

- **Rendimiento**: Procesamiento asíncrono y gestión eficiente de recursos
- **Seguridad**: Validación estricta y sanitización de entrada
- **Escalabilidad**: Diseño modular y cache inteligente
- **Mantenibilidad**: Código bien documentado y pruebas exhaustivas

## Componentes Principales

### `WebScraper`

Clase principal para la gestión de descargas.

```python
from webscraper import WebScraper

scraper = WebScraper(
    base_url="https://ejemplo.com",
    carpeta_destino="./descarga",
    **opciones
)
```

#### Opciones de Configuración

| Parámetro | Tipo | Descripción | Valor por Defecto |
|-----------|------|-------------|-------------------|
| `mantener_estructura` | bool | Preservar estructura de directorios | `True` |
| `incluir_imagenes` | bool | Descargar imágenes | `True` |
| `incluir_css` | bool | Descargar archivos CSS | `True` |
| `incluir_js` | bool | Descargar archivos JavaScript | `True` |
| `max_profundidad` | int | Profundidad máxima de descarga | `1` |
| `timeout` | int | Tiempo máximo de espera (segundos) | `30` |

### Sistema de Caché

Implementa un mecanismo de caché inteligente para optimizar descargas repetidas:

```python
class ResourceManager:
    """Gestiona la descarga y almacenamiento de recursos."""
    
    def get_resource(self, url: str) -> Optional[bytes]:
        """
        Obtiene un recurso, utilizando caché si está disponible.
        
        Args:
            url: URL del recurso a descargar
            
        Returns:
            Optional[bytes]: Contenido del recurso o None si hay error
        """
```

## Guía de Uso

### Uso Básico

```python
# Inicializar scraper
scraper = WebScraper("https://ejemplo.com", "./descarga")

# Iniciar descarga
if scraper.descargar_pagina():
    print("Descarga completada")
```

### Uso Avanzado

```python
# Configuración personalizada
scraper = WebScraper(
    base_url="https://ejemplo.com",
    carpeta_destino="./descarga",
    mantener_estructura=True,
    incluir_imagenes=True,
    max_profundidad=2,
    timeout=45
)

# Monitoreo de progreso
def actualizar_progreso(progreso: float):
    print(f"Progreso: {progreso:.2f}%")

# Iniciar descarga con callbacks
scraper.descargar_pagina(
    progress_callback=actualizar_progreso
)

# Obtener estadísticas
stats = scraper.obtener_estadisticas()
print(f"Archivos procesados: {stats['archivos_procesados']}")
```

## Referencia API

### Métodos Principales

#### `descargar_pagina()`

```python
def descargar_pagina(
    self,
    progress_bar=None,
    status_text=None
) -> bool:
    """
    Descarga una página web completa y sus recursos.

    Args:
        progress_bar: Barra de progreso de Streamlit (opcional)
        status_text: Contenedor de texto para estado (opcional)

    Returns:
        bool: True si la descarga fue exitosa
    """
```

#### `descargar_recurso()`

```python
def descargar_recurso(
    self,
    url: str
) -> Optional[str]:
    """
    Descarga un recurso específico.

    Args:
        url: URL del recurso a descargar

    Returns:
        Optional[str]: Ruta relativa del recurso descargado
    """
```

## Consideraciones Técnicas

### Seguridad

1. **Validación de URLs**
   - Esquemas permitidos: http, https
   - Sanitización de caracteres especiales
   - Prevención de path traversal

2. **Límites y Restricciones**
   - Tamaño máximo de archivo: 50MB
   - Tamaño total máximo: 500MB
   - Tipos de archivo permitidos configurables

### Rendimiento

1. **Optimizaciones**
   - Descarga asíncrona de recursos
   - Sistema de caché inteligente
   - Reutilización de conexiones HTTP

2. **Control de Recursos**
   - Límite de conexiones concurrentes
   - Timeouts configurables
   - Gestión de memoria eficiente

## Ejemplos

### Descarga con Configuración Personalizada

```python
from webscraper import WebScraper, SecurityConfig

# Configuración personalizada
config = {
    'mantener_estructura': True,
    'incluir_imagenes': True,
    'incluir_css': True,
    'incluir_js': False,
    'max_profundidad': 2,
    'timeout': 30
}

# Inicializar scraper
scraper = WebScraper(
    base_url="https://ejemplo.com",
    carpeta_destino="./descarga",
    **config
)

# Ejecutar descarga
try:
    if scraper.descargar_pagina():
        print("Descarga exitosa")
        stats = scraper.obtener_estadisticas()
        print(f"Total archivos: {stats['archivos_procesados']}")
        print(f"Tamaño total: {stats['bytes_descargados']/1024/1024:.2f} MB")
except WebScraperError as e:
    print(f"Error: {str(e)}")
```

### Manejo de Eventos y Logging

```python
import logging
from webscraper import WebScraper, setup_logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Callback de progreso
def on_progress(progress: float):
    logger.info(f"Progreso: {progress:.2f}%")

# Callback de error
def on_error(error: str):
    logger.error(f"Error: {error}")

# Inicializar y ejecutar
scraper = WebScraper("https://ejemplo.com", "./descarga")
scraper.descargar_pagina(
    progress_callback=on_progress,
    error_callback=on_error
)
```

---

Para más información y ejemplos, consulte la [documentación completa](https://github.com/bladealex9848/web-scraper-pro/docs).