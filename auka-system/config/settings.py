"""
AUKA System - Configuración centralizada
Gestiona variables de entorno y parámetros del sistema.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Settings:
    """Configuración del sistema AUKA."""
    
    # ── Supabase ────────────────────────────────────────────────────
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # ── Telegram ────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    ALLOWED_TELEGRAM_USERS: list = [int(u.strip()) for u in os.getenv("ALLOWED_TELEGRAM_USERS", "").split(",") if u.strip()]
    
    # ── NVIDIA API (Kimi K2.6) ──────────────────────────────────
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_API_URL: str = os.getenv("NVIDIA_API_URL", "https://integrate.api.nvidia.com/v1")
    KIMI_MODEL: str = os.getenv("KIMI_MODEL", "moonshotai/kimi-k2.6")
    KIMI_K25_API_KEY: str = os.getenv("KIMI_K25_API_KEY", "")
    
    # ── Ollama (modelos locales) ────────────────────────────────────
    OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3.5:9b")
    
    # ── DeepSeek ────────────────────────────────────────────────────
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    # ── Google Maps ─────────────────────────────────────────────────
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    
    # ── Instagram ───────────────────────────────────────────────────
    INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
    INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")
    
    # ── Scraping ────────────────────────────────────────────────────
    SCRAPER_DELAY_MIN: float = float(os.getenv("SCRAPER_DELAY_MIN", "1.5"))
    SCRAPER_DELAY_MAX: float = float(os.getenv("SCRAPER_DELAY_MAX", "4.0"))
    MAX_RESULTS_PER_QUERY: int = int(os.getenv("MAX_RESULTS_PER_QUERY", "20"))
    SCRAPER_TIMEOUT: int = int(os.getenv("SCRAPER_TIMEOUT", "30"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))
    
    # ── Sistema ─────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENV: str = os.getenv("ENV", "development")
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "supabase")
    
    # ── Geografía Objetivo ──────────────────────────────────────────
    CIUDADES_OBJETIVO = ["Caracas", "Valencia", "Maracay", "La Guaira"]
    CIUDADES_PRIORIDAD_ALTA = ["Caracas", "Valencia"]
    
    # ── Tipos de Evento ─────────────────────────────────────────────
    TIPOS_EVENTO = [
        "deportivo", "corporativo", "social", "cultural", 
        "gastronomico", "religioso", "otro"
    ]
    TIPOS_PRIORIDAD_ALTA = ["deportivo", "corporativo"]
    
    # ── Scoring ─────────────────────────────────────────────────────
    SCORE_ALTA_MIN: int = 80
    SCORE_MEDIA_MIN: int = 50
    SCORE_MAX: int = 100
    
    # ── Scheduling ──────────────────────────────────────────────────
    SCHEDULE_INTERVAL_HOURS: int = int(os.getenv("SCHEDULE_INTERVAL_HOURS", "6"))
    
    @classmethod
    def validate(cls) -> list:
        """Validar que las variables críticas estén configuradas."""
        errors = []
        
        if not cls.SUPABASE_URL and cls.STORAGE_BACKEND == "supabase":
            errors.append("SUPABASE_URL no configurada")
        if not cls.SUPABASE_KEY and cls.STORAGE_BACKEND == "supabase":
            errors.append("SUPABASE_KEY no configurada")
        if not cls.NVIDIA_API_KEY:
            errors.append("NVIDIA_API_KEY no configurada (Kimi K2.6)")
        if not cls.TELEGRAM_BOT_TOKEN and cls.ENV == "production":
            errors.append("TELEGRAM_BOT_TOKEN requerido en producción")
            
        return errors
    
    @classmethod
    def is_configured(cls) -> bool:
        """Verificar si la configuración mínima está completa."""
        return len(cls.validate()) == 0


# Instancia global
settings = Settings()
