import os
os.environ["PWDEBUG"] = "0"  # 🔹 Desactiva el modo depuración automático
os.environ["PLAYWRIGHT_DISABLE_HOOKS"] = "1"  # 🔹 Desactiva los hooks de depuración
import json
from playwright.sync_api import sync_playwright

# 🔐 Mejora: Mueve credenciales a variables de entorno (no las hardcodees)
USUARIO = os.getenv("PJN_USUARIO", "20213071662")
CONTRASEÑA = os.getenv("PJN_CLAVE", "surrey1970")

URL_LOGIN = "https://portalpjn.pjn.gov.ar/inicio"
SELEC_USUARIO = "input[name='username']"
SELEC_CLAVE = "input[name='password']"
SELEC_BOTON = "#kc-login"
SELEC_CONFIRMACION = "text='Menú'"

SESSION_FILE = "estado_sesion.json"

p = sync_playwright().start()  # Iniciar Playwright


def guardar_sesion(context):
    """Guarda cookies y localStorage para reutilizar la sesión."""
    storage = context.storage_state()
    with open(SESSION_FILE, "w") as f:
        json.dump(storage, f)
    print("✅ Estado de sesión guardado correctamente.")


def iniciar_sesion():
    """Inicia sesión en el Portal PJN asegurando que Playwright no sea detectado."""
    browser = p.chromium.launch(
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-web-security",  # 🔹 Evita bloqueos de seguridad entre pestañas
            "--remote-debugging-port=9222",  # 🔹 Previene bloqueos de depuración
        ]
    )

    context = browser.new_context()

    # 🔹 Eliminamos detección de Playwright antes de navegar
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    """)

    page = context.new_page()
    page.goto(URL_LOGIN)

    print("🔄 Esperando que la página cargue...")
    page.wait_for_load_state("domcontentloaded")  # ✅ Esperar que cargue completamente

    print("🔍 Verificando disponibilidad de campos...")
    try:
        page.wait_for_selector(SELEC_USUARIO, timeout=10000)
        page.wait_for_selector(SELEC_CLAVE, timeout=10000)
        page.wait_for_selector(SELEC_BOTON, timeout=10000)
    except:
        print("⚠️ No se encontraron los campos de login. La página podría haber cambiado.")
        return None

    print("🔐 Ingresando usuario y contraseña...")
    page.fill(SELEC_USUARIO, USUARIO)
    page.fill(SELEC_CLAVE, CONTRASEÑA)

    print("✅ Credenciales ingresadas. Presionando botón de login...")
    try:
        page.click(SELEC_BOTON)
    except:
        print("⚠️ Error al hacer clic en el botón de login.")
        return None

    print("⏳ Esperando confirmación de sesión iniciada...")
    try:
        page.wait_for_selector(SELEC_CONFIRMACION, timeout=60000)
        print("✅ Login exitoso.")
        guardar_sesion(context)
    except:
        print("⚠️ No se encontró el menú. Verifica si el login fue exitoso.")
        return None

    print("✅ El navegador permanecerá abierto. Ciérralo manualmente cuando termines.")
    return page


def reutilizar_sesion():
    """Reutiliza la sesión guardada y devuelve la página activa."""
    if not os.path.exists(SESSION_FILE):
        print("⚠️ No hay sesión guardada. Ejecuta iniciar_sesion() manualmente.")
        return iniciar_sesion()

    print("🔄 Reutilizando sesión guardada...")
    browser = p.chromium.launch(
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-gpu"
        ]
    )

    with open(SESSION_FILE, "r") as f:
        storage_state = json.load(f)

    context = browser.new_context(storage_state=storage_state)

    # 🔹 Aplicamos nuevamente los cambios para evitar detección
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    """)

    page = context.new_page()
    page.goto(URL_LOGIN)

    try:
        page.wait_for_selector(SELEC_CONFIRMACION, timeout=30000)
        print("✅ Sesión activa, acceso exitoso.")
    except:
        print("⚠️ La sesión ha expirado. Ejecuta iniciar_sesion() nuevamente.")
        return iniciar_sesion()

    print("✅ El navegador permanecerá abierto. Ciérralo manualmente cuando termines.")
    return page

# import os
# import json
# from playwright.sync_api import sync_playwright
#
# # ⚠️ Mejor guardar estos datos en un archivo .env o base de datos en lugar de hardcodearlos
# USUARIO = "20213071662"
# CONTRASEÑA = "surrey1970"
#
# URL_LOGIN = "https://portalpjn.pjn.gov.ar/inicio"
# SELEC_USUARIO = "input[name='username']"
# SELEC_CLAVE = "input[name='password']"
# SELEC_BOTON = "#kc-login"
#
# # 🔹 Selector del menú como indicador de sesión iniciada
# SELEC_CONFIRMACION = "text='Menú'"
#
# SESSION_FILE = "estado_sesion.json"
#
# p = sync_playwright().start()  # Iniciar Playwright de manera persistente
#
# def guardar_sesion(context):
#     """Guarda cookies y localStorage para reutilizar la sesión."""
#     storage = context.storage_state()
#     with open(SESSION_FILE, "w") as f:
#         json.dump(storage, f)
#     print("✅ Estado de sesión guardado correctamente.")
#
# def iniciar_sesion():
#     """Inicia sesión en el Portal PJN y devuelve la página activa."""
#     browser = p.chromium.launch(headless=False)  # 🚀 Mantener interfaz visible
#     context = browser.new_context()
#     page = context.new_page()
#
#     page.goto(URL_LOGIN)
#
#     print("🔐 Iniciando sesión con usuario y contraseña...")
#     page.fill(SELEC_USUARIO, USUARIO)
#     page.fill(SELEC_CLAVE, CONTRASEÑA)
#
#     page.wait_for_selector(SELEC_BOTON, timeout=30000)
#     page.click(SELEC_BOTON)
#     print("✅ Botón de login presionado")
#
#     # 🔹 Esperamos el menú como indicador de sesión iniciada
#     try:
#         page.wait_for_selector(SELEC_CONFIRMACION, timeout=60000)
#         print("✅ Login exitoso. Se detectó el menú.")
#         guardar_sesion(context)
#     except:
#         print("⚠️ No se encontró el menú. Verifica si el login fue exitoso.")
#
#     print("✅ El navegador permanecerá abierto. Ciérralo manualmente cuando termines.")
#
#     return page  # 🔹 Devuelve la página en lugar del navegador
#
# def reutilizar_sesion():
#     """Reutiliza la sesión guardada y devuelve la página activa."""
#     if not os.path.exists(SESSION_FILE):
#         print("⚠️ No hay sesión guardada. Ejecuta iniciar_sesion() manualmente.")
#         return iniciar_sesion()
#
#     print("🔄 Reutilizando sesión guardada...")
#     browser = p.chromium.launch(headless=False)  # 🚀 Mantener interfaz visible
#
#     with open(SESSION_FILE, "r") as f:
#         storage_state = json.load(f)
#
#     context = browser.new_context(storage_state=storage_state)
#     page = context.new_page()  # 🔹 Aquí se crea la `page` correctamente
#
#     page.goto(URL_LOGIN)
#
#     # Verificar si la sesión sigue activa
#     try:
#         page.wait_for_selector(SELEC_CONFIRMACION, timeout=30000)  # Ajusta el selector según sea necesario
#         print("✅ Sesión activa, acceso exitoso.")
#     except:
#         print("⚠️ La sesión ha expirado. Ejecuta iniciar_sesion() nuevamente.")
#         return iniciar_sesion()
#
#     print("✅ El navegador permanecerá abierto. Ciérralo manualmente cuando termines.")
#
#     return page  # 🔹 Devuelve `page`, no `browser`
