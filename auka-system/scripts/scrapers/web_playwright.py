"""
AUKA - Web Scraper (Playwright)
Extrae HTML completo de páginas web dinámicas.
Usado para: páginas corporativas, landing de eventos.
"""

import asyncio
import logging
from typing import Dict, Optional
from playwright.async_api import async_playwright

logger = logging.getLogger("auka.scraper.web")


class WebScraper:
    """
    Scraper genérico web usando Playwright.
    Extrae HTML completo para procesamiento por el Estructurador.
    """
    
    def __init__(self):
        self.timeout = 30000  # 30 segundos
    
    async def scrape(self, url: str) -> Dict:
        """
        Scrapear página web.
        
        Args:
            url: URL completa de la página
            
        Returns:
            Dict con HTML, título, meta descripción
        """
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                logger.info(f"[WEB] Scrapeando: {url}")
                
                response = await page.goto(url, wait_until="networkidle", timeout=self.timeout)
                
                if response and response.status >= 400:
                    return {
                        "url": url,
                        "error": f"HTTP {response.status}",
                        "html": None,
                        "title": None
                    }
                
                # Extraer datos
                title = await page.title()
                html = await page.content()
                
                # Meta description
                meta_desc = await page.query_selector_eval(
                    'meta[name="description"]',
                    'el => el.content'
                )
                
                # Intentar extraer texto visible
                text_content = await page.evaluate("() => document.body.innerText")
                
                return {
                    "url": url,
                    "title": title,
                    "html": html,
                    "text_content": text_content[:5000] if text_content else None,  # Limitar
                    "meta_description": meta_desc,
                    "status": response.status if response else None,
                    "source": "web"
                }
                
            except Exception as e:
                logger.error(f"[WEB] Error scrapeando {url}: {e}")
                return {
                    "url": url,
                    "error": str(e),
                    "html": None,
                    "title": None
                }
            finally:
                await browser.close()
    
    async def scrape_multiple(self, urls: list) -> list:
        """Scrapear múltiples URLs en secuencia."""
        results = []
        for url in urls:
            result = await self.scrape(url)
            results.append(result)
            await asyncio.sleep(2)  # Delay entre requests
        return results
