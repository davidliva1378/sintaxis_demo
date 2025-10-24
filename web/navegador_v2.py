import sys
import time
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
from web.auto_login import iniciar_sesion  # 🔹 Importamos la función de autologin
from funciones_navegador_v2 import extraer_datos_expediente, obtener_actuaciones, comparar_actuaciones  # 🔹 Importamos funciones externas


class NavegadorPersonalizado(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Navegador Personalizado - SCW PJN")
        self.setGeometry(100, 100, 400, 300)

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

        btn_comparar_actuaciones = QPushButton("🔄 Comparar Actuaciones")
        btn_comparar_actuaciones.clicked.connect(self.comparar_actuaciones)
        layout.addWidget(btn_comparar_actuaciones)

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
        """Llama a la función de extracción de datos desde el módulo externo."""
        page_expediente = self.obtener_pestaña_activa()
        if not page_expediente:
            return None
        expediente_db = extraer_datos_expediente(page_expediente)
        if expediente_db:
            mensaje = str(expediente_db)
            self.mostrar_mensaje("Expediente Encontrado", mensaje)
        else:
            self.mostrar_mensaje("Expediente No Encontrado", "No se encontró el expediente en la base de datos.")

    def obtener_actuaciones(self):
        """Llama a la función de obtención de actuaciones desde el módulo externo y devuelve las actuaciones obtenidas."""
        page_expediente = self.obtener_pestaña_activa()
        if not page_expediente:
            return []
        expediente_datos = extraer_datos_expediente(page_expediente)
        if expediente_datos:
            actuaciones = obtener_actuaciones(page_expediente, expediente_datos)
            if not actuaciones:
                self.mostrar_mensaje("Información", "📂 No se encontraron actuaciones en la web.")
            else:
                self.mostrar_mensaje("Información", f"📂 Se descargaron {len(actuaciones)} actuaciones correctamente.")
            return actuaciones
        return []

    def comparar_actuaciones(self):
        """Compara las actuaciones del expediente en la web con las almacenadas en la base de datos."""
        page_expediente = self.obtener_pestaña_activa()
        if not page_expediente:
            return

        expediente_datos = extraer_datos_expediente(page_expediente)
        if not expediente_datos:
            self.mostrar_mensaje("Error", "❌ No se encontró el expediente en la base de datos.")
            return

        expediente_id = expediente_datos.get("id_expediente")
        if not expediente_id:
            self.mostrar_mensaje("Error", "❌ No se pudo obtener el ID del expediente.")
            return

        actuaciones_nuevas = obtener_actuaciones(page_expediente, expediente_datos)
        if not actuaciones_nuevas:
            self.mostrar_mensaje("Información", "📂 No se encontraron actuaciones en la web.")
            return

        nuevas_actuaciones = comparar_actuaciones(expediente_id, actuaciones_nuevas)
        if nuevas_actuaciones:
            mensaje = f"✅ Se encontraron {len(nuevas_actuaciones)} actuaciones nuevas."
            for i, act in enumerate(nuevas_actuaciones, start=1):
                mensaje += f"\n{i}. {act['Fecha']} - {act['Tipo']} - {act['Detalle']}"
        else:
            mensaje = "📂 No hay nuevas actuaciones."

        self.mostrar_mensaje("Comparación de Actuaciones", mensaje)

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
# import os
# import requests
# from playwright.sync_api import sync_playwright
# from datetime import date, datetime
# from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
# from web.auto_login import iniciar_sesion  # 🔹 Importamos la función de autologin
# from src.database_v1 import conectar_bd  # 🔹 Importamos la conexión a la base de datos
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
#             self.mostrar_mensaje("Error", "❌ Error en el autologin. La aplicación se cerrará.")
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
#     def mostrar_mensaje(self, titulo, mensaje):
#         """Muestra un cuadro de diálogo con un mensaje."""
#         msg_box = QMessageBox()
#         msg_box.setWindowTitle(titulo)
#         msg_box.setText(mensaje)
#         msg_box.exec()
#
#     def obtener_pestaña_activa(self):
#         """Obtiene la pestaña activa en Playwright."""
#         if not self.page.context.pages:
#             self.mostrar_mensaje("Error", "❌ No hay pestañas abiertas.")
#             return None
#
#         for page in reversed(self.page.context.pages):
#             if not page.is_closed():
#                 print(f"✅ Pestaña activa detectada: {page.url}")
#                 return page
#
#         self.mostrar_mensaje("Advertencia", "⚠️ No se encontró una pestaña activa.")
#         return None
#
#     def extraer_datos_expediente(self):
#         """Extrae los datos del expediente en la pestaña activa y busca en la base de datos."""
#         print("⏳ Detectando pestaña activa...")
#
#         page_expediente = self.obtener_pestaña_activa()
#         if not page_expediente:
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
#         numero_expediente = expediente.get("numero", None)
#         caratula_expediente = expediente.get("caratula", None)
#
#         if not numero_expediente:
#             self.mostrar_mensaje("Error", "No se pudo extraer el número de expediente.")
#             return None
#
#         # Buscar en la base de datos
#         conexion = conectar_bd()
#         if not conexion:
#             self.mostrar_mensaje("Error", "No se pudo conectar a la base de datos.")
#             return None
#
#         try:
#             cursor = conexion.cursor(dictionary=True)
#             cursor.execute("SELECT * FROM expedientes WHERE numero = %s", (numero_expediente,))
#             expediente_db = cursor.fetchone()
#
#             # Si no encuentra por número, buscar por carátula exacta
#             if not expediente_db and caratula_expediente and caratula_expediente != "No encontrado":
#                 cursor.execute("SELECT * FROM expedientes WHERE caratula = %s", (caratula_expediente,))
#                 expediente_db = cursor.fetchone()
#
#             cursor.close()
#             conexion.close()
#         except Exception as err:
#             self.mostrar_mensaje("Error", f"Error al ejecutar la consulta: {err}")
#             return None
#
#         if expediente_db:
#             self.mostrar_mensaje("Información", "✅ Expediente encontrado en la base de datos.")
#
#             # Convertir fechas a string
#             for key, value in expediente_db.items():
#                 if isinstance(value, (date, datetime)):
#                     expediente_db[key] = value.strftime("%Y-%m-%d")
#
#             mensaje = json.dumps(expediente_db, indent=2, ensure_ascii=False)
#             self.mostrar_mensaje("Expediente Encontrado", mensaje)
#         else:
#             self.mostrar_mensaje("Expediente No Encontrado",
#                                  f"El expediente {numero_expediente} no está en la base de datos.")
#
#         return expediente_db
#
#     def obtener_actuaciones(self):
#         """Descarga todas las actuaciones (actuaciones, notificaciones, cédulas) en una única carpeta."""
#         print("⏳ Descargando actuaciones...")
#
#         page_expediente = self.obtener_pestaña_activa()
#         if not page_expediente:
#             print("❌ No se encontró una pestaña activa.")
#             return
#
#         expediente_datos = self.extraer_datos_expediente()
#         if not expediente_datos:
#             print("❌ No se generará el archivo JSON porque no se encontraron datos de expediente.")
#             return
#
#         expediente_numero = expediente_datos.get("numero", "desconocido")
#         expediente_numero = re.sub(r'[^a-zA-Z0-9_-]', '_', expediente_numero)
#
#         # 🔹 Carpeta única para todas las actuaciones
#         carpeta_actuaciones = os.path.join(os.getcwd(), "descargas", "todas_actuaciones")
#         os.makedirs(carpeta_actuaciones, exist_ok=True)
#
#         actuaciones = []
#         archivos_descargados = 0
#         filas = page_expediente.query_selector_all("#expediente\\:action-table tbody tr")
#
#         for idx, fila in enumerate(filas, start=1):
#             celdas = fila.query_selector_all("td")
#
#             def limpiar_texto(texto):
#                 """Elimina saltos de línea y prefijos innecesarios."""
#                 return re.sub(r'^(Oficina:|Fecha:|Tipo actuacion:|Detalle:|Foja:)\s*', '',
#                               texto.strip().replace("\n", " "))
#
#             # Buscar el icono de descarga
#             enlace = fila.query_selector("a i.fa-download")
#             archivo_url = None
#             nombre_archivo = None
#
#             if enlace:
#                 try:
#                     link_handle = page_expediente.evaluate_handle("(el) => el.closest('a')", enlace)
#                     if link_handle:
#                         archivo_url = link_handle.get_attribute("href")
#                         nombre_archivo = link_handle.get_attribute("download") or f"documento_{idx}.pdf"
#
#                         if archivo_url:
#                             # Nombre de archivo con expediente y tipo de actuación
#                             nombre_archivo = f"{expediente_numero}_Acto_{idx}_{nombre_archivo.split('/')[-1]}"
#                             ruta_archivo = os.path.join(carpeta_actuaciones, nombre_archivo)
#
#                             # Descargar con Playwright
#                             with page_expediente.expect_download() as download_info:
#                                 link_handle.click()
#                             download = download_info.value
#                             download.save_as(ruta_archivo)
#                             archivos_descargados += 1
#                             print(f"📥 Archivo guardado en: {ruta_archivo}")
#                         else:
#                             print(f"⚠️ No se encontró un enlace válido para descargar en la fila {idx}")
#
#                 except Exception as e:
#                     print(f"❌ Error al procesar la descarga en la fila {idx}: {e}")
#
#             actuaciones.append({
#                 "Oficina": limpiar_texto(celdas[1].inner_text()) if len(celdas) > 1 else "N/A",
#                 "Fecha": limpiar_texto(celdas[2].inner_text()) if len(celdas) > 2 else "N/A",
#                 "Tipo": limpiar_texto(celdas[3].inner_text()) if len(celdas) > 3 else "N/A",
#                 "Detalle": limpiar_texto(celdas[4].inner_text()) if len(celdas) > 4 else "N/A",
#                 "Foja": limpiar_texto(celdas[5].inner_text()) if len(celdas) > 5 else "N/A",
#                 "Archivo": archivo_url if archivo_url else "N/A",
#                 "NombreArchivo": nombre_archivo if archivo_url else "N/A"
#             })
#
#         expediente_datos["Cantidad de Actuaciones Obtenidas"] = len(actuaciones)
#         expediente_datos["Cantidad de Archivos Descargados"] = archivos_descargados
#
#         datos = {"Expediente": expediente_datos, "Actuaciones": actuaciones}
#
#         json_filename = os.path.join(carpeta_actuaciones, f"actuaciones-{expediente_numero}.json")
#         with open(json_filename, "w", encoding="utf-8") as f:
#             json.dump(datos, f, indent=2, ensure_ascii=False)
#
#         print(f"✅ Archivo JSON guardado: {json_filename}")
#         print(f"📂 Todos los archivos están en: {carpeta_actuaciones}")
#
#     def refrescar_pagina(self):
#         """Recarga la página actual."""
#         self.page.reload()
#         self.mostrar_mensaje("Información", "🔄 Página recargada.")
#
#     def cerrar_navegador(self):
#         """Cierra el navegador y la aplicación."""
#         self.page.context.browser.close()
#         self.mostrar_mensaje("Información", "🛑 Navegador cerrado.")
#         self.close()
#
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     ventana = NavegadorPersonalizado()
#     ventana.show()
#     sys.exit(app.exec())
