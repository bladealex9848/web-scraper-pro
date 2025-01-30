"""
Tests unitarios para el módulo WebScraper.
"""

import unittest
import tempfile
from pathlib import Path
import shutil
import responses
from unittest.mock import patch, MagicMock
from webscraper import WebScraper
from webscraper.exceptions import *


class TestWebScraper(unittest.TestCase):
    """Suite de pruebas para la clase WebScraper."""

    def setUp(self):
        """Configuración inicial para cada prueba."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_url = "https://ejemplo.com"
        self.scraper = WebScraper(self.test_url, self.temp_dir)

    def tearDown(self):
        """Limpieza después de cada prueba."""
        shutil.rmtree(self.temp_dir)

    @responses.activate
    def test_validacion_url(self):
        """Prueba la validación de URLs."""
        # URLs válidas
        urls_validas = [
            "https://ejemplo.com",
            "http://ejemplo.com/pagina",
            "https://ejemplo.com/ruta/archivo.html",
        ]

        # URLs inválidas
        urls_invalidas = [
            "ftp://ejemplo.com",
            "javascript:alert(1)",
            "datos:text/plain,contenido",
            "file:///etc/passwd",
        ]

        for url in urls_validas:
            self.assertTrue(
                self.scraper.validar_url(url), f"La URL válida {url} fue rechazada"
            )

        for url in urls_invalidas:
            self.assertFalse(
                self.scraper.validar_url(url), f"La URL inválida {url} fue aceptada"
            )

    @responses.activate
    def test_descarga_recursos(self):
        """Prueba la descarga de recursos."""
        # Configurar respuestas simuladas
        responses.add(
            responses.GET,
            self.test_url,
            body='<html><img src="imagen.jpg"/></html>',
            status=200,
        )

        responses.add(
            responses.GET,
            "https://ejemplo.com/imagen.jpg",
            body=b"contenido_imagen",
            status=200,
        )

        # Ejecutar descarga
        self.assertTrue(self.scraper.descargar_pagina())

        # Verificar archivos
        self.assertTrue(
            Path(self.temp_dir, "index.html").exists(),
            "No se creó el archivo index.html",
        )
        self.assertTrue(
            Path(self.temp_dir, "imagen.jpg").exists(), "No se descargó la imagen"
        )

    def test_manejo_errores(self):
        """Prueba el manejo de errores."""
        # URL inválida
        with self.assertRaises(URLError):
            scraper = WebScraper("url_invalida", self.temp_dir)
            scraper.descargar_pagina()

        # Error de permisos
        with patch("pathlib.Path.mkdir", side_effect=PermissionError):
            with self.assertRaises(FileSystemError):
                scraper = WebScraper(self.test_url, "/ruta/invalida")
                scraper.descargar_pagina()

    @responses.activate
    def test_limite_tamano(self):
        """Prueba los límites de tamaño de archivo."""
        # Configurar un archivo grande
        responses.add(
            responses.GET,
            self.test_url + "/archivo_grande.zip",
            body="X" * (100 * 1024 * 1024),  # 100MB
            status=200,
        )

        with self.assertRaises(SecurityError):
            self.scraper.descargar_recurso(self.test_url + "/archivo_grande.zip")

    @responses.activate
    def test_tipos_archivo_permitidos(self):
        """Prueba la validación de tipos de archivo."""
        # Archivo permitido
        responses.add(
            responses.GET, self.test_url + "/imagen.jpg", body=b"imagen", status=200
        )

        # Archivo no permitido
        responses.add(
            responses.GET, self.test_url + "/script.php", body=b"<?php ?>", status=200
        )

        # Verificar comportamiento
        self.assertIsNotNone(
            self.scraper.descargar_recurso(self.test_url + "/imagen.jpg"),
            "Se rechazó un tipo de archivo válido",
        )

        self.assertIsNone(
            self.scraper.descargar_recurso(self.test_url + "/script.php"),
            "Se aceptó un tipo de archivo no permitido",
        )

    def test_concurrencia(self):
        """Prueba el procesamiento concurrente."""
        urls = [f"{self.test_url}/recurso{i}.jpg" for i in range(10)]

        for url in urls:
            responses.add(responses.GET, url, body=b"contenido", status=200)

        with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
            mock_executor.return_value.__enter__.return_value.submit = MagicMock()
            self.scraper.descargar_pagina()
            self.assertTrue(mock_executor.called, "No se utilizó el ejecutor de hilos")

    def test_cache(self):
        """Prueba el sistema de caché."""
        url_recurso = f"{self.test_url}/recurso.jpg"

        # Primera descarga
        with patch("requests.Session.get") as mock_get:
            mock_get.return_value.content = b"contenido"

            # Verificar la primera llamada
            self.scraper.descargar_recurso(url_recurso)
            mock_get.assert_called_once()

            # Segunda descarga (debería usar caché)
            mock_get.reset_mock()
            self.scraper.descargar_recurso(url_recurso)
            mock_get.assert_not_called()

    @responses.activate
    def test_estructura_directorios(self):
        """Prueba el mantenimiento de la estructura de directorios."""
        # Configurar respuestas simuladas para una estructura jerárquica
        responses.add(
            responses.GET,
            self.test_url,
            body='<html><link href="css/style.css"/></html>',
            status=200,
        )

        responses.add(
            responses.GET,
            f"{self.test_url}/css/style.css",
            body="body { color: black; }",
            status=200,
        )

        self.scraper.descargar_pagina()

        # Verificar estructura
        self.assertTrue(
            Path(self.temp_dir, "css").is_dir(), "No se creó el directorio css"
        )
        self.assertTrue(
            Path(self.temp_dir, "css/style.css").is_file(),
            "No se mantuvo la estructura de directorios",
        )

    def test_sanitizacion_nombres(self):
        """Prueba la sanitización de nombres de archivo."""
        nombres_prueba = {
            "archivo<>:.php": "archivo__.php",
            "../../../malicioso.js": "malicioso.js",
            "ruta\\invalida\\archivo.css": "ruta_invalida_archivo.css",
            " espacios  .txt": "espacios.txt",
        }

        for entrada, esperado in nombres_prueba.items():
            resultado = self.scraper._sanitizar_nombre_archivo(entrada)
            self.assertEqual(
                resultado,
                esperado,
                f"Fallo en sanitización: {entrada} → {resultado} (esperado: {esperado})",
            )

    @responses.activate
    def test_manejo_recursos_fallidos(self):
        """Prueba el manejo de recursos que fallan al descargarse."""
        # Configurar respuestas simuladas
        responses.add(responses.GET, f"{self.test_url}/404.jpg", status=404)

        responses.add(
            responses.GET,
            f"{self.test_url}/timeout.jpg",
            body=requests.exceptions.Timeout(),
        )

        responses.add(responses.GET, f"{self.test_url}/error.jpg", status=500)

        # Verificar manejo de errores
        self.assertIsNone(
            self.scraper.descargar_recurso(f"{self.test_url}/404.jpg"),
            "No se manejó correctamente el error 404",
        )

        self.assertIsNone(
            self.scraper.descargar_recurso(f"{self.test_url}/timeout.jpg"),
            "No se manejó correctamente el timeout",
        )

        self.assertIsNone(
            self.scraper.descargar_recurso(f"{self.test_url}/error.jpg"),
            "No se manejó correctamente el error 500",
        )

    def test_estadisticas(self):
        """Prueba la generación de estadísticas."""
        # Simular algunas descargas
        with patch("requests.Session.get") as mock_get:
            mock_get.return_value.content = b"contenido"
            mock_get.return_value.status_code = 200

            for i in range(5):
                self.scraper.descargar_recurso(f"{self.test_url}/recurso{i}.jpg")

        # Verificar estadísticas
        stats = self.scraper.obtener_estadisticas()

        self.assertEqual(
            stats["archivos_procesados"], 5, "Contador de archivos incorrecto"
        )
        self.assertGreater(
            stats["bytes_descargados"], 0, "No se registraron bytes descargados"
        )
        self.assertGreater(stats["tiempo_total"], 0, "No se registró el tiempo total")

    @responses.activate
    def test_integracion_completa(self):
        """Prueba de integración completa del proceso de descarga."""
        # Configurar una página de prueba completa
        html_content = """
        <html>
            <head>
                <link rel="stylesheet" href="css/style.css">
                <script src="js/script.js"></script>
            </head>
            <body>
                <img src="images/logo.png">
                <div style="background-image: url('images/bg.jpg')"></div>
            </body>
        </html>
        """

        responses.add(responses.GET, self.test_url, body=html_content, status=200)

        # Agregar respuestas para recursos
        recursos = ["css/style.css", "js/script.js", "images/logo.png", "images/bg.jpg"]

        for recurso in recursos:
            responses.add(
                responses.GET,
                f"{self.test_url}/{recurso}",
                body=f"Contenido de {recurso}",
                status=200,
            )

        # Ejecutar descarga completa
        self.assertTrue(self.scraper.descargar_pagina(), "Falló la descarga completa")

        # Verificar estructura y archivos
        rutas_esperadas = [
            "index.html",
            "css/style.css",
            "js/script.js",
            "images/logo.png",
            "images/bg.jpg",
        ]

        for ruta in rutas_esperadas:
            self.assertTrue(
                Path(self.temp_dir, ruta).exists(), f"No se encontró el archivo {ruta}"
            )

        # Verificar contenido del HTML procesado
        with open(Path(self.temp_dir, "index.html")) as f:
            contenido = f.read()
            self.assertIn('href="css/style.css"', contenido)
            self.assertIn('src="js/script.js"', contenido)
            self.assertIn('src="images/logo.png"', contenido)
            self.assertIn("url('images/bg.jpg')", contenido)


if __name__ == "__main__":
    unittest.main()
