"""
Entra a la coleccion drabba-pdf-button, le da click al boton
"DESCARGAR CATALOGO PDF" y captura el archivo que jsPDF genera
y descarga en el navegador.
"""
import asyncio
import sys
from playwright.async_api import async_playwright

CATALOGO_URL = "https://drabbalovers.co/collections/drabba-pdf-button"
BOTON_TEXTO = "DESCARGAR CATÁLOGO PDF"
SALIDA = "catalogo.pdf"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"Abriendo {CATALOGO_URL} ...")
        await page.goto(CATALOGO_URL, wait_until="networkidle", timeout=60000)

        print("Haciendo click en el boton de descarga...")
        # 82 productos con imagenes -> hasta 3 minutos de margen
        async with page.expect_download(timeout=180000) as download_info:
            await page.get_by_text(BOTON_TEXTO, exact=False).click()

        download = await download_info.value
        await download.save_as(SALIDA)
        print(f"PDF guardado en {SALIDA}")

        await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"ERROR generando el PDF: {e}", file=sys.stderr)
        sys.exit(1)
