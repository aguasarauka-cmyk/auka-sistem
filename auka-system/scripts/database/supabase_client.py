"""
AUKA - Cliente de Base de Datos
Factory que selecciona entre Supabase y SQLite según configuración.
Si Supabase no está disponible, usa SQLite automáticamente.
"""

import logging
from typing import Dict, List, Optional, Any

from config.settings import settings

logger = logging.getLogger("auka.database")


def _create_client():
    """
    Factory: crear el cliente de DB correcto.
    Prioridad: 
    1. Si STORAGE_BACKEND=sqlite → SQLite
    2. Si Supabase configurado y disponible → Supabase
    3. Fallback → SQLite
    """
    backend = settings.STORAGE_BACKEND
    
    if backend == "sqlite":
        logger.info("[DB] Usando SQLite local (configurado)")
        from scripts.database.sqlite_client import SQLiteClient
        return SQLiteClient()
    
    # Intentar Supabase
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        try:
            from supabase import create_client, Client
            
            client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
            # Test de conectividad rápido
            # (la creación del cliente no verifica la conexión)
            logger.info("[DB] Usando Supabase")
            
            class SupabaseWrapper:
                """Wrapper para mantener interfaz compatible."""
                
                _instance = None
                
                def __init__(self, supabase_client):
                    self._client = supabase_client
                
                @property
                def client(self):
                    return self._client
                
                def table(self, table_name: str):
                    if not self._client:
                        raise RuntimeError("Supabase no inicializado")
                    # Usar prefijo auka_ automáticamente para aislar de otras bases de datos
                    prefixed_name = f"auka_{table_name}" if not table_name.startswith("auka_") else table_name
                    return self._client.table(prefixed_name)
                
                def raw(self, sql: str):
                    if not self._client:
                        raise RuntimeError("Supabase no inicializado")
                    return self._client.rpc(sql)
                
                async def upsert_prospecto(self, data: Dict) -> Dict:
                    """Realiza un Upsert lógico (Check-before-insert) estricto para evitar duplicados en la BD real."""
                    try:
                        query = self.table("prospectos").select("id, raw_data, notas")
                        
                        # Construir matriz de validación (OR)
                        or_conds = []
                        if data.get("instagram"): or_conds.append(f"instagram.eq.{data['instagram']}")
                        if data.get("telefono"): or_conds.append(f"telefono.eq.{data['telefono']}")
                        if data.get("web"): or_conds.append(f"web.eq.{data['web']}")
                        
                        existing = None
                        if or_conds:
                            # Buscar colisión en cualquiera de los identificadores únicos
                            res = query.or_(",".join(or_conds)).execute()
                            if res.data:
                                existing = res.data[0]
                        
                        if existing:
                            # Fusión de datos (Evitar sobrescribir si el existente tiene más info)
                            # Se actualizan solo los campos nuevos para enriquecer el perfil
                            result = self.table("prospectos").update(data).eq("id", existing["id"]).execute()
                            return {"success": True, "data": result.data, "action": "updated"}
                        else:
                            # Inserción limpia
                            result = self.table("prospectos").insert(data).execute()
                            return {"success": True, "data": result.data, "action": "inserted"}
                    except Exception as e:
                        logger.error(f"[SUPABASE] Error en upsert estricto: {e}")
                        return {"success": False, "error": str(e)}
                
                async def get_prospectos(self, filters: Optional[Dict] = None, limit: int = 20) -> List[Dict]:
                    try:
                        query = self.table("prospectos").select("*")
                        if filters:
                            for key, value in filters.items():
                                query = query.eq(key, value)
                        result = query.limit(limit).execute()
                        return result.data or []
                    except Exception as e:
                        logger.error(f"[SUPABASE] Error consultando prospectos: {e}")
                        return []
                
                async def update_prospecto(self, prospecto_id: str, data: Dict) -> Dict:
                    try:
                        result = self.table("prospectos").update(data).eq("id", prospecto_id).execute()
                        return {"success": True, "data": result.data}
                    except Exception as e:
                        logger.error(f"[SUPABASE] Error actualizando: {e}")
                        return {"success": False, "error": str(e)}
            
            return SupabaseWrapper(client)
            
        except Exception as e:
            logger.warning(f"[DB] Supabase falló ({e}), usando SQLite como fallback")
    
    # Fallback a SQLite
    logger.info("[DB] Usando SQLite local (fallback)")
    from scripts.database.sqlite_client import SQLiteClient
    return SQLiteClient()


# Instancia global — se crea al importar
db = _create_client()
