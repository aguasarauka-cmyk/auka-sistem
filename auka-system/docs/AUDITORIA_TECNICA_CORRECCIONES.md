# AUKA - Auditoría Técnica y Correcciones Aplicadas
## Resumen de Cambios - Mayo 2026

---

## Problemas Identificados y Soluciones

### 1. Agentes no siguen instrucciones correctamente
**Problema:** El agente iba a Google Maps en lugar de analizar páginas web específicas.

**Solución:** Se implementó sistema de modos de prospección explícitos:
- `MODO_EMPRESAS`: Buscar datos de contacto de empresas
- `MODO_EVENTOS`: Buscar eventos específicos

El agente Conversacional ahora pregunta/confirmar el modo antes de buscar.

---

### 2. Mezcla de tareas de prospección (Tarea A vs Tarea B)
**Problema:** Sin separación clara entre buscar empresas vs buscar eventos.

**Solución:** 
- Director ahora extrae `modo_prospeccion` del mensaje del usuario
- Si no está claro, pregunta "¿buscas empresas organizadoras de eventos o eventos específicos?"
- El modo se pasa a todos los agentes del pipeline

---

### 3. Base de datos con problemas de calidad
**Problema:** Registros duplicados, entradas de otros países (Valencia España vs Venezuela).

**Solución:**
- Filtro geográfico obligatorio: "Venezuela" añadido a todas las queries
- `_extract_city` ahora rechaza direcciones de otros países
- Deduplicación mejorada con verificación por identificadores únicos + fuzzy (threshold 0.85)

---

### 4. Agente de memoria no filtration antes de guardar
**Problema:** Registros se insertaban sin validar duplicados.

**Solución:**
- `check_duplicate` ahora:
  1. Busca por teléfono, Instagram, o web (OR)
  2. Si no encuentra, usa fuzzy matching por nombre
  3. Solo registra si es nuevo

---

### 5. Conversación natural no fluye
**Problema:** Sistema no mantiene contexto entre sesiones.

**Solución:**
- Nuevas funciones `save_conversational_context` y `get_conversational_context`
- Persiste el hilo de conversación en tabla `conversaciones`
- `get_context` ahora devuelve `contexto_conversacional`

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `scripts/agents/director.py` | + modo_prospeccion en pipeline ENTENDER |
| `scripts/agents/conversacional.py` | + DETECTAR_MODO + confirmar modo |
| `scripts/agents/scraper.py` | + filtro geográfica Venezuela |
| `scripts/agents/memory.py` | + contexto conversacional |
| `scripts/scrapers/google_maps.py` | + location_hint="Venezuela" |

---

## Próximos Pasos Recomendados

1. **Probar el sistema**: Ejecutar una búsqueda de prueba
2. **Limpiar BD existente**: Eliminar registros no venezolanos
3. **Monitorear**: Verificar que el filtro geográfico funciona

---

## Estado de Correcciones

| Problema | Estado |
|---------|--------|
| Modos de prospección | ✅ Completado |
| Filtro geográfico Venezuela | ✅ Completado |
| Deduplicación | ✅ Completado |
| Contexto conversacional | ✅ Completado |