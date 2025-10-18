📘 INSTRUCCIONES DE INSTALACIÓN DEL PROYECTO JURÍDICO

1. ABRÍ PowerShell como ADMINISTRADOR.
2. Navegá a la carpeta del proyecto:

   cd "C:\Users\aleja\Documents\Sistema"

3. Ejecutá el script de instalación:

   .\setup.ps1

⚙️ Este script hará lo siguiente:
- Crear el entorno virtual (.venv)
- Activarlo
- Instalar todos los paquetes del archivo requirements.txt
- Instalar Chromium para usar con Playwright

📌 NOTA: si tenés problemas al activar el entorno, usá este comando primero:
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

4. Definí las variables de entorno requeridas para el acceso al PJN:

   En PowerShell (ejecutado una vez):

   setx PJN_USER "tu_usuario"
   setx PJN_PASSWORD "tu_clave"

   Luego cerrá y abrí de nuevo la terminal para que los valores se apliquen.

🗂️ DOCUMENTACIÓN DEL SISTEMA V4

- Toda la documentación nueva relacionada con el Sistema V4 debe guardarse en el directorio `Sistema_v4/documentacion/`.
- Utilizá el archivo `Sistema_v4/documentacion/README.md` como guía para el formato y convenciones de los documentos futuros.

🧩 CONFIGURACIÓN INICIAL DEL SISTEMA V5

1. Personalizá las plantillas `config/sistema.json` y `config/monitor.json`.
   - Ambos archivos incluyen comentarios (claves que comienzan con `__`) para guiar los ajustes.
   - Las claves comentadas se ignoran automáticamente al cargar la configuración, por lo que podés dejarlas como referencia.
   - Actualizá rutas, intervalos y preferencias antes de ejecutar los módulos del sistema.

2. Creá la estructura de carpetas esperada por `SystemConfig` ejecutando el script de inicialización:

   ```bash
   python Sistema_v5/inicializar_directorios.py
   ```

   El script toma los directorios definidos en `config/sistema.json`, los resuelve respecto a la raíz del proyecto y crea los que falten.

3. Después de personalizar los archivos de configuración podés volver a ejecutar el script cuando cambies rutas o agregues nuevos directorios.
