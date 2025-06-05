#from src.funciones_v1 import main
from src.expedientes_v1 import *
from src.sincronizacion_v1 import *
from src.actuaciones_v1 import *
from src.procesador_json_v1 import *
from src.procesador_excel import *



# from web.auto_login import iniciar_sesion
# page = iniciar_sesion()



# from web.auto_login import reutilizar_sesion
# from web.monitoreo import capturar_lista_expedientes
#
# # Iniciar sesión o reutilizar la sesión existente
# page = reutilizar_sesion()
#
# if page:  # Verificar que la página se haya iniciado correctamente
#     expedientes = capturar_lista_expedientes(page)
#
# print("✅ Monitoreo finalizado. El navegador permanecerá abierto.")
# while True:
#     pass  # Evita que el navegador se cierre automáticamente


#
# # Intenta reutilizar la sesión guardada
# navegador = reutilizar_sesion()
#
# # Si la sesión ha expirado, se inicia nuevamente
# if navegador is None:
#     navegador = iniciar_sesion()
#
# # 🔹 Mantener la ejecución del script para que el navegador no se cierre
# print("✅ Playwright seguirá corriendo. Cierra el navegador manualmente cuando termines.")
# while True:
#     pass  # Mantiene el programa en ejecución indefinidamente
#



#integrar_expedientes_json_bd()
#actualizar_situacion(2,"PRUEBA_SISTEMA")
#actualizar_caratula(2, "SUPERHIJITUS C/ EL CAZADOR")
#obtener_o_insertar_jurisdiccion("JUSTICIA DIVINA")
#sincronizar_expedientes()



archivo_json = "C:\\Users\\aleja\\OneDrive\\Escritorio\\Proyecto-Descargas\\actuaciones-FGR0005682023.json"
procesar_actuaciones(archivo_json)

# if __name__ == "__main__":
#     funciones_v1.main()  # Llama a la función principal
# archivo_json = "C:\\Users\\aleja\\OneDrive\\Escritorio\\Proyecto-Descargas\\actuaciones-FPA0019432023"
# funciones_v1.procesar_actuaciones(archivo_json)



# id_expediente = 1
# nueva_situacion = "PRÉSTAMO"  # Debe coincidir con la tabla Situaciones
#
# if actualizar_situacion(id_expediente, nueva_situacion):
#     print("✅ Cambio guardado")
# else:
#     print("❌ No se pudo actualizar la situación.")


#from src.expedientes_v1 import cargar_expediente

# nuevo_id = cargar_expediente(
#     numero="FRE 2024-0012",
#     caratula="Caso Tributario",
#     tipo_proceso=None,  # ✅ Se permite que MySQL lo asigne automáticamente
#     situacion_id=4,
#     dependencia_id=5,
#     observacion="Caso sin tipo de proceso definido",
#     fecha_inicio="2024-04-25",
#     fecha_actualizacion="2024-05-01",
#     ultima_actuacion="2024-05-05",
#     jurisdiccion_nombre="Juzgado Federal de San Luis"
# )
# import json
#
# Cargar el archivo JSON
# with open("C:\\Users\\aleja\\OneDrive\\Escritorio\\Proyecto-Descargas\\expedientes.json", "r", encoding="utf-8") as file:
#     json_data = json.load(file)
#
# # Llamar a la función procesar_expedientes para generar el DataFrame
# df_expedientes = procesar_expedientes(json_data)
#
# # Guardar el DataFrame como archivo Excel
# df_expedientes.to_excel("expedientes_procesados.xlsx", index=False, engine="openpyxl")
#
#
# # Llamar a la función para generar el script SQL
# df_expedientes = pd.read_excel("expedientes_procesados.xlsx")
# script_sql = generar_script_insercion_sql_con_dependencias(df_expedientes)
# #
# # # Verificar si la función devolvió un resultado válido
# if script_sql:
#     # Definir la ruta donde guardar el archivo
#     sql_file_path = "insert_expedientes.sql"
#
#     # Guardar el contenido en un archivo SQL
#     with open(sql_file_path, "w", encoding="utf-8") as file:
#         file.write(script_sql)
#
#     print(f"✅ Archivo SQL guardado en: {sql_file_path}")
# else:
#     print("❌ No se generó el script SQL.")
