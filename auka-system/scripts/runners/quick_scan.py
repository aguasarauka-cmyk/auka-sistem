"""
AUKA - Quick Scan
Ejecuta una búsqueda completa de prospectos en Google Maps.
Uso: python scripts/runners/quick_scan.py --city Caracas --query "eventos deportivos"
"""

import asyncio
import argparse
import json
import sys
import os
import logging

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("auka.quick_scan")


async def run_maps_scan(city: str, query: str, limit: int = 10):
    """Ejecutar búsqueda en Google Maps y procesar resultados."""
    from scripts.scrapers.google_maps import GoogleMapsScraper
    from scripts.utils.llm_client import LLMClient
    from scripts.database.supabase_client import db
    
    print(f"\n{'='*60}")
    print(f"🔍 AUKA Quick Scan - Google Maps")
    print(f"   Ciudad: {city}")
    print(f"   Búsqueda: {query}")
    print(f"   Límite: {limit} resultados")
    print(f"{'='*60}\n")
    
    # 1. Scrape Google Maps
    scraper = GoogleMapsScraper()
    full_query = f"{query} {city}"
    
    print(f"🌐 Buscando en Google Maps: '{full_query}'...")
    results = await scraper.search(full_query, limit=limit)
    
    if not results:
        print("❌ No se encontraron resultados")
        return
    
    print(f"✅ {len(results)} empresas encontradas\n")
    
    # 2. Mostrar resultados
    for i, r in enumerate(results, 1):
        print(f"  {i}. 🏢 {r.get('title', 'Sin nombre')}")
        if r.get("address"):
            print(f"     📍 {r['address'][:80]}")
        if r.get("phone"):
            print(f"     📞 {r['phone']}")
        if r.get("website"):
            print(f"     🌐 {r['website']}")
        if r.get("rating"):
            print(f"     ⭐ {r['rating']}")
        if r.get("category"):
            print(f"     📂 {r['category']}")
        print()
    
    # 3. Guardar en DB
    saved = 0
    for r in results:
        try:
            prospecto = {
                "empresa": r.get("title"),
                "ubicacion": r.get("address"),
                "telefono": r.get("phone"),
                "web": r.get("website"),
                "ciudad": city,
                "fuente": "google_maps",
                "estado": "nuevo",
                "prioridad": "MEDIA",
                "raw_data": json.dumps(r, ensure_ascii=False),
            }
            result = await db.insert_prospecto(prospecto)
            if result.get("success"):
                saved += 1
        except Exception as e:
            logger.debug(f"Error guardando: {e}")
    
    print(f"💾 {saved}/{len(results)} prospectos guardados en DB")
    
    # 4. Enriquecer con LLM (análisis rápido)
    try:
        llm = LLMClient()
        companies_text = "\n".join([
            f"- {r.get('title', '?')} ({r.get('category', 'N/A')}) - {r.get('address', 'N/A')}"
            for r in results[:5]
        ])
        
        prompt = f"""Analiza estas empresas encontradas en Google Maps para prospección de Aguas Arauka (agua embotellada premium para eventos).
        
Empresas encontradas buscando "{query}" en {city}:
{companies_text}

Responde en JSON con el formato:
{{
  "resumen": "resumen breve de lo encontrado",
  "mejores_prospectos": ["nombre1", "nombre2"],
  "recomendacion": "siguiente acción sugerida"
}}"""
        
        print(f"\n🧠 Analizando con Kimi K2.6...")
        analysis = llm.generate_json(prompt)
        
        if "error" not in analysis:
            print(f"\n📊 ANÁLISIS:")
            print(f"   📝 {analysis.get('resumen', 'N/A')}")
            if analysis.get("mejores_prospectos"):
                print(f"   🎯 Mejores: {', '.join(analysis['mejores_prospectos'])}")
            print(f"   💡 {analysis.get('recomendacion', 'N/A')}")
        
    except Exception as e:
        logger.warning(f"Análisis LLM falló: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ Scan completado")
    print(f"{'='*60}\n")
    
    return results


async def run_instagram_scan(hashtag: str, limit: int = 5):
    """Ejecutar búsqueda en Instagram."""
    from scripts.scrapers.instagram import InstagramScraper
    
    print(f"\n{'='*60}")
    print(f"📸 AUKA Quick Scan - Instagram")
    print(f"   Hashtag: #{hashtag}")
    print(f"   Límite: {limit} posts")
    print(f"{'='*60}\n")
    
    scraper = InstagramScraper()
    
    print(f"🔍 Buscando posts con #{hashtag}...")
    results = await scraper.search_by_hashtag(hashtag, limit=limit)
    
    if not results:
        print("❌ No se encontraron resultados (puede requerir login)")
        return
    
    print(f"✅ {len(results)} posts encontrados\n")
    
    for i, r in enumerate(results, 1):
        print(f"  {i}. @{r.get('username', '?')}")
        caption = r.get('caption', '')[:100]
        if caption:
            print(f"     💬 {caption}...")
        print()
    
    return results


def main():
    parser = argparse.ArgumentParser(description="AUKA Quick Scan")
    parser.add_argument("--source", choices=["maps", "instagram", "both"], default="maps",
                       help="Fuente de búsqueda")
    parser.add_argument("--city", default="Caracas", help="Ciudad objetivo")
    parser.add_argument("--query", default="productoras de eventos", help="Término de búsqueda")
    parser.add_argument("--hashtag", default="eventoscaracas", help="Hashtag para Instagram")
    parser.add_argument("--limit", type=int, default=10, help="Máximo de resultados")
    
    args = parser.parse_args()
    
    async def _run():
        if args.source in ("maps", "both"):
            await run_maps_scan(args.city, args.query, args.limit)
        
        if args.source in ("instagram", "both"):
            await run_instagram_scan(args.hashtag, args.limit)
    
    asyncio.run(_run())


if __name__ == "__main__":
    main()
