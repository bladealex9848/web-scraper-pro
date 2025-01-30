# Web Scraper Pro 🌐

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white&labelColor=101010)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white&labelColor=101010)](https://streamlit.io)
[![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-4-4B8BBE?style=for-the-badge&logo=python&logoColor=white&labelColor=101010)](https://www.crummy.com/software/BeautifulSoup/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge&labelColor=101010)](https://opensource.org/licenses/MIT)

Herramienta de alto rendimiento para descargar sitios web completos de forma local, implementada con arquitectura modular y una interfaz gráfica intuitiva en Streamlit.

## 🚀 Características Principales

### Capacidades Técnicas ⚡
- 📥 Descarga completa de sitios web
  - HTML, CSS, JavaScript
  - Imágenes y recursos multimedia
  - Mantenimiento de estructura original
- 🔄 Procesamiento asíncrono optimizado
- 💾 Sistema de caché inteligente
- 🗂️ Gestión eficiente de recursos

### Interfaz y Usabilidad 🎯
- 📊 Panel de control interactivo con Streamlit
- 📈 Barra de progreso en tiempo real
- 📁 Visualización jerárquica de directorios
- 🗜️ Exportación automática a ZIP

### Seguridad y Rendimiento 🛡️
- 🔒 Validación estricta de URLs
- 🌐 Restricción a dominio original
- 📝 Sistema de logging detallado
- ⚡ Optimización de recursos

## 📋 Requisitos del Sistema

### Requisitos Base
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Dependencias Principales
```plaintext
streamlit>=1.10.0
requests>=2.26.0
beautifulsoup4>=4.9.3
urllib3>=1.26.7
```

## 🔧 Instalación

### Instalación Rápida
```bash
# Clonar repositorio
git clone https://github.com/bladealex9848/web-scraper-pro.git

# Navegar al directorio
cd web-scraper-pro

# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🚀 Uso

### Iniciar Aplicación
```bash
# Lanzar interfaz Streamlit
streamlit run app.py

# Acceder vía navegador
http://localhost:8501
```

### Ejemplo de Uso Programático 💻
```python
from webscraper.scraper import WebScraper

# Inicializar scraper con configuración
scraper = WebScraper(
    base_url="https://ejemplo.com",
    carpeta_destino="./descarga"
)

# Iniciar proceso de descarga
scraper.descargar_pagina()
```

## 📁 Estructura del Proyecto

```plaintext
web-scraper-pro/
├── app.py                  # Aplicación principal Streamlit
├── webscraper/             # Módulo core de la aplicación
│   ├── __init__.py         # Inicialización del módulo
│   └── scraper.py          # Clase WebScraper
│   └── config.py           # Configuración de la aplicación
│   └── utils.py            # Utilidades y funciones auxiliares
│   └── exceptions.py       # Excepciones personalizadas
├── temp                    # Directorio temporal
├── logs/                   # Directorio para logs
└── temp_download/          # Directorio temporal para descargas  
├── tests/                  # Pruebas unitarias
│   └── test_scraper.py     # Pruebas para la clase WebScraper
├── static/                 # Pruebas unitarias
│   └── style.css           # Archivo CSS para la aplicación
├── docs/                   # Documentación del proyecto
│   └── API.md              # Documentación de la API
│   └── DEVELOPMENT.md      # Guía de desarrollo
├── requirements.txt        # Dependencias del proyecto
├── LICENSE                 # Licencia MIT
└── README.md               # Esta documentación
└── CHANGELOG.md            # Registro de cambios
└── .gitignore              # Archivos y directorios ignorados por Git
└── .streamlit/             # Configuración de Streamlit
    └── config.toml         # Configuración de Streamlit
```

## 🔒 Seguridad

### Medidas Implementadas
- ✅ Validación rigurosa de URLs
- 🔒 Restricción a dominio original
- 📝 Logging detallado de operaciones
- 🛡️ Manejo seguro de archivos y directorios

### Recomendaciones de Uso
- 🔍 Verificar URLs antes de la descarga
- 📊 Monitorear el uso de recursos
- 🔐 Mantener dependencias actualizadas

## 🤝 Contribuir

### Proceso de Contribución
1. Fork del repositorio
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Añade nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

### Guías de Contribución
- 📝 Documentar todos los cambios
- ✅ Incluir tests cuando sea posible
- 🔍 Seguir estilo de código existente
- 📋 Actualizar README si es necesario

## ✒️ Autor

### Alexander Oviedo Fadul
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Alexander_Oviedo-0077B5?style=for-the-badge&logo=linkedin&logoColor=white&labelColor=101010)](https://www.linkedin.com/in/alexander-oviedo-fadul/)
[![Web](https://img.shields.io/badge/Web-alexanderoviedofadul.dev-14a1f0?style=for-the-badge&logo=dev.to&logoColor=white&labelColor=101010)](https://alexanderoviedofadul.dev)
[![GitHub](https://img.shields.io/badge/GitHub-bladealex9848-14a1f0?style=for-the-badge&logo=github&logoColor=white&labelColor=101010)](https://github.com/bladealex9848)

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles

---

⌨️ Desarrollado con ❤️ por [Alexander Oviedo Fadul](https://github.com/bladealex9848) 😊

### Contacto Adicional
- 📧 [Correo Profesional](mailto:info@alexanderoviedofadul.dev)
- 💼 [Portfolio](https://alexanderoviedofadul.dev)
- 🐦 [Twitter](https://twitter.com/alexanderofadul)
