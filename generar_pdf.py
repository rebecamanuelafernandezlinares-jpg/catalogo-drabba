"""
Entra a la coleccion drabba-pdf-button, le da click al boton
"DESCARGAR CATALOGO PDF" y captura el archivo que jsPDF genera
y descarga en el navegador. Reintenta varias veces porque el
sitio a veces carga mas lento o con popups intermitentes.
"""
import asyncio
import re
import sys
from playwright.async_api import async_playwright

CATALOGO_URL = "https://drabbalovers.co/collections/drabba-pdf-button"
BOTON_REGEX = re.compile(r"descargar", re.IGNORECASE)
SALIDA = "catalogo.pdf"
INTENTOS = 3
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

# Textos comunes de botones de cierre de popups en Shopify
CERRAR_POPUP_REGEX = re.compile(r"close|cerrar|✕|×|no,? gracias|aceptar", re.IGNORECASE)


async def cerrar_popups_si_hay(page):
    """Intenta cerrar cualquier modal/popup que pueda estar tapando el boton."""
    try:
        cerrar = page.get_by_role("button", name=CERRAR_POPUP_REGEX)
        if await cerrar.count() > 0:
            await cerrar.first.click(timeout=3000)
            await page.wait_for_timeout(1000)
    except Exception:
        pass  # si no hay popup o no se puede cerrar, seguimos normal

    # Tambien probamos con la tecla Escape, que cierra la mayoria de modales
    try:
        await page.keyboard.press("Escape")
    except Exception:
        pass


async def intentar_descarga(page, intento_num):
    print(f"--- Intento {intento_num} de {INTENTOS} ---")
    print(f"Abriendo {CATALOGO_URL} ...")
    await page.goto(CATALOGO_URL, wait_until="load", timeout=60000)
    await page.wait_for_timeout(4000)  # deja asentar banners/cookies/popups

    await cerrar_popups_si_hay(page)

    await page.screenshot(path=f"debug_intento{intento_num}_antes.png", full_page=True)

    boton = page.get_by_text(BOTON_REGEX)
    count = await boton.count()
    print(f"Elementos encontrados con 'descargar': {count}")

    await boton.first.wait_for(state="visible", timeout=20000)
    await boton.first.scroll_into_view_if_needed(timeout=10000)

    print("Haciendo click en el boton de descarga...")
    async with page.expect_download(timeout=180000) as download_info:
        await boton.first.click(timeout=20000, force=False)

    download = await download_info.value
    await download.save_as(SALIDA)
    print(f"PDF guardado en {SALIDA}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1366, "height": 900},
        )
        page = await context.new_page()

        ultimo_error = None
        for intento in range(1, INTENTOS + 1):
            try:
                await intentar_descarga(page, intento)
                ultimo_error = None
                break  # exito, salimos del loop
            except Exception as e:
                ultimo_error = e
                print(f"Intento {intento} fallo: {e}")
                await page.screenshot(path=f"debug_intento{intento}_error.png", full_page=True)
                if intento < INTENTOS:
                    print("Reintentando...")
                    await page.wait_for_timeout(3000)

        await browser.close()

        if ultimo_error is not None:
            raise ultimo_error


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"ERROR generando el PDF: {e}", file=sys.stderr)
        sys.exit(1)
