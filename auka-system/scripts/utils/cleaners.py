"""
AUKA - Limpiadores de Texto
Funciones para limpiar HTML, emojis y normalizar texto.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger("auka.cleaners")


class TextCleaner:
    """Limpiador de texto para preparación de datos de LLM."""
    
    # Patrones comunes
    HTML_TAGS = re.compile(r'<[^>]+>')
    EMOJI_RANGE = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", 
        flags=re.UNICODE
    )
    EXTRA_SPACES = re.compile(r'\s+')
    SPECIAL_CHARS = re.compile(r'[^\w\s@#:.,;+\-/()\'\"|]')
    
    def clean(self, text: str) -> str:
        """
        Pipeline completo de limpieza.
        
        Orden:
            1. Eliminar HTML
            2. Eliminar emojis
            3. Eliminar caracteres especiales
            4. Normalizar espacios
            5. Truncar si es muy largo
        """
        if not text:
            return ""
        
        # 1. HTML
        text = self.HTML_TAGS.sub(' ', text)
        
        # 2. Emojis
        text = self.EMOJI_RANGE.sub(' ', text)
        
        # 3. Caracteres especiales (mantener @ para menciones, # para hashtags)
        text = self.SPECIAL_CHARS.sub(' ', text)
        
        # 4. Espacios múltiples
        text = self.EXTRA_SPACES.sub(' ', text)
        
        # 5. Trim
        text = text.strip()
        
        # 6. Truncar si es muy largo (límite de 5000 chars para LLM)
        if len(text) > 5000:
            text = text[:5000] + "..."
        
        return text
    
    def clean_html_only(self, text: str) -> str:
        """Solo eliminar tags HTML."""
        if not text:
            return ""
        return self.HTML_TAGS.sub(' ', text).strip()
    
    def clean_instagram_caption(self, caption: str) -> str:
        """Limpiar caption de Instagram específicamente."""
        if not caption:
            return ""
        
        text = self.clean(caption)
        
        # Preservar hashtags pero limpiar exceso
        hashtags = re.findall(r'#\w+', text)
        if len(hashtags) > 10:
            # Mantener solo los primeros 10 hashtags
            for ht in hashtags[10:]:
                text = text.replace(ht, '')
        
        # Preservar menciones @
        text = self.EXTRA_SPACES.sub(' ', text).strip()
        
        return text
    
    def extract_hashtags(self, text: str) -> list:
        """Extraer hashtags de texto."""
        if not text:
            return []
        return re.findall(r'#\w+', text.lower())
    
    def extract_mentions(self, text: str) -> list:
        """Extraer menciones @ de texto."""
        if not text:
            return []
        return re.findall(r'@\w+', text.lower())


# Instancia global
cleaner = TextCleaner()
