"""
AUKA-MEMORIA: Gestiona estado, historial y aprendizaje del sistema.
NO usa LLM - lógica determinística pura para máxima velocidad.
Principio: Persistencia total en Supabase (sobrevive reinicios).
"""

import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from scripts.database.supabase_client import db

logger = logging.getLogger("auka.memoria")


class MemoryAgent:
    """
    Agente Memoria: Deduplicación, aprendizaje y contexto histórico.
    100% determinista - sin LLM.
    """
    
    def __init__(self):
        self._local_cache: Dict[str, Dict] = {}
        self._cache_max_size = 100
    
    # ═══════════════════════════════════════════════════════════════
    # CHECK_DUPLICATE
    # ═══════════════════════════════════════════════════════════════
    
    async def check_duplicate(self, empresa_data: Dict) -> Dict[str, Any]:
        """
        Verificación estricta de duplicados evaluando entidades independientes.
        """
        telefono = empresa_data.get("telefono")
        instagram = empresa_data.get("instagram")
        web = empresa_data.get("web")
        
        # 1. Verificación exacta por identificadores únicos (teléfono, instagram, web)
        try:
            query = db.table("memoria_empresas").select("*")
            or_conds = []
            if telefono: or_conds.append(f"telefono.eq.{telefono}")
            if instagram: or_conds.append(f"instagram.eq.{instagram}")
            if web: or_conds.append(f"web.eq.{web}")
            
            if or_conds:
                res = query.or_(",".join(or_conds)).execute()
                if res.data:
                    reg = res.data[0]
                    self._update_counter(reg["id"])
                    # Actualizar caché y notificar al orquestador que debe hacer Update, no Insert
                    return {
                        "es_duplicado": True,
                        "registro_id": reg["id"],
                        "match_exacto_por": "identificador_unico",
                        "veces_encontrado": reg.get("veces_encontrado", 1) + 1
                    }
        except Exception as e:
            logger.error(f"[MEMORIA] Error db lookup explí­cito: {e}")
            
        # 2. Fallback a Fuzzy por nombre comercial (umbral 0.85)
        nombre = empresa_data.get("empresa", "")
        if nombre:
            es_dup, match = await self._fuzzy_check(nombre)
            if es_dup:
                return {"es_duplicado": True, "match_por": "fuzzy", "nombre_similar": match}
        
        # 3. Registrar nueva entidad y generar hash seguro compuesto
        hash_seguro = hashlib.md5(f"{telefono}-{instagram}-{web}-{nombre}".encode()).hexdigest()
        await self._register_new(empresa_data, hash_seguro)
        return {"es_duplicado": False}
                    self._update_counter(reg["id"])
                    # Actualizar caché y notificar al orquestador que debe hacer Update, no Insert
                    return {
                        "es_duplicado": True,
                        "registro_id": reg["id"],
                        "match_exacto_por": "identificador_unico",
                        "veces_encontrado": reg.get("veces_encontrado", 1) + 1
                    }
        except Exception as e:
            logger.error(f"[MEMORIA] Error db lookup explícito: {e}")
            
        # 2. Fallback a Fuzzy por nombre comercial
        nombre = empresa_data.get("empresa", "")
        if nombre:
            es_dup, match = await self._fuzzy_check(nombre)
            if es_dup:
                return {"es_duplicado": True, "match_por": "fuzzy", "nombre_similar": match}
        
        # 3. Registrar nueva entidad y generar hash seguro compuesto
        hash_seguro = hashlib.md5(f"{telefono}-{instagram}-{web}-{nombre}".encode()).hexdigest()
        await self._register_new(empresa_data, hash_seguro)
        return {"es_duplicado": False}
    
    def _generate_hash(self, empresa: Dict) -> str:
        """Generar hash único."""
        identificador = (
            empresa.get("telefono") or 
            empresa.get("instagram") or 
            empresa.get("web") or 
            empresa.get("empresa", "").lower().strip()
        )
        return hashlib.md5(identificador.encode()).hexdigest()
    
    async def _fuzzy_check(self, nombre_nuevo: str, threshold: float = 0.85) -> tuple:
        """Verificación fuzzy por nombre."""
        try:
            result = db.table("memoria_empresas").select("empresa").execute()
            for reg in result.data or []:
                nombre = reg.get("empresa", "")
                if nombre:
                    sim = SequenceMatcher(None, nombre_nuevo.lower().strip(), nombre.lower().strip()).ratio()
                    if sim > threshold:
                        return True, nombre
        except Exception:
            pass
        return False, None
    
    async def _register_new(self, empresa: Dict, hash_id: str):
        """Registrar nueva empresa."""
        try:
            data = {
                "empresa": empresa.get("empresa"),
                "telefono": empresa.get("telefono"),
                "instagram": empresa.get("instagram"),
                "web": empresa.get("web"),
                "hash_identificador": hash_id
            }
            result = db.table("memoria_empresas").insert(data).execute()
            if result.data:
                self._add_to_cache(hash_id, result.data[0])
        except Exception as e:
            logger.error(f"[MEMORIA] Error registrando: {e}")
    
    def _update_counter(self, registro_id: str):
        """Actualizar contador."""
        try:
            db.table("memoria_empresas").update({
                "ultima_vez_visto": "NOW()",
                "veces_encontrado": db.raw("veces_encontrado + 1")
            }).eq("id", registro_id).execute()
        except Exception:
            pass
    
    # ═══════════════════════════════════════════════════════════════
    # LOG_SEARCH
    # ═══════════════════════════════════════════════════════════════
    
    async def log_search(self, query: str, fuente: str, resultados_totales: int,
                        prospectos_nuevos: int, duracion: int, ciudad: Optional[str] = None) -> Dict:
        """Registrar búsqueda y calcular eficiencia."""
        eficiencia = prospectos_nuevos / resultados_totales if resultados_totales > 0 else 0
        
        try:
            db.table("memoria_busquedas").insert({
                "query": query, "fuente": fuente, "resultados_totales": resultados_totales,
                "prospectos_nuevos": prospectos_nuevos, "duracion_segundos": duracion,
                "eficiencia": eficiencia, "ciudad": ciudad
            }).execute()
            await self._update_source_stats(fuente, eficiencia)
            return {"registrado": True, "eficiencia": eficiencia}
        except Exception as e:
            logger.error(f"[MEMORIA] Error log: {e}")
            return {"registrado": False, "eficiencia": 0}
    
    async def _update_source_stats(self, fuente: str, eficiencia_nueva: float):
        """Actualizar stats de fuente."""
        try:
            result = db.table("memoria_fuentes").select("*").eq("fuente", fuente).execute()
            if result.data:
                stats = result.data[0]
                n = stats["total_busquedas"]
                nuevo_prom = (stats["eficiencia_promedio"] * n + eficiencia_nueva) / (n + 1)
                db.table("memoria_fuentes").update({
                    "total_busquedas": n + 1,
                    "eficiencia_promedio": nuevo_prom,
                    "ultima_busqueda": "NOW()"
                }).eq("fuente", fuente).execute()
            else:
                db.table("memoria_fuentes").insert({
                    "fuente": fuente, "total_busquedas": 1,
                    "eficiencia_promedio": eficiencia_nueva, "ultima_busqueda": "NOW()"
                }).execute()
        except Exception:
            pass
    
    # ═══════════════════════════════════════════════════════════════
    # GET_CONTEXT
    # ═══════════════════════════════════════════════════════════════
    
    async def get_context(self, scope: str = "last_24h") -> Dict[str, Any]:
        """Obtener contexto histórico para el Director."""
        try:
            since = self._calculate_since(scope)
            
            queries_r = db.table("memoria_busquedas").select("query, fuente, ciudad") \
                .gte("fecha", since).execute()
            queries = list(set(q["query"] for q in (queries_r.data or []) if q.get("query")))
            ciudades = list(set(q["ciudad"] for q in (queries_r.data or []) if q.get("ciudad")))
            
            emp_r = db.table("memoria_empresas").select("empresa").eq("procesado", True).execute()
            empresas = [e["empresa"] for e in (emp_r.data or []) if e.get("empresa")]
            
            f_r = db.table("memoria_fuentes").select("fuente, eficiencia_promedio").execute()
            fuentes = {f["fuente"]: f.get("eficiencia_promedio", 0) for f in (f_r.data or [])}
            
            # Obtener contexto conversacional
            contexto_conv = await self.get_conversational_context()
            
            return {
                "queries_realizadas": queries,
                "empresas_procesadas": empresas,
                "fuentes_rendimiento": fuentes,
                "ciudades_cubiertas": ciudades,
                "recomendacion": self._generate_recommendation(ciudades, fuentes),
                "contexto_conversacional": contexto_conv,
                "scope": scope
            }
        except Exception as e:
            logger.error(f"[MEMORIA] Error contexto: {e}")
            return self._default_context()
    
    # ═══════════════════════════════════════════════════════════════════════
    # CONTEXTO CONVERSACIONAL (Persistir hilo de conversación)
    # ═══════════════════════════════════════════════════════════════
    
    async def save_conversational_context(self, user_id: str, ultimo_mensaje: str, modo_prospeccion: str = None, ciudad_foco: str = None) -> Dict:
        """Guardar contexto de la conversación actual."""
        try:
            # Buscar si ya existe contexto activo para este usuario
            existente = db.table("conversaciones").select("*") \
                .eq("user_id", user_id) \
                .order("creado_en", desc=True) \
                .limit(1).execute()
            
            if existente.data:
                # Actualizar contexto existente
                ctx = existente.data[0]
                datos = ctx.get("datos", {}) or {}
                datos["ultimo_mensaje"] = ultimo_mensaje
                if modo_prospeccion: datos["modo_prospeccion"] = modo_prospeccion
                if ciudad_foco: datos["ciudad_foco"] = ciudad_foco
                
                db.table("conversaciones").update({
                    "respuesta_agente": f"Contexto actualizado: {ultimo_mensaje}",
                    "datos": datos
                }).eq("id", ctx["id"]).execute()
                
                return {"actualizado": True, "user_id": user_id}
            else:
                # Crear nuevo contexto
                return db.table("conversaciones").insert({
                    "user_id": user_id,
                    "canal": "telegram",
                    "mensaje_usuario": ultimo_mensaje,
                    "respuesta_agente": "Iniciando contexto",
                    "accion_ejecutada": "contexto_nuevo",
                    "datos": {
                        "ultimo_mensaje": ultimo_mensaje,
                        "modo_prospeccion": modo_prospeccion,
                        "ciudad_foco": ciudad_foco
                    }
                }).execute()
        except Exception as e:
            logger.error(f"[MEMORIA] Error guardando contexto: {e}")
            return {"actualizado": False, "error": str(e)}
    
    async def get_conversational_context(self, user_id: str = None, limit: int = 5) -> List[Dict]:
        """Obtener contexto conversacional previo."""
        try:
            query = db.table("conversaciones").select("user_id, mensaje_usuario, respuesta_agente, accion_ejecutada, datos, creado_en")
            if user_id:
                query = query.eq("user_id", user_id)
            query = query.order("creado_en", desc=True).limit(limit)
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.warning(f"[MEMORIA] Error recuperando contexto: {e}")
            return []
                "scope": scope
            }
        except Exception as e:
            logger.error(f"[MEMORIA] Error contexto: {e}")
            return self._default_context()
    
    # ═══════════════════════════════════════════════════════════════
    # GET_BEST_QUERIES
    # ═══════════════════════════════════════════════════════════════
    
    async def get_best_queries(self, ciudad: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Obtener queries con mejor eficiencia."""
        try:
            q = db.table("memoria_busquedas").select("query, fuente, eficiencia") \
                .order("eficiencia", desc=True).limit(limit)
            if ciudad:
                q = q.eq("ciudad", ciudad)
            return (q.execute().data or [])
        except Exception:
            return []
    
    # ═══════════════════════════════════════════════════════════════
    # MARK_PROCESSED
    # ═══════════════════════════════════════════════════════════════
    
    async def mark_processed(self, empresa_id: str):
        """Marcar empresa como procesada."""
        try:
            db.table("memoria_empresas").update({"procesado": True}).eq("id", empresa_id).execute()
        except Exception:
            pass
    
    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def _calculate_since(self, scope: str) -> str:
        """Calcular fecha límite."""
        now = datetime.utcnow()
        deltas = {"last_24h": timedelta(hours=24), "last_week": timedelta(days=7),
                  "last_month": timedelta(days=30), "all": timedelta(days=3650)}
        return (now - deltas.get(scope, deltas["last_24h"])).isoformat()
    
    def _generate_recommendation(self, ciudades: List[str], fuentes: Dict) -> str:
        """Generar recomendación automática."""
        todas = ["Caracas", "Valencia", "Maracay", "La Guaira"]
        faltantes = [c for c in todas if c not in ciudades]
        if faltantes:
            return f"explorar {faltantes[0]}"
        if fuentes:
            return f"priorizar {max(fuentes, key=fuentes.get)}"
        return "rotar queries"
    
    def _default_context(self) -> Dict:
        return {"queries_realizadas": [], "empresas_procesadas": [],
                "fuentes_rendimiento": {}, "ciudades_cubiertas": [],
                "recomendacion": "iniciar exploración"}
    
    def _add_to_cache(self, hash_id: str, data: Dict):
        """Agregar a caché local con límite."""
        self._local_cache[hash_id] = data
        if len(self._local_cache) > self._cache_max_size:
            oldest = next(iter(self._local_cache))
            del self._local_cache[oldest]
    
    async def generar_reporte_eficiencia(self) -> Dict:
        """Reporte de eficiencia del sistema."""
        try:
            fuentes = db.table("memoria_fuentes").select("*").execute().data or []
            return {
                "fuentes": [{"nombre": f["fuente"],
                           "eficiencia": f"{f.get('eficiencia_promedio', 0)*100:.0f}%",
                           "busquedas": f.get("total_busquedas", 0)} for f in fuentes],
                "generado_en": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}


# Instancia singleton
memory_agent = MemoryAgent()
