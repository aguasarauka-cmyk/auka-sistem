"""
AUKA - Instagram Scraper
Extrae perfiles y posts desde Instagram.
Técnica: Playwright con login de sesión persistente.
Anti-bloqueo: Delays aleatorios, sesión persistente, rotación UA, viewport móvil.
"""

import asyncio
import logging
import random
import json
import os
from typing import List, Dict, Optional
from playwright.async_api import async_playwright

from config.settings import settings

logger = logging.getLogger("auka.scraper.instagram")


class InstagramScraper:
    """
    Scraper especializado para Instagram.
    Extrae: bio, posts, captions, contactos, seguidores.
    
    Usa credenciales desde variables de entorno:
    - INSTAGRAM_USERNAME
    - INSTAGRAM_PASSWORD
    """
    
    BASE_URL = "https://www.instagram.com"
    
    USER_AGENTS = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    ]
    
    def __init__(self):
        self.username = settings.INSTAGRAM_USERNAME
        self.password = settings.INSTAGRAM_PASSWORD
        self.session_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        self.session_file = os.path.join(self.session_dir, "instagram_session.json")
        self.delay_min = 3.0
        self.delay_max = 7.0
        
        # Ensure data directory exists
        os.makedirs(self.session_dir, exist_ok=True)
    
    async def _login(self, page) -> bool:
        """
        Login a Instagram con credenciales.
        Guarda sesión en archivo para reutilizar.
        """
        if not self.username or not self.password:
            logger.warning("[IG] Sin credenciales de Instagram configuradas")
            return False
        
        try:
            logger.info(f"[IG] Intentando login como @{self.username}")
            await page.goto(f"{self.BASE_URL}/accounts/login/", wait_until="networkidle")
            await asyncio.sleep(random.uniform(2, 4))
            
            # Aceptar cookies si aparece
            try:
                cookie_btn = await page.query_selector('button:has-text("Allow"), button:has-text("Permitir"), button:has-text("Accept")')
                if cookie_btn:
                    await cookie_btn.click()
                    await asyncio.sleep(1)
            except Exception:
                pass
            
            # Llenar username
            username_input = await page.wait_for_selector('input[name="username"]', timeout=10000)
            await username_input.fill("")
            await asyncio.sleep(0.5)
            await username_input.type(self.username, delay=random.randint(50, 150))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Llenar password
            password_input = await page.query_selector('input[name="password"]')
            await password_input.fill("")
            await asyncio.sleep(0.5)
            await password_input.type(self.password, delay=random.randint(50, 150))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Click login
            login_btn = await page.query_selector('button[type="submit"]')
            if login_btn:
                await login_btn.click()
            
            await asyncio.sleep(random.uniform(5, 8))
            
            # Verificar login exitoso (no estamos en la página de login)
            current_url = page.url
            if "/accounts/login" not in current_url:
                logger.info("[IG] Login exitoso")
                
                # Manejar "Guardar info" popup
                try:
                    not_now = await page.query_selector('button:has-text("Ahora no"), button:has-text("Not Now")')
                    if not_now:
                        await not_now.click()
                        await asyncio.sleep(2)
                except Exception:
                    pass
                
                # Manejar "Activar notificaciones" popup
                try:
                    not_now2 = await page.query_selector('button:has-text("Ahora no"), button:has-text("Not Now")')
                    if not_now2:
                        await not_now2.click()
                        await asyncio.sleep(1)
                except Exception:
                    pass
                
                return True
            else:
                logger.error("[IG] Login falló - aún en página de login")
                # Check for error messages
                try:
                    error_el = await page.query_selector('#slfErrorAlert, p[data-testid="login-error-message"]')
                    if error_el:
                        error_text = await error_el.text_content()
                        logger.error(f"[IG] Error de login: {error_text}")
                except Exception:
                    pass
                return False
                
        except Exception as e:
            logger.error(f"[IG] Error durante login: {e}")
            return False
    
    async def _create_browser_context(self, playwright):
        """Crear contexto de browser con sesión persistente."""
        browser = await playwright.chromium.launch(headless=True)
        
        # Intentar cargar sesión existente
        storage_state = None
        if os.path.exists(self.session_file):
            try:
                storage_state = self.session_file
                logger.info("[IG] Cargando sesión guardada")
            except Exception:
                storage_state = None
        
        context_options = {
            "user_agent": random.choice(self.USER_AGENTS),
            "viewport": {"width": 390, "height": 844},
            "locale": "es-VE",
        }
        
        if storage_state:
            context_options["storage_state"] = storage_state
        
        context = await browser.new_context(**context_options)
        return browser, context
    
    async def _ensure_logged_in(self, page, context) -> bool:
        """Verificar si hay sesión activa, si no, hacer login."""
        try:
            await page.goto(self.BASE_URL, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            # Check if we're logged in
            if "/accounts/login" in page.url:
                logger.info("[IG] No hay sesión activa, haciendo login...")
                success = await self._login(page)
                if success:
                    # Guardar sesión
                    try:
                        await context.storage_state(path=self.session_file)
                        logger.info("[IG] Sesión guardada")
                    except Exception as e:
                        logger.warning(f"[IG] No se pudo guardar sesión: {e}")
                return success
            
            logger.info("[IG] Sesión activa detectada")
            return True
            
        except Exception as e:
            logger.error(f"[IG] Error verificando sesión: {e}")
            return False
    
    async def search_by_hashtag(self, hashtag: str, limit: int = 15) -> List[Dict]:
        """
        Buscar posts por hashtag.
        
        Args:
            hashtag: Hashtag sin # (ej: "eventoscaracas")
            limit: Máximo de posts
            
        Returns:
            Lista de posts con datos del perfil
        """
        results = []
        tag = hashtag.lstrip('#')
        
        async with async_playwright() as p:
            browser, context = await self._create_browser_context(p)
            page = await context.new_page()
            
            try:
                # Asegurar login
                logged_in = await self._ensure_logged_in(page, context)
                if not logged_in:
                    logger.warning("[IG] Continuando sin login (resultados limitados)")
                
                url = f"{self.BASE_URL}/explore/tags/{tag}/"
                logger.info(f"[IG] Buscando hashtag: #{tag}")
                await page.goto(url, wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(3, 5))
                
                # Verificar si la página cargó correctamente
                page_text = await page.text_content("body")
                if "no se encontraron" in (page_text or "").lower() or "sorry" in (page_text or "").lower():
                    logger.info(f"[IG] Hashtag #{tag} sin resultados")
                    return []
                
                # Extraer posts
                posts = await page.query_selector_all('article a[href*="/p/"]')
                
                for post in posts[:limit]:
                    try:
                        await post.click()
                        await asyncio.sleep(random.uniform(2, 4))
                        
                        # Extraer datos del post modal
                        post_data = await self._extract_post_data(page)
                        if post_data:
                            post_data["hashtag"] = hashtag
                            results.append(post_data)
                        
                        # Cerrar modal
                        try:
                            close_btn = await page.query_selector('[aria-label="Cerrar"], [aria-label="Close"], svg[aria-label="Cerrar"]')
                            if close_btn:
                                await close_btn.click()
                                await asyncio.sleep(1)
                            else:
                                await page.keyboard.press("Escape")
                                await asyncio.sleep(1)
                        except Exception:
                            await page.keyboard.press("Escape")
                            await asyncio.sleep(1)
                            
                    except Exception as e:
                        logger.debug(f"[IG] Error en post: {e}")
                        try:
                            await page.keyboard.press("Escape")
                            await asyncio.sleep(1)
                        except Exception:
                            pass
                
                logger.info(f"[IG] #{tag}: {len(results)} posts extraídos")
                
            except Exception as e:
                logger.error(f"[IG] Error en búsqueda hashtag #{tag}: {e}")
            finally:
                # Guardar sesión antes de cerrar
                try:
                    await context.storage_state(path=self.session_file)
                except Exception:
                    pass
                await browser.close()
        
        return results
    
    async def _extract_post_data(self, page) -> Optional[Dict]:
        """Extraer datos de un post abierto en modal."""
        try:
            # Username
            username = ""
            username_selectors = [
                'a[class*="notranslate"]',
                'header a[href*="/"]',
                'span a[href*="/"]',
            ]
            for sel in username_selectors:
                el = await page.query_selector(sel)
                if el:
                    username = (await el.text_content() or "").strip()
                    if username and username != "":
                        break
            
            # Caption
            caption = ""
            caption_selectors = [
                'div[class*="_a9zs"]',
                'span[class*="_a9zs"]',
                'div[class*="C4VMK"] span',
            ]
            for sel in caption_selectors:
                el = await page.query_selector(sel)
                if el:
                    caption = (await el.text_content() or "").strip()
                    if caption:
                        break
            
            if not username and not caption:
                return None
            
            return {
                "username": username.strip().lstrip('@'),
                "caption": caption[:1000],  # Limit caption length
                "source": "instagram"
            }
        except Exception as e:
            logger.debug(f"[IG] Error extrayendo post: {e}")
            return None
    
    async def scrape_profile(self, username: str) -> Dict:
        """
        Scrapear perfil de Instagram.
        
        Args:
            username: Usuario de Instagram (con o sin @)
            
        Returns:
            Dict con datos del perfil
        """
        user = username.lstrip('@')
        
        async with async_playwright() as p:
            browser, context = await self._create_browser_context(p)
            page = await context.new_page()
            
            try:
                # Asegurar login
                await self._ensure_logged_in(page, context)
                
                url = f"{self.BASE_URL}/{user}/"
                logger.info(f"[IG] Scrapeando perfil: @{user}")
                await page.goto(url, wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(2, 4))
                
                # Verificar si existe
                page_text = await page.text_content("body")
                if "lo sentimos" in (page_text or "").lower() or "sorry" in (page_text or "").lower():
                    return {"error": "Perfil no encontrado", "username": user}
                
                # Extraer datos
                bio = await self._get_bio(page)
                posts = await self._get_recent_posts(page, limit=6)
                follower_count = await self._get_follower_count(page)
                
                # Extraer contactos de la bio
                phone = self._extract_phone_from_text(bio)
                email = self._extract_email_from_text(bio)
                
                return {
                    "username": user,
                    "full_name": None,
                    "biography": bio,
                    "follower_count": follower_count,
                    "contact_phone_number": phone,
                    "public_email": email,
                    "external_url": None,
                    "posts": posts,
                    "source": "instagram"
                }
                
            except Exception as e:
                logger.error(f"[IG] Error scrapeando perfil @{user}: {e}")
                return {"error": str(e), "username": user}
            finally:
                try:
                    await context.storage_state(path=self.session_file)
                except Exception:
                    pass
                await browser.close()
    
    async def _get_bio(self, page) -> str:
        """Extraer bio del perfil."""
        try:
            # Múltiples selectores para máxima compatibilidad
            selectors = [
                'div[class*="_aa_c"]',
                'section main div.-vDIg span',
                'h1[class*="_aacl"]',
                'span[class*="_ap3a"]',
            ]
            for sel in selectors:
                el = await page.query_selector(sel)
                if el:
                    text = await el.text_content()
                    if text and len(text.strip()) > 0:
                        return text.strip()
            return ""
        except Exception:
            return ""
    
    async def _get_recent_posts(self, page, limit: int = 6) -> List[Dict]:
        """Extraer posts recientes."""
        posts = []
        try:
            post_links = await page.query_selector_all('article a[href*="/p/"]')
            for link in post_links[:limit]:
                try:
                    await link.click()
                    await asyncio.sleep(2)
                    
                    post_data = await self._extract_post_data(page)
                    if post_data:
                        posts.append(post_data)
                    
                    # Cerrar
                    try:
                        close = await page.query_selector('[aria-label="Cerrar"], [aria-label="Close"]')
                        if close:
                            await close.click()
                        else:
                            await page.keyboard.press("Escape")
                        await asyncio.sleep(1)
                    except Exception:
                        await page.keyboard.press("Escape")
                        await asyncio.sleep(1)
                except Exception:
                    try:
                        await page.keyboard.press("Escape")
                        await asyncio.sleep(1)
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"[IG] Error posts: {e}")
        
        return posts
    
    async def _get_follower_count(self, page) -> Optional[int]:
        """Extraer número de seguidores."""
        try:
            # Buscar elemento con seguidores
            selectors = [
                'a[href$="/followers/"] span',
                'li:nth-child(2) span[class*="_ac2a"]',
                'ul li:nth-child(2) span',
            ]
            for sel in selectors:
                el = await page.query_selector(sel)
                if el:
                    text = await el.text_content()
                    if text:
                        return self._parse_count(text)
            return None
        except Exception:
            return None
    
    def _parse_count(self, text: str) -> Optional[int]:
        """Parsear contador tipo '1.5k', '2m'."""
        if not text:
            return None
        
        text = text.lower().strip().replace(',', '').replace(' ', '')
        
        if 'k' in text:
            return int(float(text.replace('k', '')) * 1000)
        elif 'm' in text:
            return int(float(text.replace('m', '')) * 1000000)
        else:
            # Remove dots used as thousands separator
            text = text.replace('.', '')
            try:
                return int(text)
            except ValueError:
                return None
    
    def _extract_phone_from_text(self, text: str) -> Optional[str]:
        """Extraer teléfono de texto."""
        import re
        patterns = [
            r'\+?58[-\s]?\d{3}[-\s]?\d{7}',
            r'0\d{3}[-\s]?\d{7}'
        ]
        for p in patterns:
            match = re.search(p, text or "")
            if match:
                return match.group(0)
        return None
    
    def _extract_email_from_text(self, text: str) -> Optional[str]:
        """Extraer email de texto."""
        import re
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(pattern, text or "")
        return match.group(0) if match else None
