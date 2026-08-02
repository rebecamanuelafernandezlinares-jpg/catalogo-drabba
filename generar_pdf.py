"""
Entra a la colección drabba-pdf-button, hace clic en el botón
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


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True
        )

        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1366, "height": 900},
            accept_downloads=True,
        )

        page = await context.new_page()

        try:
            print(f"Abriendo {CATALOGO_URL}...")

            await page.goto(
                CATALOGO_URL,
                wait_until="networkidle",
                timeout=60000,
            )

            await page.wait_for_timeout(5000)

            # Captura de diagnóstico
            await page.screenshot(
                path="debug_antes_click.png",
                full_page=True,
            )

            print("Esperando el botón...")

            await page.wait_for_selector(
                'button[id^="drabbaPdfBtn"]',
                timeout=60000,
            )

            boton = page.locator('button[id^="drabbaPdfBtn"]')

            cantidad = await boton.count()
            print(f"Botones encontrados: {cantidad}")

            await boton.first.scroll_into_view_if_needed()

            await boton.first.wait_for(
                state="visible",
                timeout=60000,
            )

            print("Haciendo clic...")

            async with page.expect_download(timeout=180000) as download_info:
                await boton.first.click(force=True)

            download = await download_info.value
            await download.save_as(SALIDA)

            print(f"PDF guardado como {SALIDA}")

        except Exception as e:
            print(f"ERROR: {e}")

            await page.screenshot(
                path="debug_error.png",
                full_page=True,
            )

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
