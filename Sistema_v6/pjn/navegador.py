import sys
import time
import json
import re
import os
import requests
from playwright.sync_api import sync_playwright
from datetime import date, datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
from Sistema_v6.pjn.auto_login import iniciar_sesion  # 🔹 Importamos la función de autologin
from src.database_v1 import conectar_bd  # 🔹 Importamos la conexión a la base de datos


class NavegadorPersonalizado(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Navegador Personalizado - SCW PJN")
        self.setGeometry(100, 100, 400, 300)

        self.pestañas_abiertas = {}  # 🔹 Almacena múltiples pestañas con nombres clave

        # 🔹 Iniciar sesión automáticamente
        self.page = iniciar_sesion()
        if not self.page:
            self.mostrar_mensaje("Error", "❌ Error en el autologin. La aplicación se cerrará.")
            sys.exit()

        print("✅ Autologin exitoso.")

        # Diseñar la interfaz con botones
        layout = QVBoxLayout()

        btn_extraer_expediente = QPushButton("🔍 Extraer Datos del Expediente")
        btn_extraer_expediente.clicked.connect(self.extraer_datos_expediente)
        layout.addWidget(btn_extraer_expediente)

        btn_obtener_actuaciones = QPushButton("📥 Obtener Actuaciones")
        btn_obtener_actuaciones.clicked.connect(self.obtener_actuaciones)
        layout.addWidget(btn_obtener_actuaciones)

        btn_recargar = QPushButton("🔄 Refrescar Página")
        btn_recargar.clicked.connect(self.refrescar_pagina)
        layout.addWidget(btn_recargar)

        btn_cerrar = QPushButton("🛑 Cerrar Navegador")
        btn_cerrar.clicked.connect(self.cerrar_navegador)
        layout.addWidget(btn_cerrar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def mostrar_mensaje(self, titulo, mensaje):
        """Muestra un cuadro de diálogo con un mensaje."""
        msg_box = QMessageBox()
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.exec()

    def obtener_pestaña_activa(self):
        """Obtiene la pestaña activa en Playwright."""
        if not self.page.context.pages:
            self.mostrar_mensaje("Error", "❌ No hay pestañas abiertas.")
            return None

        for page in reversed(self.page.context.pages):
            if not page.is_closed():
                print(f"✅ Pestaña activa detectada: {page.url}")
                return page

        self.mostrar_mensaje("Advertencia", "⚠️ No se encontró una pestaña activa.")
        return None

    def extraer_datos_expediente(self):
        """Extrae los datos del expediente en la pestaña activa y busca en la base de datos."""
        print("⏳ Detectando pestaña activa...")

        page_expediente = self.obtener_pestaña_activa()
        if not page_expediente:
            return None

        page_expediente.wait_for_load_state("load")
        page_expediente.wait_for_load_state("networkidle")

        print(f"✅ Pestaña lista. Extrayendo datos de: {page_expediente.url}")

        selectores = {
            "numero": "span[style='color:#000000;']",
            "jurisdiccion": "#expediente\\:j_idt96\\:detailCamera",
            "dependencia": "#expediente\\:j_idt96\\:detailDependencia",
            "situacion": "#expediente\\:j_idt96\\:detailSituation",
            "caratula": "#expediente\\:j_idt96\\:detailCover"
        }

        expediente = {}
        for campo, selector in selectores.items():
            elemento = page_expediente.query_selector(selector)
            expediente[campo] = elemento.inner_text().strip() if elemento else "No encontrado"

        numero_expediente = expediente.get("numero", None)
        caratula_expediente = expediente.get("caratula", None)

        if not numero_expediente:
            self.mostrar_mensaje("Error", "No se pudo extraer el número de expediente.")
            return None

        # Buscar en la base de datos
        conexion = conectar_bd()
        if not conexion:
            self.mostrar_mensaje("Error", "No se pudo conectar a la base de datos.")
            return None

        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM expedientes WHERE numero = %s", (numero_expediente,))
            expediente_db = cursor.fetchone()

            # Si no encuentra por número, buscar por carátula exacta
            if not expediente_db and caratula_expediente and caratula_expediente != "No encontrado":
                cursor.execute("SELECT * FROM expedientes WHERE caratula = %s", (caratula_expediente,))
                expediente_db = cursor.fetchone()

            cursor.close()
            conexion.close()
        except Exception as err:
            self.mostrar_mensaje("Error", f"Error al ejecutar la consulta: {err}")
            return None

        if expediente_db:
            self.mostrar_mensaje("Información", "✅ Expediente encontrado en la base de datos.")

            # Convertir fechas a string
            for key, value in expediente_db.items():
                if isinstance(value, (date, datetime)):
                    expediente_db[key] = value.strftime("%Y-%m-%d")

            mensaje = json.dumps(expediente_db, indent=2, ensure_ascii=False)
            self.mostrar_mensaje("Expediente Encontrado", mensaje)
        else:
            self.mostrar_mensaje("Expediente No Encontrado",
                                 f"El expediente {numero_expediente} no está en la base de datos.")

        return expediente_db

    import os
    import re

    def obtener_actuaciones(self):
        """Descarga todas las actuaciones (actuaciones, notificaciones, cédulas) en una única carpeta."""
        print("⏳ Descargando actuaciones...")

        page_expediente = self.obtener_pestaña_activa()
        if not page_expediente:
            print("❌ No se encontró una pestaña activa.")
            return

        expediente_datos = self.extraer_datos_expediente()
        if not expediente_datos:
            print("❌ No se generará el archivo JSON porque no se encontraron datos de expediente.")
            return

        expediente_numero = expediente_datos.get("numero", "desconocido")
        expediente_numero = re.sub(r'[^a-zA-Z0-9_-]', '_', expediente_numero)

        # 🔹 Carpeta única para todas las actuaciones
        carpeta_actuaciones = os.path.join(os.getcwd(), "descargas", "todas_actuaciones")
        os.makedirs(carpeta_actuaciones, exist_ok=True)

        actuaciones = []
        archivos_descargados = 0
        filas = page_expediente.query_selector_all("#expediente\\:action-table tbody tr")

        for idx, fila in enumerate(filas, start=1):
            celdas = fila.query_selector_all("td")

            def limpiar_texto(texto):
                """Elimina saltos de línea y prefijos innecesarios."""
                return re.sub(r'^(Oficina:|Fecha:|Tipo actuacion:|Detalle:|Foja:)\s*', '',
                              texto.strip().replace("\n", " "))

            # Buscar el icono de descarga
            enlace = fila.query_selector("a i.fa-download")
            archivo_url = None
            nombre_archivo = None

            if enlace:
                link_handle = page_expediente.evaluate_handle("(el) => el.closest('a')", enlace)
                if link_handle:
                    archivo_url = link_handle.get_attribute("href")
                    nombre_archivo = link_handle.get_attribute("download") or f"documento_{idx}.pdf"

                    # Nombre de archivo con expediente y tipo de actuación
                    nombre_archivo = f"{expediente_numero}_Acto_{idx}_{nombre_archivo.split('/')[-1]}"
                    ruta_archivo = os.path.join(carpeta_actuaciones, nombre_archivo)

                    # Descargar con Playwright
                    try:
                        with page_expediente.expect_download() as download_info:
                            link_handle.click()
                        download = download_info.value
                        download.save_as(ruta_archivo)
                        archivos_descargados += 1
                        print(f"📥 Archivo guardado en: {ruta_archivo}")
                    except Exception as e:
                        print(f"❌ Error al descargar {archivo_url}: {e}")

            actuaciones.append({
                "Oficina": limpiar_texto(celdas[1].inner_text()) if len(celdas) > 1 else "N/A",
                "Fecha": limpiar_texto(celdas[2].inner_text()) if len(celdas) > 2 else "N/A",
                "Tipo": limpiar_texto(celdas[3].inner_text()) if len(celdas) > 3 else "N/A",
                "Detalle": limpiar_texto(celdas[4].inner_text()) if len(celdas) > 4 else "N/A",
                "Foja": limpiar_texto(celdas[5].inner_text()) if len(celdas) > 5 else "N/A",
                "Archivo": archivo_url,
                "NombreArchivo": nombre_archivo
            })

        expediente_datos["Cantidad de Actuaciones Obtenidas"] = len(actuaciones)
        expediente_datos["Cantidad de Archivos Descargados"] = archivos_descargados

        datos = {"Expediente": expediente_datos, "Actuaciones": actuaciones}

        json_filename = os.path.join(carpeta_actuaciones, f"actuaciones-{expediente_numero}.json")
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)

        print(f"✅ Archivo JSON guardado: {json_filename}")
        print(f"📂 Todos los archivos están en: {carpeta_actuaciones}")

    # def obtener_actuaciones(self):
    #     """Descarga las actuaciones y genera un archivo JSON."""
    #     print("⏳ Descargando actuaciones...")
    #     page_expediente = self.obtener_pestaña_activa()
    #     if not page_expediente:
    #         print("❌ No se encontró una pestaña activa.")
    #         return
    #
    #     expediente_datos = self.extraer_datos_expediente()
    #     if not expediente_datos:
    #         print("❌ No se generará el archivo JSON porque no se encontraron datos de expediente.")
    #         return
    #
    #     expediente_numero = expediente_datos.get("numero", "desconocido")
    #     expediente_numero = re.sub(r'[^a-zA-Z0-9_-]', '_', expediente_numero)  # Remover caracteres inválidos
    #
    #     actuaciones = []
    #     filas = page_expediente.query_selector_all("#expediente\\:action-table tbody tr")
    #
    #     for idx, fila in enumerate(filas, start=1):
    #         celdas = fila.query_selector_all("td")
    #
    #         def limpiar_texto(texto):
    #             """Elimina saltos de línea y prefijos innecesarios"""
    #             return re.sub(r'^(Oficina:|Fecha:|Tipo actuacion:|Detalle:|Foja:)\s*', '',
    #                           texto.strip().replace("\n", " "))
    #
    #         actuaciones.append({
    #             "Oficina": limpiar_texto(celdas[1].inner_text()) if len(celdas) > 1 else "N/A",
    #             "Fecha": limpiar_texto(celdas[2].inner_text()) if len(celdas) > 2 else "N/A",
    #             "Tipo": limpiar_texto(celdas[3].inner_text()) if len(celdas) > 3 else "N/A",
    #             "Detalle": limpiar_texto(celdas[4].inner_text()) if len(celdas) > 4 else "N/A",
    #             "Foja": limpiar_texto(celdas[5].inner_text()) if len(celdas) > 5 else "N/A"
    #         })
    #
    #     datos = {"Expediente": expediente_datos, "Actuaciones": actuaciones}
    #
    #     with open(f"actuaciones-{expediente_numero}.json", "w", encoding="utf-8") as f:
    #         json.dump(datos, f, indent=2, ensure_ascii=False)
    #
    #     print(f"✅ Archivo JSON guardado: actuaciones-{expediente_numero}.json")

    def refrescar_pagina(self):
        """Recarga la página actual."""
        self.page.reload()
        self.mostrar_mensaje("Información", "🔄 Página recargada.")

    def cerrar_navegador(self):
        """Cierra el navegador y la aplicación."""
        self.page.context.browser.close()
        self.mostrar_mensaje("Información", "🛑 Navegador cerrado.")
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = NavegadorPersonalizado()
    ventana.show()
    sys.exit(app.exec())

# import sys
# import time
# import json
# import re
# from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
# from Sistema_v6.pjn.auto_login import iniciar_sesion  # 🔹 Importamos la función de autologin
#
#
# class NavegadorPersonalizado(QMainWindow):
#     def __init__(self):
#         super().__init__()
#
#         self.setWindowTitle("Navegador Personalizado - SCW PJN")
#         self.setGeometry(100, 100, 400, 300)
#
#         self.pestañas_abiertas = {}  # 🔹 Almacena múltiples pestañas con nombres clave
#
#         # 🔹 Iniciar sesión automáticamente
#         self.page = iniciar_sesion()
#         if not self.page:
#             print("❌ Error en el autologin. Cerrando aplicación...")
#             sys.exit()
#
#         print("✅ Autologin exitoso.")
#
#         # Diseñar la interfaz con botones
#         layout = QVBoxLayout()
#
#         btn_extraer_expediente = QPushButton("🔍 Extraer Datos del Expediente")
#         btn_extraer_expediente.clicked.connect(self.extraer_datos_expediente)
#         layout.addWidget(btn_extraer_expediente)
#
#         btn_obtener_actuaciones = QPushButton("📥 Obtener Actuaciones")
#         btn_obtener_actuaciones.clicked.connect(self.obtener_actuaciones)
#         layout.addWidget(btn_obtener_actuaciones)
#
#         btn_recargar = QPushButton("🔄 Refrescar Página")
#         btn_recargar.clicked.connect(self.refrescar_pagina)
#         layout.addWidget(btn_recargar)
#
#         btn_cerrar = QPushButton("🛑 Cerrar Navegador")
#         btn_cerrar.clicked.connect(self.cerrar_navegador)
#         layout.addWidget(btn_cerrar)
#
#         container = QWidget()
#         container.setLayout(layout)
#         self.setCentralWidget(container)
#
#     def obtener_pestaña_activa(self):
#         """Obtiene la pestaña activa en Playwright."""
#         if not self.page.context.pages:
#             print("❌ No hay pestañas abiertas.")
#             return None
#
#         for page in reversed(self.page.context.pages):
#             if not page.is_closed():
#                 print(f"✅ Pestaña activa detectada: {page.url}")
#                 return page
#
#         print("⚠️ No se encontró una pestaña activa.")
#         return None
#
#     def extraer_datos_expediente(self):
#         """Extrae los datos del expediente en la pestaña activa usando Playwright."""
#         print("⏳ Detectando pestaña activa...")
#
#         page_expediente = self.obtener_pestaña_activa()
#         if not page_expediente:
#             print("❌ Error: No se detectó una pestaña activa.")
#             return None
#
#         page_expediente.wait_for_load_state("load")
#         page_expediente.wait_for_load_state("networkidle")
#
#         print(f"✅ Pestaña lista. Extrayendo datos de: {page_expediente.url}")
#
#         selectores = {
#             "numero": "span[style='color:#000000;']",
#             "jurisdiccion": "#expediente\\:j_idt96\\:detailCamera",
#             "dependencia": "#expediente\\:j_idt96\\:detailDependencia",
#             "situacion": "#expediente\\:j_idt96\\:detailSituation",
#             "caratula": "#expediente\\:j_idt96\\:detailCover"
#         }
#
#         expediente = {}
#         for campo, selector in selectores.items():
#             elemento = page_expediente.query_selector(selector)
#             expediente[campo] = elemento.inner_text().strip() if elemento else "No encontrado"
#
#         if all(valor == "No encontrado" for valor in expediente.values()):
#             print("⚠️ No se encontraron datos del expediente. Se cancelará la generación del archivo JSON.")
#             return None
#
#         print("📌 Datos extraídos:", expediente)
#         return expediente
#
    # def obtener_actuaciones(self):
    #     """Descarga las actuaciones y genera un archivo JSON."""
    #     print("⏳ Descargando actuaciones...")
    #     page_expediente = self.obtener_pestaña_activa()
    #     if not page_expediente:
    #         print("❌ No se encontró una pestaña activa.")
    #         return
    #
    #     expediente_datos = self.extraer_datos_expediente()
    #     if not expediente_datos:
    #         print("❌ No se generará el archivo JSON porque no se encontraron datos de expediente.")
    #         return
    #
    #     expediente_numero = expediente_datos.get("numero", "desconocido")
    #     expediente_numero = re.sub(r'[^a-zA-Z0-9_-]', '_', expediente_numero)  # Remover caracteres inválidos
    #
    #     actuaciones = []
    #     filas = page_expediente.query_selector_all("#expediente\\:action-table tbody tr")
    #     for idx, fila in enumerate(filas, start=1):
    #         celdas = fila.query_selector_all("td")
    #         actuaciones.append({
    #             "Oficina": celdas[1].inner_text().strip() if len(celdas) > 1 else "N/A",
    #             "Fecha": celdas[2].inner_text().strip() if len(celdas) > 2 else "N/A",
    #             "Tipo": celdas[3].inner_text().strip() if len(celdas) > 3 else "N/A",
    #             "Detalle": celdas[4].inner_text().strip() if len(celdas) > 4 else "N/A",
    #             "Foja": celdas[5].inner_text().strip() if len(celdas) > 5 else "N/A"
    #         })
    #
    #     datos = {"Expediente": expediente_datos, "Actuaciones": actuaciones}
    #     with open(f"actuaciones-{expediente_numero}.json", "w", encoding="utf-8") as f:
    #         json.dump(datos, f, indent=2, ensure_ascii=False)
    #     print(f"✅ Archivo JSON guardado: actuaciones-{expediente_numero}.json")
#
#     def refrescar_pagina(self):
#         """Recarga la página actual."""
#         self.page.reload()
#         print("🔄 Página recargada.")
#
#     def cerrar_navegador(self):
#         """Cierra el navegador y la aplicación."""
#         self.page.context.browser.close()
#         print("🛑 Navegador cerrado.")
#         self.close()
#
#
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     ventana = NavegadorPersonalizado()
#     ventana.show()
#     sys.exit(app.exec())

#
# # import sys
# # import time
# # import json
# # import re
# # from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
# # from Sistema_v6.pjn.auto_login import iniciar_sesion  # 🔹 Importamos la función de autologin
# #
# #
# # class NavegadorPersonalizado(QMainWindow):
# #     def __init__(self):
# #         super().__init__()
# #
# #         self.setWindowTitle("Navegador Personalizado - SCW PJN")
# #         self.setGeometry(100, 100, 400, 300)
# #
# #         self.pestañas_abiertas = {}  # 🔹 Almacena múltiples pestañas con nombres clave
# #
# #         # 🔹 Iniciar sesión automáticamente
# #         self.page = iniciar_sesion()
# #         if not self.page:
# #             print("❌ Error en el autologin. Cerrando aplicación...")
# #             sys.exit()
# #
# #         print("✅ Autologin exitoso.")
# #
# #         # Diseñar la interfaz con botones
# #         layout = QVBoxLayout()
# #
# #         btn_ir_a_pagina = QPushButton("📂 Abrir Lista de Expedientes")
# #         btn_ir_a_pagina.clicked.connect(self.abrir_lista_expedientes)
# #         layout.addWidget(btn_ir_a_pagina)
# #
# #         btn_extraer_expediente = QPushButton("🔍 Extraer Datos del Expediente")
# #         btn_extraer_expediente.clicked.connect(self.extraer_datos_expediente)
# #         layout.addWidget(btn_extraer_expediente)
# #
# #         btn_descargar_actuaciones = QPushButton("📥 Descargar Actuaciones")
# #         btn_descargar_actuaciones.clicked.connect(self.descargar_actuaciones)
# #         layout.addWidget(btn_descargar_actuaciones)
# #
# #         btn_recargar = QPushButton("🔄 Refrescar Página")
# #         btn_recargar.clicked.connect(self.refrescar_pagina)
# #         layout.addWidget(btn_recargar)
# #
# #         btn_cerrar = QPushButton("🛑 Cerrar Navegador")
# #         btn_cerrar.clicked.connect(self.cerrar_navegador)
# #         layout.addWidget(btn_cerrar)
# #
# #         container = QWidget()
# #         container.setLayout(layout)
# #         self.setCentralWidget(container)
# #
# #     def obtener_pestaña_activa(self):
# #         """Obtiene la pestaña activa en Playwright."""
# #         if not self.page.context.pages:
# #             print("❌ No hay pestañas abiertas.")
# #             return None
# #
# #         for page in reversed(self.page.context.pages):
# #             if not page.is_closed():
# #                 print(f"✅ Pestaña activa detectada: {page.url}")
# #                 return page
# #
# #         print("⚠️ No se encontró una pestaña activa.")
# #         return None
# #
# #     def abrir_lista_expedientes(self):
# #         """Abre la lista de expedientes en la web."""
# #         self.page.goto("https://scw.pjn.gov.ar/scw/consultaListaRelacionados.seam")
# #         print("📂 Página de expedientes abierta.")
# #
# #     def extraer_datos_expediente(self):
# #         """Extrae los datos del expediente en la pestaña activa usando Playwright."""
# #         print("⏳ Detectando pestaña activa...")
# #
# #         page_expediente = self.obtener_pestaña_activa()
# #         if not page_expediente:
# #             print("❌ Error: No se detectó una pestaña activa.")
# #             return
# #
# #         page_expediente.wait_for_load_state("load")
# #         page_expediente.wait_for_load_state("networkidle")
# #
# #         print(f"✅ Pestaña lista. Extrayendo datos de: {page_expediente.url}")
# #
# #         selectores = {
# #             "numero": "span[style='color:#000000;']",
# #             "jurisdiccion": "#expediente\\:j_idt96\\:detailCamera",
# #             "dependencia": "#expediente\\:j_idt96\\:detailDependencia",
# #             "situacion": "#expediente\\:j_idt96\\:detailSituation",
# #             "caratula": "#expediente\\:j_idt96\\:detailCover"
# #         }
# #
# #         expediente = {}
# #         for campo, selector in selectores.items():
# #             elemento = page_expediente.query_selector(selector)
# #             expediente[campo] = elemento.inner_text().strip() if elemento else "No encontrado"
# #
# #         print("📌 Datos extraídos:", expediente)
# #         return expediente
# #
# #     def descargar_actuaciones(self):
# #         """Descarga las actuaciones y genera un archivo JSON."""
# #         print("⏳ Descargando actuaciones...")
# #         page_expediente = self.obtener_pestaña_activa()
# #         if not page_expediente:
# #             print("❌ No se encontró una pestaña activa.")
# #             return
# #
# #         expediente_datos = self.extraer_datos_expediente()
# #         expediente_numero = expediente_datos.get("numero", "desconocido")
# #         expediente_numero = re.sub(r'[^a-zA-Z0-9_-]', '_', expediente_numero)  # Remover caracteres inválidos
# #
# #         actuaciones = []
# #         base_url = "https://scw.pjn.gov.ar"
# #         filas = page_expediente.query_selector_all("#expediente\\:action-table tbody tr")
# #         for idx, fila in enumerate(filas, start=1):
# #             celdas = fila.query_selector_all("td")
# #             enlace_a = fila.query_selector("a")
# #             archivo_url = enlace_a.get_attribute("href") if enlace_a else None
# #             if archivo_url and not archivo_url.startswith("http"):
# #                 archivo_url = base_url + archivo_url
# #
# #             nombre_archivo = f"{expediente_numero}_Acto_{idx}.pdf" if archivo_url else None
# #
# #             actuaciones.append({
# #                 "Oficina": celdas[1].inner_text().replace("Oficina:\n", "").strip() if len(celdas) > 1 else "N/A",
# #                 "Fecha": celdas[2].inner_text().replace("Fecha:\n", "").strip() if len(celdas) > 2 else "N/A",
# #                 "Tipo": celdas[3].inner_text().replace("Tipo actuacion:\n", "").strip() if len(celdas) > 3 else "N/A",
# #                 "Detalle": celdas[4].inner_text().replace("Detalle:\n", "").strip() if len(celdas) > 4 else "N/A",
# #                 "Foja": celdas[5].inner_text().strip() if len(celdas) > 5 and celdas[5].inner_text().strip() else "N/A",
# #                 "Archivo": archivo_url,
# #                 "NombreArchivo": nombre_archivo
# #             })
# #
# #         datos = {"Expediente": expediente_datos, "Actuaciones": actuaciones}
# #         with open(f"actuaciones-{expediente_numero}.json", "w", encoding="utf-8") as f:
# #             json.dump(datos, f, indent=2, ensure_ascii=False)
# #         print(f"✅ Archivo JSON guardado: actuaciones-{expediente_numero}.json")
# #
# #     def refrescar_pagina(self):
# #         """Recarga la página actual."""
# #         self.page.reload()
# #         print("🔄 Página recargada.")
# #
# #     def cerrar_navegador(self):
# #         """Cierra el navegador y la aplicación."""
# #         self.page.context.browser.close()
# #         print("🛑 Navegador cerrado.")
# #         self.close()
# #
# #
# # if __name__ == "__main__":
# #     app = QApplication(sys.argv)
# #     ventana = NavegadorPersonalizado()
# #     ventana.show()
# #     sys.exit(app.exec())
