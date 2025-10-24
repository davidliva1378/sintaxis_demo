from PySide6.QtCore import QThread, Signal
from web.auto_login import reutilizar_sesion_async


class VerificadorNotificaciones(QThread):
    resultado = Signal(object)

    def run(self):
        import asyncio
        asyncio.run(self.verificar_async())

    async def verificar_async(self):
        from notificaciones_v2.notificaciones_control_v4_async import actualizar_notificaciones_nuevas
        import os
        async with reutilizar_sesion_async() as (page, context, browser):
            if page:
                destino = os.path.abspath(os.path.join(os.getcwd(), "datos_extraidos", "monitoreo"))
                nuevas = await actualizar_notificaciones_nuevas(page, destino=destino)
                self.resultado.emit(nuevas)
            else:
                self.resultado.emit(None)
