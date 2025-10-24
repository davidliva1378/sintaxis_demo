import sys
import asyncio
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
from web.auto_login import reutilizar_sesion_async
from funciones_navegador_async import extraer_datos_expediente, obtener_actuaciones, comparar_actuaciones

class NavegadorPersonalizado(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Navegador Personalizado - SCW PJN")
        self.setGeometry(100, 100, 400, 300)

        self._autologin_cm = reutilizar_sesion_async()
        self.page, self.context, self.browser = asyncio.run(self._autologin_cm.__aenter__())
        if not self.page:
            self.mostrar_mensaje("Error", "❌ Error en el autologin. La aplicación se cerrará.")
            sys.exit()
        print("✅ Autologin exitoso.")

        layout = QVBoxLayout()

        btn_extraer_expediente = QPushButton("🔍 Extraer Datos del Expediente")
        btn_extraer_expediente.clicked.connect(lambda: self.ejecutar_async(self.extraer_datos_expediente()))
        layout.addWidget(btn_extraer_expediente)

        btn_obtener_actuaciones = QPushButton("📥 Obtener Actuaciones")
        btn_obtener_actuaciones.clicked.connect(lambda: self.ejecutar_async(self.obtener_actuaciones()))
        layout.addWidget(btn_obtener_actuaciones)

        btn_comparar_actuaciones = QPushButton("🔄 Comparar Actuaciones")
        btn_comparar_actuaciones.clicked.connect(lambda: self.ejecutar_async(self.comparar_actuaciones()))
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

    def ejecutar_async(self, coroutine):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coroutine)

    def mostrar_mensaje(self, titulo, mensaje):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.exec()

    def obtener_pestaña_activa(self):
        try:
            # Buscar última pestaña no cerrada que contenga 'expediente.seam'
            for page in reversed(self.context.pages):
                if not page.is_closed() and "expediente.seam" in page.url:
                    print(f"✅ Pestaña activa detectada: {page.url}")
                    return page

            # Si no encontró por URL, devuelve la última abierta válida
            pages = [p for p in self.context.pages if not p.is_closed()]
            if pages:
                last_page = pages[-1]
                print(f"⚠️ No se detectó pestaña con expediente.seam. Usando: {last_page.url}")
                return last_page

            self.mostrar_mensaje("Error", "❌ No hay pestañas abiertas.")
            return None
        except Exception as e:
            self.mostrar_mensaje("Error", f"⚠️ No se pudo obtener la pestaña activa: {e}")
            return None

    async def extraer_datos_expediente(self):
        page_expediente = self.obtener_pestaña_activa()
        if not page_expediente:
            return None
        expediente_db = await extraer_datos_expediente(page_expediente)
        if expediente_db:
            mensaje = str(expediente_db)
            self.mostrar_mensaje("Expediente Encontrado", mensaje)
        else:
            self.mostrar_mensaje("Expediente No Encontrado", "No se encontró el expediente en la base de datos.")

    async def obtener_actuaciones(self):
        page_expediente = self.obtener_pestaña_activa()
        if not page_expediente:
            return []
        expediente_datos = await extraer_datos_expediente(page_expediente)
        if expediente_datos:
            actuaciones = await obtener_actuaciones(page_expediente, expediente_datos)
            if not actuaciones:
                self.mostrar_mensaje("Información", "📂 No se encontraron actuaciones en la web.")
            else:
                self.mostrar_mensaje("Información", f"📂 Se descargaron {len(actuaciones)} actuaciones correctamente.")
            return actuaciones
        return []

    async def comparar_actuaciones(self):
        page_expediente = self.obtener_pestaña_activa()
        if not page_expediente:
            return
        expediente_datos = await extraer_datos_expediente(page_expediente)
        if not expediente_datos:
            self.mostrar_mensaje("Error", "❌ No se encontró el expediente en la base de datos.")
            return
        expediente_id = expediente_datos.get("id_expediente")
        if not expediente_id:
            self.mostrar_mensaje("Error", "❌ No se pudo obtener el ID del expediente.")
            return
        actuaciones_nuevas = await obtener_actuaciones(page_expediente, expediente_datos)
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
        self.page.reload()
        self.mostrar_mensaje("Información", "🔄 Página recargada.")

    def cerrar_navegador(self):
        async def cerrar():
            try:
                if self._autologin_cm:
                    await self._autologin_cm.__aexit__(None, None, None)
            except Exception as e:
                print(f"❌ Error al cerrar navegador: {e}")

        asyncio.run(cerrar())
        self.mostrar_mensaje("Información", "🛑 Navegador cerrado.")
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = NavegadorPersonalizado()
    ventana.show()
    sys.exit(app.exec())