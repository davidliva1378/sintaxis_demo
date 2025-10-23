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

4. Definí **obligatoriamente** las credenciales del PJN como variables de entorno antes de ejecutar cualquier módulo que se conecte al portal.

   En PowerShell (ejecutado una vez):

   setx PJN_USER "tu_usuario"
   setx PJN_PASSWORD "tu_clave"

   Luego cerrá y abrí de nuevo la terminal para que los valores se apliquen.

   📁 Alternativa recomendada para entornos de desarrollo: creá un archivo `.env` en la raíz del proyecto con el siguiente contenido y cargalo con [python-dotenv](https://pypi.org/project/python-dotenv/) u otra herramienta equivalente.

   ```dotenv
   PJN_USER=tu_usuario
   PJN_PASSWORD=tu_clave
   ```

   Asegurate de añadir `.env` al archivo `.gitignore` o a la configuración de tu sistema de control de versiones para que las credenciales nunca se suban al repositorio.

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

🚀 EXTRACCIÓN INICIAL DE EXPEDIENTES V2.0

El Sistema V5 incluye un nuevo flujo mejorado para la incorporación inicial de expedientes al sistema:

**Características principales:**
- Reutiliza el MonitorPJN existente (sin duplicar código)
- Sistema de filtros avanzados con GUI interactiva (4 tipos de filtros combinables)
- Procesamiento por lotes con manejo inteligente de errores
- Exportación dual: JSON + CSV automáticamente
- Umbral configurable de errores consecutivos

**Uso básico (desde directorio Sistema_v5):**

   cd Sistema_v5
   python ejecutar_extraccion_inicial_v2.py

**Opciones avanzadas:**

   # Modo headless (sin navegador visible)
   python ejecutar_extraccion_inicial_v2.py --headless

   # Sin filtros (procesar todos los expedientes)
   python ejecutar_extraccion_inicial_v2.py --no-filtros

   # Umbral de errores personalizado
   python ejecutar_extraccion_inicial_v2.py --umbral-errores 10

📖 Para más información, consultá la guía completa en:
   Sistema_v5/docs/GUIA_EXTRACCION_INICIAL_V2.md

🔒 RECOMENDACIONES DE SEGURIDAD Y DESPLIEGUE

- Nunca hardcodees `PJN_USER` ni `PJN_PASSWORD` en scripts, notebooks o archivos de configuración versionados.
- Para despliegues en servidores, contenedores o servicios CI/CD, usá los mecanismos nativos de gestión de secretos (por ejemplo, variables protegidas en GitHub Actions, GitLab CI, Docker secrets o cofres de la nube) en lugar de archivos planos.
- Si usás archivos `.env` en producción, almacenalos fuera del repositorio, aplicá permisos restrictivos (por ejemplo, sólo lectura para el usuario del servicio) y rotá las credenciales periódicamente.
- Considerá habilitar el paquete `python-dotenv` o soluciones equivalentes para cargar automáticamente las variables durante la inicialización de la aplicación, evitando imprimir o registrar los valores en texto plano.
