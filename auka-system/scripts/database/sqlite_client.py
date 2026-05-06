"""
AUKA - Cliente de Base de Datos (SQLite local)
Implementa la misma interfaz que supabase_client.py para uso offline/local.
Las tablas se crean automáticamente basándose en el esquema de schemas.py.
"""

import sqlite3
import json
import uuid
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger("auka.sqlite")


class SQLiteQueryBuilder:
    """Builder que imita la API de Supabase para compatibilidad."""
    
    def __init__(self, db_path: str, table_name: str):
        self._db_path = db_path
        self._table = table_name
        self._select_cols = "*"
        self._filters = []
        self._filter_values = []
        self._order_col = None
        self._order_desc = False
        self._limit_val = None
        self._count_mode = None
        self._insert_data = None
        self._update_data = None
        self._gte_filters = []
    
    def select(self, columns: str = "*", count: str = None):
        self._select_cols = columns
        self._count_mode = count
        return self
    
    def eq(self, column: str, value: Any):
        self._filters.append((column, "=", value))
        return self
    
    def gte(self, column: str, value: Any):
        self._filters.append((column, ">=", value))
        return self
    
    def order(self, column: str, desc: bool = False):
        self._order_col = column
        self._order_desc = desc
        return self
    
    def limit(self, n: int):
        self._limit_val = n
        return self
    
    def insert(self, data: Dict):
        self._insert_data = data
        return self
    
    def update(self, data: Dict):
        self._update_data = data
        return self
    
    def execute(self):
        """Execute the built query."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if self._insert_data:
                return self._exec_insert(cursor, conn)
            elif self._update_data:
                return self._exec_update(cursor, conn)
            else:
                return self._exec_select(cursor, conn)
        finally:
            conn.close()
    
    def _exec_select(self, cursor, conn):
        if self._count_mode == "exact":
            query = f"SELECT COUNT(*) as count FROM {self._table}"
        else:
            query = f"SELECT {self._select_cols} FROM {self._table}"
        
        where_parts = []
        values = []
        for col, op, val in self._filters:
            where_parts.append(f"{col} {op} ?")
            values.append(val)
        
        if where_parts:
            query += " WHERE " + " AND ".join(where_parts)
        
        if self._order_col:
            direction = "DESC" if self._order_desc else "ASC"
            query += f" ORDER BY {self._order_col} {direction}"
        
        if self._limit_val:
            query += f" LIMIT {self._limit_val}"
        
        cursor.execute(query, values)
        
        if self._count_mode == "exact":
            row = cursor.fetchone()
            result = _SQLiteResult()
            result.data = []
            result.count = row["count"] if row else 0
            return result
        
        rows = cursor.fetchall()
        result = _SQLiteResult()
        result.data = [dict(r) for r in rows]
        result.count = len(result.data)
        return result
    
    def _exec_insert(self, cursor, conn):
        data = self._insert_data
        # Add ID if not present
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        
        # Serialize any dict/list values to JSON
        for i, v in enumerate(values):
            if isinstance(v, (dict, list)):
                values[i] = json.dumps(v, ensure_ascii=False)
        
        query = f"INSERT OR IGNORE INTO {self._table} ({columns}) VALUES ({placeholders})"
        
        try:
            cursor.execute(query, values)
            conn.commit()
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                logger.warning(f"[SQLITE] Tabla {self._table} no existe, creándola...")
                _create_table_if_needed(conn, self._table)
                cursor.execute(query, values)
                conn.commit()
            else:
                raise
        
        result = _SQLiteResult()
        result.data = [data]
        return result
    
    def _exec_update(self, cursor, conn):
        data = self._update_data
        
        # Handle special values
        processed_data = {}
        for k, v in data.items():
            if v == "NOW()":
                processed_data[k] = datetime.utcnow().isoformat()
            elif isinstance(v, (dict, list)):
                processed_data[k] = json.dumps(v, ensure_ascii=False)
            else:
                processed_data[k] = v
        
        set_parts = [f"{k} = ?" for k in processed_data.keys()]
        values = list(processed_data.values())
        
        where_parts = []
        for col, op, val in self._filters:
            where_parts.append(f"{col} {op} ?")
            values.append(val)
        
        query = f"UPDATE {self._table} SET {', '.join(set_parts)}"
        if where_parts:
            query += " WHERE " + " AND ".join(where_parts)
        
        cursor.execute(query, values)
        conn.commit()
        
        result = _SQLiteResult()
        result.data = [processed_data]
        return result


class _SQLiteResult:
    """Imita el resultado de Supabase."""
    def __init__(self):
        self.data = []
        self.count = 0


def _create_table_if_needed(conn, table_name):
    """Crear tabla si no existe con esquema básico."""
    schemas = {
        "auka_prospectos": """
            CREATE TABLE IF NOT EXISTS auka_prospectos (
                id TEXT PRIMARY KEY,
                empresa TEXT,
                evento TEXT,
                tipo_evento TEXT,
                fecha TEXT,
                ubicacion TEXT,
                ciudad TEXT,
                lat REAL,
                lng REAL,
                telefono TEXT,
                email TEXT,
                web TEXT,
                instagram TEXT,
                estado TEXT DEFAULT 'nuevo',
                prioridad TEXT DEFAULT 'BAJA',
                score INTEGER DEFAULT 0,
                notas TEXT,
                fuente TEXT,
                raw_data TEXT,
                creado_en TEXT DEFAULT (datetime('now')),
                actualizado_en TEXT DEFAULT (datetime('now'))
            )
        """,
        "auka_memoria_busquedas": """
            CREATE TABLE IF NOT EXISTS auka_memoria_busquedas (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                fuente TEXT NOT NULL,
                fecha TEXT DEFAULT (datetime('now')),
                resultados_totales INTEGER DEFAULT 0,
                prospectos_nuevos INTEGER DEFAULT 0,
                duracion_segundos INTEGER DEFAULT 0,
                eficiencia REAL DEFAULT 0,
                ciudad TEXT
            )
        """,
        "auka_memoria_empresas": """
            CREATE TABLE IF NOT EXISTS auka_memoria_empresas (
                id TEXT PRIMARY KEY,
                empresa TEXT,
                telefono TEXT,
                instagram TEXT,
                web TEXT,
                hash_identificador TEXT UNIQUE,
                primera_vez_visto TEXT DEFAULT (datetime('now')),
                ultima_vez_visto TEXT DEFAULT (datetime('now')),
                veces_encontrado INTEGER DEFAULT 1,
                procesado INTEGER DEFAULT 0
            )
        """,
        "auka_memoria_fuentes": """
            CREATE TABLE IF NOT EXISTS auka_memoria_fuentes (
                id TEXT PRIMARY KEY,
                fuente TEXT UNIQUE NOT NULL,
                total_busquedas INTEGER DEFAULT 0,
                total_prospectos INTEGER DEFAULT 0,
                eficiencia_promedio REAL DEFAULT 0,
                ultima_busqueda TEXT,
                activa INTEGER DEFAULT 1
            )
        """,
        "auka_conversaciones": """
            CREATE TABLE IF NOT EXISTS auka_conversaciones (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                canal TEXT DEFAULT 'telegram',
                mensaje_usuario TEXT,
                respuesta_agente TEXT,
                accion_ejecutada TEXT,
                datos TEXT,
                creado_en TEXT DEFAULT (datetime('now'))
            )
        """
    }
    
    if table_name in schemas:
        conn.execute(schemas[table_name])
        conn.commit()
        logger.info(f"[SQLITE] Tabla '{table_name}' creada")


class SQLiteClient:
    """
    Cliente SQLite que implementa la misma interfaz que SupabaseClient.
    Drop-in replacement para desarrollo local.
    """
    
    _instance = None
    _db_path = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            self.__class__._db_path = os.path.join(data_dir, "auka.db")
            self._initialize_db()
            logger.info(f"[SQLITE] Base de datos: {self._db_path}")
    
    def _initialize_db(self):
        """Crear todas las tablas al iniciar."""
        conn = sqlite3.connect(self._db_path)
        try:
            for table in ["auka_prospectos", "auka_memoria_busquedas", "auka_memoria_empresas", 
                          "auka_memoria_fuentes", "auka_conversaciones"]:
                _create_table_if_needed(conn, table)
            
            # Insertar fuentes iniciales
            for fuente in ["google_maps", "instagram", "web"]:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO auka_memoria_fuentes (id, fuente) VALUES (?, ?)",
                        (str(uuid.uuid4()), fuente)
                    )
                except Exception:
                    pass
            conn.commit()
        finally:
            conn.close()
    
    @property
    def client(self):
        """Compatibilidad con SupabaseClient."""
        return self  # Self-reference since we are the client
    
    def table(self, table_name: str) -> SQLiteQueryBuilder:
        """Obtener referencia a tabla."""
        prefixed_name = f"auka_{table_name}" if not table_name.startswith("auka_") else table_name
        return SQLiteQueryBuilder(self._db_path, prefixed_name)
    
    def raw(self, sql: str):
        """Ejecutar SQL raw."""
        # Not directly equivalent, but provides basic functionality
        return sql
    
    async def insert_prospecto(self, data: Dict) -> Dict:
        """Insertar prospecto en tabla prospectos."""
        try:
            result = self.table("prospectos").insert(data).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            logger.error(f"[SQLITE] Error insertando prospecto: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_prospectos(self, filters: Optional[Dict] = None, limit: int = 20) -> List[Dict]:
        """Obtener prospectos con filtros opcionales."""
        try:
            query = self.table("prospectos").select("*")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            result = query.limit(limit).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"[SQLITE] Error consultando prospectos: {e}")
            return []
    
    async def update_prospecto(self, prospecto_id: str, data: Dict) -> Dict:
        """Actualizar prospecto existente."""
        try:
            result = self.table("prospectos").update(data).eq("id", prospecto_id).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            logger.error(f"[SQLITE] Error actualizando prospecto: {e}")
            return {"success": False, "error": str(e)}
