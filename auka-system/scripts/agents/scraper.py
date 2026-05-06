"""
AUKA-SCRAPER: Router de scraping. Delega a scrapers especializados.
NO usa LLM. Ejecución pura de Python.
Principio: Ejecuta, recolecta, devuelve. No interpreta.
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional, Any

from scripts.scrapers.google_maps import GoogleMapsScraper
from scripts.scrapers.instagram import InstagramScraper
from scripts.scrapers.web_playwright import WebScraper

logger = logging.getLogger("auka.scraper")


class ScraperAgent:
    """
    Agente Scraper: Router que ejecuta scraping según la fuente.
    NO tiene lógica de negocio - solo orquesta scrapers técnicos.
    """
    
    def __init__(self):
        self.maps_scraper = GoogleMapsScraper()
        self.ig_scraper = InstagramScraper()
        self.web_scraper = WebScraper()
        self.min_delay = 1.5
        self.max_delay = 4.0
    
    async def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecutar tarea de scraping según el tipo.
        
        Args:
            task_data: dict con task, params
            
        Returns:
            dict con status, data, meta
        """
        task = task_data.get("task", "")
        params = task_data.get("params", {})
        
        logger.info(f"[SCRAPER] Ejecutando: {task}")
        
        if task == "search_maps":
            result = await self._execute_maps_search(params)
        elif task == "search_instagram":
            result = await self._execute_instagram(params)
        elif task == "scrape_web":
            result = await self._execute_web(params)
        elif task == "execute_search":
            result = await self._execute_composite_search(params)
        else:
            result = {"status": "error", "data": None, "meta": {"error": f"Tarea '{task}' no soportada"}}
        
        await self._apply_delay()
        return result
    
    async def _execute_maps_search(self, params: Dict) -> Dict:
        """Ejecutar búsqueda en Google Maps."""
        queries = params.get("queries", [])
        location = params.get("location", "")
        limit = params.get("limit", 20)
        
        all_results = []
        errors = []
        
        for query in queries:
            try:
                results = await self.maps_scraper.search(
                    query=f"{query} {location}".strip(),
                    limit=limit
                )
                all_results.extend(results)
                await asyncio.sleep(random.uniform(2, 5))
            except Exception as e:
                logger.error(f"[SCRAPER] Error Maps '{query}': {e}")
                errors.append({"query": query, "error": str(e)})
        
        normalized = [self._normalize_maps_result(r) for r in all_results]
        
        return {
            "status": "success" if normalized else "partial_error",
            "data": normalized,
            "meta": {
                "source": "google_maps",
                "count": len(normalized),
                "queries_executed": len(queries),
                "errors": errors or None
            }
        }
    
    async def _execute_instagram(self, params: Dict) -> Dict:
        """Ejecutar scraping de Instagram."""
        hashtags = params.get("hashtags", [])
        limit = params.get("limit", 15)
        
        all_results = []
        errors = []
        
        for hashtag in hashtags:
            try:
                results = await self.ig_scraper.search_by_hashtag(hashtag=hashtag, limit=limit)
                all_results.extend(results)
                await asyncio.sleep(random.uniform(3, 6))
            except Exception as e:
                logger.error(f"[SCRAPER] Error IG '{hashtag}': {e}")
                errors.append({"hashtag": hashtag, "error": str(e)})
        
        normalized = [self._normalize_instagram_result(r) for r in all_results]
        
        return {
            "status": "success" if normalized else "partial_error",
            "data": normalized,
            "meta": {
                "source": "instagram",
                "count": len(normalized),
                "hashtags_searched": hashtags,
                "errors": errors or None
            }
        }
    
    async def _execute_web(self, params: Dict) -> Dict:
        """Ejecutar scraping web."""
        urls = params.get("urls", [])
        all_results = []
        errors = []
        
        for url in urls:
            try:
                result = await self.web_scraper.scrape(url)
                all_results.append(result)
                await asyncio.sleep(random.uniform(1.5, 3))
            except Exception as e:
                logger.error(f"[SCRAPER] Error web '{url}': {e}")
                errors.append({"url": url, "error": str(e)})
        
        return {
            "status": "success" if all_results else "partial_error",
            "data": all_results,
            "meta": {"source": "web", "count": len(all_results), "errors": errors or None}
        }
    
    async def _execute_composite_search(self, params: Dict) -> Dict:
        """Ejecutar búsqueda compuesta en múltiples fuentes."""
        queries = params.get("queries", [])
        sources = params.get("sources", ["google_maps", "instagram"])
        location = params.get("location", "")
        limit = params.get("limit", 20)
        
        all_results = []
        
        if "google_maps" in sources:
            maps_result = await self._execute_maps_search({
                "queries": queries, "location": location, "limit": limit
            })
            if maps_result["status"] in ("success", "partial_error"):
                all_results.extend(maps_result.get("data", []))
        
        if "instagram" in sources:
            hashtags = [q for q in queries if q.startswith('#')]
            if hashtags:
                ig_result = await self._execute_instagram({"hashtags": hashtags, "limit": limit})
                if ig_result["status"] in ("success", "partial_error"):
                    all_results.extend(ig_result.get("data", []))
        
        return {
            "status": "success",
            "data": all_results,
            "meta": {"source": "composite", "count": len(all_results), "sources_used": sources}
        }
    
    def _normalize_maps_result(self, raw: Dict) -> Dict:
        """Normalizar resultado de Google Maps."""
        return {
            "source": "google_maps",
            "empresa": raw.get("title") or raw.get("name"),
            "direccion": raw.get("address"),
            "telefono": raw.get("phone"),
            "web": raw.get("website"),
            "rating": raw.get("rating"),
            "ciudad": self._extract_city(raw.get("address", "")),
            "raw_data": raw
        }
    
    def _normalize_instagram_result(self, raw: Dict) -> Dict:
        """Normalizar resultado de Instagram."""
        return {
            "source": "instagram",
            "empresa": raw.get("full_name") or raw.get("username"),
            "instagram": f"@{raw.get('username', '')}",
            "bio": raw.get("biography"),
            "telefono": raw.get("contact_phone_number"),
            "email": raw.get("public_email"),
            "web": raw.get("external_url"),
            "posts": raw.get("posts", []),
            "seguidores": raw.get("follower_count"),
            "raw_data": raw
        }
    
    def _extract_city(self, address: str) -> Optional[str]:
        """Extraer ciudad de dirección venezolana."""
        if not address:
            return None
        cities = ["caracas", "valencia", "maracay", "la guaira"]
        address_lower = address.lower()
        for city in cities:
            if city in address_lower:
                return city.title()
        return None
    
    async def _apply_delay(self):
        """Delay aleatorio anti-bloqueo (async, no bloquea event loop)."""
        await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))


# Instancia singleton
scraper_agent = ScraperAgent()
