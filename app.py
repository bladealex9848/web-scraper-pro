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
