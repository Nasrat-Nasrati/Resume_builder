"""Isolated Chromium PDF rendering; render input is immutable and network-free."""
import asyncio
from .templates import render_html

MAX_RENDER_INPUT_BYTES = 1_200_000
RENDER_TIMEOUT_MS = 30_000

async def _block_network(route):
    if route.request.url.startswith(("http://", "https://", "ws://", "wss://")):
        await route.abort()
    else:
        await route.continue_()

async def _render(payload):
    from playwright.async_api import async_playwright
    html = render_html(payload)
    if len(html.encode("utf-8")) > MAX_RENDER_INPUT_BYTES:
        raise ValueError("CV content exceeds the supported PDF size.")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            context = await browser.new_context(service_workers="block", accept_downloads=False)
            await context.route("**/*", _block_network)
            page = await context.new_page()
            page.set_default_timeout(RENDER_TIMEOUT_MS)
            await page.set_content(html, wait_until="load", timeout=RENDER_TIMEOUT_MS)
            await page.evaluate("document.fonts.ready")
            return await asyncio.wait_for(page.pdf(format="A4", print_background=True, prefer_css_page_size=True), timeout=RENDER_TIMEOUT_MS / 1000)
        finally:
            await browser.close()

def render_cv_pdf(payload):
    return asyncio.run(_render(payload))
