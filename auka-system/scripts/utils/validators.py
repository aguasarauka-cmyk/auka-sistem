"""
AUKA - Validadores de Datos
Funciones para validar JSON, limpiar outputs y normalizar datos.
"""

import json
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger("auka.validators")


def validate_json_output(
    text: str, 
    default: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Validar y parsear JSON desde texto crudo.
    Maneja markdown, espacios extra y errores comunes.
    
    Args:
        text: Texto que debería contener JSON
        default: Valor por defecto si falla el parseo
        
    Returns:
        Dict con el JSON parseado o default
    """
    if not text or not isinstance(text, str):
        return default or {}
    
    # Limpiar markdown
    cleaned = text.replace("```json", "").replace("```", "").strip()
    
    # Intentar parsear directamente
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Intentar extraer JSON entre llaves
    try:
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # Intentar fix comunes
    try:
        # Reemplazar comillas simples por dobles
        fixed = cleaned.replace("'", '"')
        # Quitar trailing commas
        fixed = re.sub(r',(\s*[}\]])', r'\1', fixed)
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    
    logger.warning(f"[VALIDATOR] No se pudo parsear JSON: {cleaned[:100]}...")
    return default or {}


def validate_prospecto(data: Dict) -> tuple:
    """
    Validar estructura mínima de un prospecto.
    
    Returns:
        (is_valid: bool, errors: list, confidence: str)
    """
    errors = []
    
    # Campos críticos
    if not data.get("empresa"):
        errors.append("Falta nombre de empresa")
    if not data.get("ciudad"):
        errors.append("Falta ciudad")
    
    # Calcular confianza
    score = 0
    if data.get("empresa"): score += 3
    if data.get("telefono"): score += 2
    if data.get("email"): score += 2
    if data.get("evento"): score += 1
    if data.get("fecha"): score += 1
    if data.get("instagram"): score += 1
    
    if score >= 6:
        confidence = "alta"
    elif score >= 3:
        confidence = "media"
    else:
        confidence = "baja"
    
    is_valid = len(errors) == 0 or confidence != "baja"
    
    return is_valid, errors, confidence


def sanitize_string(value: Any) -> Optional[str]:
    """Limpiar y sanitizar un string."""
    if not value:
        return None
    
    text = str(value).strip()
    
    # Eliminar caracteres de control
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    
    # Normalizar espacios
    text = re.sub(r'\s+', ' ', text)
    
    return text if text else None


def extract_phone(text: str) -> Optional[str]:
    """Extraer teléfono venezolano de texto."""
    if not text:
        return None
    
    patterns = [
        r'\+?58[-\s.]?\d{3}[-\s.]?\d{7}',
        r'0\d{3}[-\s.]?\d{7}',
        r'\d{4}[-\s.]?\d{7}',
        r'\(\d{3}\)\s?\d{7}'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return None


def extract_email(text: str) -> Optional[str]:
    """Extraer email de texto."""
    if not text:
        return None
    
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def normalize_venezuela_phone(phone: str) -> Optional[str]:
    """Normalizar teléfono venezolano a formato estándar."""
    if not phone:
        return None
    
    # Eliminar todo excepto dígitos y +
    digits = re.sub(r'[^\d+]', '', phone)
    
    # Si empieza con 0, reemplazar por +58
    if digits.startswith('0'):
        digits = '+58' + digits[1:]
    
    # Si no tiene código de país, agregar +58
    if not digits.startswith('+'):
        digits = '+58' + digits
    
    return digits if len(digits) >= 12 else phone
