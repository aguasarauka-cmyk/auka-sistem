"""
AUKA - Google Maps Scraper
Extrae empresas desde búsquedas de Google Maps usando Playwright.
Técnica: Scroll infinito con carga dinámica.
Anti-bloqueo: User-agent real, delays progresivos, aceptación de cookies.
"""

import asyncio
import logging
import random
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page

logger = logging.getLogger("auka.scraper.maps")


class GoogleMapsScraper:
    """
    Scraper especializado para Google Maps.
    Extrae: nombre, dirección, teléfono, web, rating, coordenadas.
    """
    
    BASE_URL = "https://www.google.com/maps/search/"
    
    # User agents rotativos
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ]
    
    def __init__(self):
        self.delay_min = 1.5
        self.delay_max = 4.0
    
    async def search(self, query: str, limit: int = 20, location_hint: str = "Venezuela") -> List[Dict]:
        """
        Buscar empresas en Google Maps.
        
        Args:
            query: Término de búsqueda (ej: "productoras de eventos caracas")
            limit: Máximo de resultados
            location_hint: Hint de ubicación para forzar búsqueda en Venezuela
            
        Returns:
            Lista de dicts con datos de empresas
        """
        results = []
        seen_titles = set()
        
        # Usar query directamente, sin forzar "Venezuela" (rompe la búsqueda de Maps)
        # En su lugar, usamos locale es-VE y el parámetro near para geolocalización
        forced_query = query
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=random.choice(self.USER_AGENTS),
                viewport={"width": 1920, "height": 1080},
                locale="es-VE",
                geolocation={"latitude": 10.4806, "longitude": -66.9036},  # Caracas
                permissions=["geolocation"]
            )
            page = await context.new_page()
            
            try:
                search_url = f"{self.BASE_URL}{forced_query.replace(' ', '+')}/?hl=es-419"
                if location_hint:
                    search_url += f"&near={location_hint.replace(' ', '+')}"
                    
                logger.info(f"[MAPS] Navegando: {search_url}")
                
                await page.goto(search_url, wait_until="domcontentloaded")
                await asyncio.sleep(3)
                
                # Aceptar cookies de Google si aparecen
                await self._accept_cookies(page)
                
                # Esperar resultados
                try:
                    await page.wait_for_selector('div[role="feed"]', timeout=15000)
                except Exception:
                    # Intentar buscar resultados con selector alternativo
                    try:
                        await page.wait_for_selector('div.Nv2PK', timeout=10000)
                    except Exception:
                        logger.warning(f"[MAPS] No se encontraron resultados para: {forced_query}")
                        return []
                
                # Scroll progresivo
                scroll_attempts = 0
                max_attempts = min(limit // 3 + 2, 15)
                prev_count = 0
                
                while len(results) < limit and scroll_attempts < max_attempts:
                    # Extraer tarjetas visibles con múltiples selectores
                    cards = await page.query_selector_all('div[role="feed"] > div > div > a[href*="maps"]')
                    if not cards:
                        cards = await page.query_selector_all('div.Nv2PK')
                    
                    for card in cards:
                        if len(results) >= limit:
                            break
                        
                        try:
                            data = await self._extract_card_data(page, card)
                            if data and data.get("title"):
                                # Deduplicar
                                title_key = (data["title"] or "").lower().strip()
                                if title_key and title_key not in seen_titles:
                                    seen_titles.add(title_key)
                                    data["query_used"] = forced_query
                                    results.append(data)
                        except Exception as e:
                            logger.debug(f"[MAPS] Error extrayendo card: {e}")
                    
                    # Si no encontramos más resultados, salir
                    if len(results) == prev_count:
                        scroll_attempts += 2  # Acelerar salida
                    prev_count = len(results)
                    
                    # Scroll en el feed
                    try:
                        await page.evaluate("""
                            const feed = document.querySelector('div[role="feed"]');
                            if (feed) feed.scrollBy(0, 800);
                        """)
                    except Exception:
                        pass
                    
                    await asyncio.sleep(random.uniform(2, 4))
                    scroll_attempts += 1
                
            except Exception as e:
                logger.error(f"[MAPS] Error en búsqueda: {e}")
            finally:
                await browser.close()
        
        logger.info(f"[MAPS] '{forced_query}': {len(results)} empresas extraídas")
        return results[:limit]
    
    async def _accept_cookies(self, page: Page):
        """Aceptar cookies de Google si aparecen."""
        try:
            # Esperar un poco por el popup
            await asyncio.sleep(1)
            
            # Buscar botón de aceptar cookies (múltiples idiomas)
            cookie_selectors = [
                'button:has-text("Aceptar todo")',
                'button:has-text("Accept all")',
                'button:has-text("Rechazar todo")',  # Usar rechazar si no hay aceptar
                'form[action*="consent"] button',
                'button[aria-label*="Accept"]',
                'button[aria-label*="Aceptar"]',
            ]
            
            for sel in cookie_selectors:
                try:
                    btn = await page.query_selector(sel)
                    if btn:
                        await btn.click()
                        await asyncio.sleep(2)
                        logger.debug("[MAPS] Cookies aceptadas")
                        return
                except Exception:
                    continue
        except Exception:
            pass
    
    async def _extract_card_data(self, page: Page, card) -> Optional[Dict]:
        """Extraer datos de una tarjeta de resultado."""
        try:
            # Click para abrir detalle
            await card.click()
            await asyncio.sleep(random.uniform(1.5, 2.5))
            
            # Extraer título
            title = None
            title_selectors = [
                'h1.DUwDvf',
                'h1[class*="fontHeadlineLarge"]',
                'div[role="main"] h1',
            ]
            for sel in title_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        title = (await el.text_content() or "").strip()
                        if title:
                            break
                except Exception:
                    continue
            
            if not title:
                return None
            
            # Extraer dirección
            address = await self._get_detail_field(page, [
                'button[data-item-id="address"]',
                'button[aria-label*="irección"]',
                'button[aria-label*="ddress"]',
            ])
            
            # Extraer teléfono
            phone = await self._get_detail_field(page, [
                'button[data-item-id*="phone"]',
                'button[aria-label*="eléfono"]',
                'button[aria-label*="hone"]',
            ])
            
            # Extraer sitio web
            website = await self._get_detail_field(page, [
                'a[data-item-id="authority"]',
                'button[data-item-id="authority"]',
                'a[aria-label*="itio web"]',
                'a[aria-label*="ebsite"]',
            ])
            
            # Rating
            rating = None
            try:
                rating_el = await page.query_selector('div.F7nice span[aria-hidden="true"]')
                if not rating_el:
                    rating_el = await page.query_selector('div[class*="fontDisplayLarge"]')
                if rating_el:
                    rating_text = await rating_el.text_content()
                    if rating_text:
                        rating = float(rating_text.strip().replace(',', '.'))
            except Exception:
                pass
            
            # Categoría
            category = None
            try:
                cat_el = await page.query_selector('button[jsaction*="category"]')
                if cat_el:
                    category = (await cat_el.text_content() or "").strip()
            except Exception:
                pass
            
            return {
                "title": title,
                "address": self._clean_aria_label(address),
                "phone": self._clean_aria_label(phone),
                "website": self._clean_website(website),
                "rating": rating,
                "category": category,
                "source": "google_maps",
            }
            
        except Exception as e:
            logger.debug(f"[MAPS] Error en card: {e}")
            return None
    
    async def _get_detail_field(self, page: Page, selectors: List[str]) -> Optional[str]:
        """Extraer campo por múltiples selectores."""
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    # Try aria-label first (most reliable)
                    label = await el.get_attribute("aria-label")
                    if label:
                        return label
                    # Then text content
                    text = await el.text_content()
                    if text:
                        return text.strip()
            except Exception:
                continue
        return None
    
    def _clean_aria_label(self, text: Optional[str]) -> Optional[str]:
        """Limpiar aria-label quitando prefijos descriptivos."""
        if not text:
            return None
        # Remove common prefixes like "Dirección: ", "Teléfono: "
        prefixes = ["Dirección: ", "Address: ", "Teléfono: ", "Phone: ", 
                     "Sitio web: ", "Website: ", "Cómo llegar: "]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):]
        return text.strip() or None
    
    def _clean_website(self, text: Optional[str]) -> Optional[str]:
        """Limpiar URL de website."""
        if not text:
            return None
        text = self._clean_aria_label(text)
        if not text:
            return None
        # If it's a full aria label, extract just the URL part
        if " " in text:
            parts = text.split()
            for part in parts:
                if "." in part and "/" not in part[:5]:
                    return part
            return parts[0]
        return text
