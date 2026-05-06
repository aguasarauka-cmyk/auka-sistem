"""
AUKA - Smoke Test
Verifica que todos los componentes están correctamente instalados y configurados.
"""

import asyncio
import sys
import os

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)


def test_imports():
    """Verificar que todos los módulos se importan correctamente."""
    print("=" * 60)
    print("🔍 TEST 1: Imports de módulos")
    print("=" * 60)
    
    modules = [
        ("config.settings", "Settings"),
        ("scripts.utils.llm_client", "LLMClient"),
        ("scripts.utils.validators", "validate_json_output"),
        ("scripts.utils.cleaners", "TextCleaner"),
        ("scripts.scrapers.google_maps", "GoogleMapsScraper"),
        ("scripts.scrapers.instagram", "InstagramScraper"),
        ("scripts.scrapers.web_playwright", "WebScraper"),
        ("scripts.agents.director", "DirectorAgent"),
        ("scripts.agents.explorer", "ExplorerAgent"),
        ("scripts.agents.scraper", "ScraperAgent"),
        ("scripts.agents.structurer", "StructurerAgent"),
        ("scripts.agents.analyst", "AnalystAgent"),
        ("scripts.agents.memory", "MemoryAgent"),
        ("scripts.agents.conversational", "ConversationalAgent"),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, class_name in modules:
        try:
            mod = __import__(module_name, fromlist=[class_name])
            getattr(mod, class_name)
            print(f"  ✅ {module_name}.{class_name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {module_name}.{class_name}: {e}")
            failed += 1
    
    print(f"\n  Resultado: {passed}/{passed+failed} módulos OK")
    return failed == 0


def test_config():
    """Verificar configuración."""
    print("\n" + "=" * 60)
    print("🔧 TEST 2: Configuración (.env)")
    print("=" * 60)
    
    from config.settings import settings
    
    checks = [
        ("NVIDIA_API_KEY", bool(settings.NVIDIA_API_KEY), "Kimi K2.6"),
        ("SUPABASE_URL", bool(settings.SUPABASE_URL), "Supabase URL"),
        ("SUPABASE_KEY", bool(settings.SUPABASE_KEY), "Supabase Key"),
        ("INSTAGRAM_USERNAME", bool(settings.INSTAGRAM_USERNAME), "Instagram User"),
        ("INSTAGRAM_PASSWORD", bool(settings.INSTAGRAM_PASSWORD), "Instagram Pass"),
        ("DEEPSEEK_API_KEY", bool(settings.DEEPSEEK_API_KEY), "DeepSeek"),
        ("GOOGLE_MAPS_API_KEY", bool(settings.GOOGLE_MAPS_API_KEY), "Google Maps"),
    ]
    
    all_ok = True
    for name, ok, desc in checks:
        status = "✅" if ok else "⚠️"
        if not ok:
            all_ok = False
        value_hint = "configurado" if ok else "FALTA"
        print(f"  {status} {desc}: {value_hint}")
    
    errors = settings.validate()
    if errors:
        print(f"\n  ⚠️ Errores de validación: {errors}")
    else:
        print(f"\n  ✅ Configuración válida")
    
    return all_ok


def test_playwright():
    """Verificar que Playwright funciona."""
    print("\n" + "=" * 60)
    print("🌐 TEST 3: Playwright + Chromium")
    print("=" * 60)
    
    async def _test():
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://www.google.com", wait_until="domcontentloaded")
            title = await page.title()
            await browser.close()
            return title
    
    try:
        title = asyncio.run(_test())
        print(f"  ✅ Playwright OK - Navegó a Google: '{title}'")
        return True
    except Exception as e:
        print(f"  ❌ Playwright FALLÓ: {e}")
        return False


def test_llm():
    """Verificar conexión al LLM (NVIDIA Kimi K2.6)."""
    print("\n" + "=" * 60)
    print("🧠 TEST 4: LLM (NVIDIA Kimi K2.6)")
    print("=" * 60)
    
    try:
        from scripts.utils.llm_client import LLMClient
        
        client = LLMClient(primary_model="nvidia-kimi-k26", backup_model="ollama")
        response = client.generate(
            prompt="Responde SOLO con: OK",
            temperature=0.1,
            max_tokens=10
        )
        print(f"  ✅ LLM OK - Respuesta: '{response.strip()[:50]}'")
        return True
    except Exception as e:
        print(f"  ❌ LLM FALLÓ: {e}")
        return False


def test_ollama():
    """Verificar conexión a Ollama (modelo local)."""
    print("\n" + "=" * 60)
    print("🏠 TEST 5: Ollama (modelo local)")
    print("=" * 60)
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            print(f"  ✅ Ollama OK - Modelos: {', '.join(model_names)}")
            return True
        else:
            print(f"  ⚠️ Ollama respondió con status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ⚠️ Ollama no disponible: {e}")
        return False


def test_supabase():
    """Verificar conexión a Supabase."""
    print("\n" + "=" * 60)
    print("💾 TEST 6: Supabase")
    print("=" * 60)
    
    try:
        from scripts.database.supabase_client import db
        
        if db.client:
            # Intentar consultar si las tablas existen
            try:
                result = db.table("prospectos").select("count", count="exact").limit(1).execute()
                count = getattr(result, 'count', 0)
                print(f"  ✅ Supabase OK - Tabla prospectos existe ({count} registros)")
                return True
            except Exception as e:
                error_str = str(e)
                if "does not exist" in error_str or "relation" in error_str:
                    print(f"  ⚠️ Supabase conectado pero las tablas no existen aún")
                    print(f"     → Ejecuta el SQL de schemas.py en Supabase SQL Editor")
                    return True  # Connection works
                else:
                    print(f"  ⚠️ Supabase error: {e}")
                    return False
        else:
            print(f"  ❌ Supabase no inicializado (verificar URL y KEY)")
            return False
    except Exception as e:
        print(f"  ❌ Supabase FALLÓ: {e}")
        return False


def main():
    """Ejecutar todos los tests."""
    print("\n" + "🚀" * 30)
    print("    AUKA SYSTEM - SMOKE TEST")
    print("🚀" * 30 + "\n")
    
    results = {
        "Imports": test_imports(),
        "Config": test_config(),
        "Playwright": test_playwright(),
        "LLM": test_llm(),
        "Ollama": test_ollama(),
        "Supabase": test_supabase(),
    }
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n  Total: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n  🎉 ¡SISTEMA LISTO PARA OPERAR!")
    elif passed >= 4:
        print("\n  ⚡ Sistema funcional con algunas advertencias")
    else:
        print("\n  ⚠️ Se requieren correcciones antes de continuar")
    
    return passed >= 4


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
