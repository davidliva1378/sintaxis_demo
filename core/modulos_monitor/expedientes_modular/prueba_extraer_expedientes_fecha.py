
import asyncio
from datetime import datetime
from core.modulos_monitor.expedientes_modular.extraer_expedientes_por_fecha import ir_a_consultas_tras_login

if __name__ == "__main__":
    fecha_input = input("📅 Ingresá la fecha de corte (DD/MM/AAAA) [Enter para usar la de hoy]: ").strip()
    if not fecha_input:
        fecha_input = datetime.today().strftime('%d/%m/%Y')
    asyncio.run(ir_a_consultas_tras_login(fecha_corte=fecha_input))
