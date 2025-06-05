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