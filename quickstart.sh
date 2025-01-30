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
