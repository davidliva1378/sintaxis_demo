from playwright.sync_api import sync_playwright

def iniciar_navegador():
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    return browser, p
