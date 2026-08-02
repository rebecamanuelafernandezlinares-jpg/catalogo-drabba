"""
Entra a la colección drabba-pdf-button, ABRE el cart drawer (el botón vive
ahí dentro y está oculto por CSS hasta que el drawer se abre), hace clic en
"DESCARGAR CATÁLOGO PDF" y captura el archivo descargado.
"""
import asyncio
import sys
from playwright.async_api import async_playwright
 
CATALOGO_URL = "https://drabbalovers.co/collections/drabba-pdf-button"
SALIDA = "catalogo.pdf"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)
 
 
async def buscar_boton(page):
    """Intenta localizar el botón por varios selectores posibles."""
    candidatos = [
        'button[id^="drabbaPdfBtn"]',
        'a[id^="drabbaPdfBtn"]',
        'text=/descargar cat[aá]logo pdf/i',
    ]
    for sel in candidatos:
        loc = page.locator(sel)
        if await loc.count() > 0:
            return loc.first
    return None
 
 
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1366, "height": 900},
            accept_downloads=True,
        )
        page = await context.new_page()
        try:
            print(f"Abriendo {CATALOGO_URL}...")
            await page.goto(CATALOGO_URL, wait_until="domcontentloaded", timeout=60000)
            # No confiamos en networkidle: muchos sitios con chat/pixeles nunca llegan a idle.
            await page.wait_for_timeout(4000)
 
            # 1) Buscar directo, por si el botón ya está visible en la página.
            boton = await buscar_boton(page)
            if boton is not None and await boton.is_visible():
                print("Botón visible directamente en la página.")
            else:
                print("No visible aún. Intentando abrir el cart drawer...")
                # 2) Abrir el drawer del carrito (el botón vive ahí dentro).
                abrio = False
                for sel in [
                    'a[href="/cart"]',
                    '[data-cart-icon]',
                    'button[aria-label*="cart" i]',
                    'button[aria-label*="carrito" i]',
                    '#cart-icon-bubble',
                ]:
                    icono = page.locator(sel).first
                    if await icono.count() > 0:
                        try:
                            await icono.click(timeout=5000, force=True)
                            abrio = True
                            break
                        except Exception:
                            continue
 
                if abrio:
                    await page.wait_for_timeout(2000)
                    boton = await buscar_boton(page)
 
            await page.screenshot(path="debug_antes_click.png", full_page=True)
 
            if boton is None:
                # Volcado de diagnóstico si seguimos sin encontrarlo.
                with open("debug_html.txt", "w", encoding="utf-8") as f:
                    f.write(await page.content())
                raise RuntimeError(
                    "No se encontró el botón ni en la página ni dentro del cart drawer. "
                    "Revisa debug_html.txt buscando 'drabbaPdfBtn' o 'Descargar' para ver "
                    "en qué contenedor real vive (puede requerir otro selector)."
                )
 
            await boton.scroll_into_view_if_needed()
 
            print("Haciendo clic (sin exigir visibilidad, con force)...")
            async with page.expect_download(timeout=180000) as download_info:
                await boton.click(force=True, timeout=15000)
            download = await download_info.value
            await download.save_as(SALIDA)
            print(f"PDF guardado como {SALIDA}")
 
        except Exception as e:
            print(f"ERROR: {e}")
            await page.screenshot(path="debug_error.png", full_page=True)
            with open("debug_html.txt", "w", encoding="utf-8") as f:
                f.write(await page.content())
            raise
        finally:
            await browser.close()
 
 
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"ERROR generando el PDF: {e}", file=sys.stderr)
        sys.exit(1)
