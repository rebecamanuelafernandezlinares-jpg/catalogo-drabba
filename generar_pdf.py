"""
Entra a la coleccion drabba-pdf-button, le da click al boton
"DESCARGAR CATALOGO PDF" y captura el archivo que jsPDF genera
y descarga en el navegador.
"""
import asyncio
import re
import sys
from playwright.async_api import async_playwright

CATALOGO_URL = "https://drabbalovers.co/collections/drabba-pdf-button"
# Buscamos solo "DESCARGAR" (sin tildes) para evitar problemas de codificacion
# de caracteres acentuados entre el sitio y este script.
BOTON_REGEX = re.compile(r"DRABBA", re.IGNORECASE)
SALIDA = "catalogo.pdf"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1366, "height": 900},
        )
        page = await context.new_page()

        print(f"Abriendo {CATALOGO_URL} ...")
        await page.goto(CATALOGO_URL, wait_until="load", timeout=60000)
        await page.wait_for_timeout(3000)  # deja asentar banners/cookies

        # Screenshot de diagnostico SIEMPRE, para poder ver que carga la pagina
        await page.screenshot(path="debug_antes_click.png", full_page=True)

        print("Buscando el boton de descarga...")
        try:
            boton = page.get_by_text(BOTON_REGEX)
            count = await boton.count()
            print(f"Elementos encontrados con 'DRABBA': {count}")

            await boton.first.wait_for(state="visible", timeout=20000)

            print("Haciendo click en el boton de descarga...")
            # 82 productos con imagenes -> hasta 3 minutos de margen
            async with page.expect_download(timeout=180000) as download_info:
                await boton.first.click(timeout=20000)

            download = await download_info.value
            await download.save_as(SALIDA)
            print(f"PDF guardado en {SALIDA}")

        except Exception:
            # Si algo falla, guarda otra screenshot y el HTML completo
            await page.screenshot(path="debug_error.png", full_page=True)
            html = await page.content()
            with open("debug_html.txt", "w", encoding="utf-8") as f:
                f.write(html)
            raise

        finally:
            await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"ERROR generando el PDF: {e}", file=sys.stderr)
        sys.exit(1)
