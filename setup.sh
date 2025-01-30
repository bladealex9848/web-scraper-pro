#!/bin/bash

# Configuración de colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para manejar errores
handle_error() {
    echo -e "${RED}Error: $1${NC}"
    exit 1
}

# Función para crear directorios
create_directory() {
    mkdir -p "$1" || handle_error "No se pudo crear el directorio $1"
    echo -e "${BLUE}Creando directorio:${NC} $1"
}

# Función para crear archivos
create_file() {
    echo -e "${BLUE}Creando archivo:${NC} $1"
    if ! cat > "$1"; then
        handle_error "No se pudo crear el archivo $1"
    fi
}

# Verificar que estamos en macOS
if [[ "$(uname)" != "Darwin" ]]; then
    handle_error "Este script está diseñado para ejecutarse en macOS"
fi

# Nombre del proyecto
PROJECT_NAME="web-scraper-pro"
echo -e "${YELLOW}Iniciando la creación del proyecto: $PROJECT_NAME${NC}"

# Crear directorio principal y entrar en él
create_directory "$PROJECT_NAME"
cd "$PROJECT_NAME" || handle_error "No se pudo acceder al directorio del proyecto"

# Crear estructura de directorios
echo -e "${YELLOW}Creando estructura de directorios...${NC}"
create_directory "webscraper"
create_directory "static"
create_directory "temp"

# Crear archivo principal app.py
echo -e "${YELLOW}Creando archivos principales...${NC}"
create_file "app.py" << 'EOF'
import streamlit as st
from webscraper.scraper import WebScraper
import os
import shutil
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    st.set_page_config(
        page_title="Web Scraper Pro",
        page_icon="🌐",
        layout="wide"
    )
    
    st.title("Web Scraper Pro 🌐")
    st.write("Descarga sitios web completos con todos sus recursos.")

    # Configuración en la barra lateral
    with st.sidebar:
        st.header("Configuración")
        mantener_estructura = st.checkbox("Mantener estructura de directorios", value=True)
        incluir_imagenes = st.checkbox("Incluir imágenes", value=True)
        incluir_css = st.checkbox("Incluir CSS", value=True)
        incluir_js = st.checkbox("Incluir JavaScript", value=True)

    # Entrada de URL
    url = st.text_input("Introduce la URL del sitio web:", "https://ejemplo.com")
    
    # Botón de descarga
    if st.button("Descargar sitio", type="primary"):
        if url:
            try:
                # Limpiar directorio temporal
                temp_dir = "temp/download"
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                os.makedirs(temp_dir)

                # Configurar y mostrar barra de progreso
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Iniciar descarga
                scraper = WebScraper(
                    url, 
                    temp_dir,
                    mantener_estructura=mantener_estructura,
                    incluir_imagenes=incluir_imagenes,
                    incluir_css=incluir_css,
                    incluir_js=incluir_js
                )
                
                if scraper.descargar_pagina(progress_bar, status_text):
                    st.success("¡Descarga completada!")
                    
                    # Crear y ofrecer descarga del ZIP
                    zip_path = "sitio_descargado.zip"
                    shutil.make_archive("sitio_descargado", 'zip', temp_dir)
                    
                    with open(zip_path, "rb") as fp:
                        st.download_button(
                            label="Descargar ZIP 📦",
                            data=fp,
                            file_name=zip_path,
                            mime="application/zip"
                        )
                        
                    # Mostrar estadísticas
                    st.subheader("Estadísticas de descarga")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Archivos descargados", scraper.total_archivos)
                    with col2:
                        st.metric("Tamaño total", f"{scraper.tamano_total:.2f} MB")
                    with col3:
                        st.metric("Tiempo total", f"{scraper.tiempo_total:.2f} s")
                else:
                    st.error("Error en la descarga")
            except Exception as e:
                st.error(f"Error: {str(e)}")
                logging.error(f"Error durante la descarga: {str(e)}")

if __name__ == "__main__":
    main()
EOF

# Crear archivo scraper.py
create_file "webscraper/scraper.py" << 'EOF'
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
EOF

# Crear __init__.py
create_file "webscraper/__init__.py" << 'EOF'
from .scraper import WebScraper

__version__ = "1.0.0"
EOF

# Crear requirements.txt
create_file "requirements.txt" << 'EOF'
streamlit>=1.28.0
requests>=2.31.0
beautifulsoup4>=4.12.0
urllib3>=2.1.0
pathlib>=1.0.1
python-logging-json>=0.2.0
concurrent-log-handler>=0.9.24
EOF

# Crear .gitignore
create_file ".gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/
.env/

# IDE
.idea/
.vscode/
*.swp
*.swo
.project
.pydevproject

# Logs
*.log
logs/
logging/

# Carpetas temporales y descargas
temp/
downloads/
*.zip

# OS
.DS_Store
Thumbs.db
*.bak
*.tmp
*.temp

# Streamlit
.streamlit/
EOF

# Crear README.md
create_file "README.md" << 'EOF'
# Web Scraper Pro 🌐

Herramienta de alto rendimiento para descargar sitios web completos de forma local, con interfaz gráfica en Streamlit.

## Características ⚡

- 📥 Descarga completa de sitios web (HTML, CSS, JS, imágenes, etc.)
- 🚀 Procesamiento asíncrono de recursos
- 💾 Sistema de caché para evitar duplicados
- 📊 Interfaz gráfica con Streamlit
- 📁 Mantiene estructura original de directorios
- 🗜️ Exportación automática a ZIP

## Instalación Rápida 🔧

```bash
# Clonar repositorio
git clone https://github.com/bladealex9848/web-scraper-pro.git

# Navegar al directorio
cd web-scraper-pro

# Instalar dependencias
pip install -r requirements.txt
```

## Uso 🚀

```bash
# Iniciar aplicación
streamlit run app.py
```

## Autor ✒️

**Alexander Oviedo Fadul**

[![GitHub](https://img.shields.io/badge/GitHub-bladealex9848-14a1f0?style=for-the-badge&logo=github&logoColor=white&labelColor=101010)](https://github.com/bladealex9848)

## Licencia 📄

Este proyecto está bajo la Licencia MIT
EOF

# Crear CHANGELOG.md
create_file "CHANGELOG.md" << 'EOF'
# Registro de cambios

## [1.0.0] - 2025-01-29

### Añadido
- Implementación inicial del Web Scraper
- Interfaz web con Streamlit
- Descarga completa de sitios web
- Sistema de caché y logging
- Exportación a ZIP

### Mejorado
- Rendimiento en descargas múltiples
- Manejo de errores robusto
- Interfaz de usuario intuitiva
EOF

# Crear LICENSE
create_file "LICENSE" << 'EOF'
MIT License

Copyright (c) 2025 Alexander Oviedo Fadul

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# Crear archivo CSS básico
create_file "static/style.css" << 'EOF'
/* Estilos personalizados para la aplicación */
.stApp {
    max-width: 1200px;
    margin: 0 auto;
}

.stProgress > div > div {
    background-color: #00acee;
}

/* Estilos para los botones */
.stButton > button {
    width: 100%;
    border-radius: 5px;
    padding: 0.5rem 1rem;
    margin-top: 1rem;
}

/* Estilos para las métricas */
.stMetric {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Estilos para las alertas */
.stAlert {
    padding: 1rem;
    border-radius: 5px;
    margin: 1rem 0;
}

/* Personalización de la barra lateral */
.sidebar .sidebar-content {
    background-color: #f8f9fa;
}

/* Mejoras de legibilidad */
.stMarkdown {
    line-height: 1.6;
}

/* Responsividad */
@media (max-width: 768px) {
    .stApp {
        padding: 1rem;
    }
}
EOF

# Crear configuración de Streamlit
create_directory ".streamlit"
create_file ".streamlit/config.toml" << 'EOF'
[theme]
primaryColor = "#00acee"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"
textColor = "#262730"
font = "sans serif"

[server]
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200
EOF

# Crear archivo de inicio rápido
create_file "quickstart.sh" << 'EOF'
#!/bin/bash

# Colores para mensajes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Iniciando configuración del entorno...${NC}"

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 no está instalado"
    exit 1
fi

# Crear entorno virtual
echo -e "${BLUE}Creando entorno virtual...${NC}"
python3 -m venv venv

# Activar entorno virtual
echo -e "${BLUE}Activando entorno virtual...${NC}"
source venv/bin/activate

# Instalar dependencias
echo -e "${BLUE}Instalando dependencias...${NC}"
pip install -r requirements.txt

# Iniciar la aplicación
echo -e "${GREEN}¡Configuración completada!${NC}"
echo -e "${BLUE}Iniciando la aplicación...${NC}"
streamlit run app.py
EOF

# Hacer ejecutables los scripts
chmod +x app.py quickstart.sh

# Inicializar repositorio git
git init
git add .
git commit -m "Commit inicial: Configuración base del proyecto"

echo -e "${GREEN}¡Proyecto creado exitosamente!${NC}"
echo -e "\n${YELLOW}Para comenzar:${NC}"
echo -e "1. cd $PROJECT_NAME"
echo -e "2. ./quickstart.sh"
echo -e "\nO si prefieres hacerlo manualmente:"
echo -e "1. python3 -m venv venv"
echo -e "2. source venv/bin/activate"
echo -e "3. pip install -r requirements.txt"
echo -e "4. streamlit run app.py"

echo -e "\n${BLUE}¡Feliz desarrollo!${NC} 🚀"