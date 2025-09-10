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

   setx PJN_USUARIO "tu_usuario"
   setx PJN_CLAVE "tu_clave"

   Luego cerrá y abrí de nuevo la terminal para que los valores se apliquen.
