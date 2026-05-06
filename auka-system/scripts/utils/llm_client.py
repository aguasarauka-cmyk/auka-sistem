"""
AUKA - Cliente Unificado de LLMs
Gestiona conexiones a múltiples proveedores con fallback automático.
Soporta: NVIDIA (Kimi K2.6/K2.5), Ollama (Qwen/Gemma local), DeepSeek
"""

import json
import logging
import time
import requests
from typing import Optional, Dict, Any

from config.settings import settings

logger = logging.getLogger("auka.llm_client")


class LLMClient:
    """
    Cliente unificado para modelos de lenguaje.
    Proporciona fallback automático entre proveedores.
    
    Proveedores soportados:
    - nvidia-kimi-k26: Kimi K2.6 via NVIDIA API (principal)
    - nvidia-kimi-k25: Kimi K2.5 via NVIDIA API
    - ollama: Modelos locales via Ollama (qwen3.5, gemma, llama)
    - deepseek: DeepSeek API
    """
    
    PROVIDERS = {
        "nvidia-kimi-k26": {
            "api_url": settings.NVIDIA_API_URL,
            "api_key": settings.NVIDIA_API_KEY,
            "model": "moonshotai/kimi-k2.6",
        },
        "llama-3.1-70b": {
            "api_url": settings.NVIDIA_API_URL,
            "api_key": settings.NVIDIA_API_KEY,
            "model": "meta/llama-3.1-70b-instruct",
        },
        "ollama": {
            "api_url": settings.OLLAMA_API_URL,
            "api_key": "ollama",  # Ollama doesn't need a real key
            "model": settings.OLLAMA_MODEL,  # qwen3.5:9b
        },
        "deepseek": {
            "api_url": "https://api.deepseek.com/v1",
            "api_key": settings.DEEPSEEK_API_KEY,
            "model": settings.DEEPSEEK_MODEL,
        }
    }
    
    # Map old model names to new provider names
    MODEL_ALIASES = {
        "kimi-k2.5": "nvidia-kimi-k26",  # K2.5 muerto, redirigir a K2.6
        "kimi-k2.6": "nvidia-kimi-k26",
        "gemma-4b": "ollama",
        "qwen3.5": "ollama",
        "deepseek-chat": "deepseek",
    }
    
    def __init__(self, primary_model: str = "nvidia-kimi-k26", backup_model: str = "llama-3.1-70b"):
        # Resolve aliases
        self.primary = self.MODEL_ALIASES.get(primary_model, primary_model)
        self.backup = self.MODEL_ALIASES.get(backup_model, backup_model)
        self.timeout = settings.LLM_TIMEOUT
        self.max_retries = 2
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        Generar texto usando LLM con fallback automático.
        
        Args:
            prompt: Prompt del usuario
            system_prompt: Instrucciones de sistema
            model: Modelo específico (usa primary si no se especifica)
            temperature: Creatividad (0-1)
            max_tokens: Límite de tokens
            
        Returns:
            Texto generado
        """
        # Resolve model alias
        model_to_use = self.MODEL_ALIASES.get(model, model) if model else self.primary
        
        # Try primary with retries
        for attempt in range(self.max_retries):
            try:
                return self._call_provider(model_to_use, prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"[LLM] Intento {attempt+1} falló {model_to_use}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # Backoff
        
        # Try backup
        if model_to_use != self.backup:
            logger.info(f"[LLM] Intentando backup: {self.backup}")
            try:
                return self._call_provider(self.backup, prompt, system_prompt, temperature, max_tokens)
            except Exception as e2:
                logger.error(f"[LLM] Falló backup {self.backup}: {e2}")
        
        raise RuntimeError(f"Todos los modelos fallaron para: {prompt[:50]}...")
    
    def _call_provider(
        self, 
        provider_name: str, 
        prompt: str, 
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Llamar a proveedor específico."""
        
        if provider_name not in self.PROVIDERS:
            raise ValueError(f"Proveedor no soportado: {provider_name}")
        
        provider = self.PROVIDERS[provider_name]
        
        if not provider["api_key"]:
            raise ValueError(f"API key no configurada para {provider_name}")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Ollama doesn't need Bearer auth
        if provider_name == "ollama":
            headers["Authorization"] = f"Bearer {provider['api_key']}"
        else:
            headers["Authorization"] = f"Bearer {provider['api_key']}"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": provider["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        
        # NVIDIA specific: add thinking for Kimi K2.6
        if provider_name == "nvidia-kimi-k26":
            payload["chat_template_kwargs"] = {"thinking": False}  # Disable for speed
        
        api_endpoint = f"{provider['api_url']}/chat/completions"
        
        logger.debug(f"[LLM] Calling {provider_name} at {api_endpoint}")
        
        response = requests.post(
            api_endpoint,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            error_detail = response.text[:500]
            raise RuntimeError(f"HTTP {response.status_code} from {provider_name}: {error_detail}")
        
        data = response.json()
        
        # Extract text from response
        try:
            content = data["choices"][0]["message"]["content"]
            # For thinking models, content might have <think> tags
            if "<think>" in content and "</think>" in content:
                # Extract only the answer part after </think>
                parts = content.split("</think>")
                if len(parts) > 1:
                    content = parts[-1].strip()
            return content
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Respuesta inesperada de {provider_name}: {data}")
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generar y parsear JSON directamente.
        
        Args:
            prompt: Prompt que solicita JSON
            system_prompt: Instrucciones de sistema
            model: Modelo a usar
            
        Returns:
            Dict con el JSON parseado
        """
        # Añadir instrucción de JSON si no está
        if "JSON" not in prompt.upper():
            prompt += "\n\nResponde SOLO con JSON válido, sin texto adicional."
        
        response = self.generate(prompt, system_prompt, model, temperature=0.2)
        
        # Limpiar markdown si viene con ```json
        cleaned = response.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"[LLM] JSON inválido: {e}")
            logger.debug(f"[LLM] Respuesta cruda: {response[:200]}")
            # Try to extract JSON from response
            import re
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            return {"error": "json_parse_failed", "raw_response": response[:500]}


# Instancia por defecto (Kimi K2.6 principal, Ollama backup)
llm_client = LLMClient()
