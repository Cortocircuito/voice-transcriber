# Plan: Mejorar Algoritmo de Comparación de Texto

## Problema Actual

El algoritmo usa `difflib.SequenceMatcher` que espera correspondencia 1:1 entre palabras. Cuando hay desajustes (ej: usuario dice "the cat" en vez de "cat"), causa efecto cascada:
- Palabras posteriores quedan descalabradas
- Palabras correctas se marcan como error (falsos positivos)

## Solución: 3 Métodos Combinados

### 1. Algoritmo Fonético Básico (Soundex Simplificado)

Sin librerías externas, implementar un algoritmo fonético básico:

```python
def get_phonetic_code(word: str) -> str:
    """Convierte palabra a código fonético simplificado."""
    # Reglas básicas:
    # - Vocales = mismo grupo
    # - Consonantes similares fonéticamente = mismo código
    # -Primera letra se preserva
```

Ejemplos:
- "cat" → "K0" 
- "cut" → "K0" (suenan similar)
- "phone" → "F5" 
- "fone" → "F5" (suenan igual)

### 2. Ventana de Búsqueda Flexible

Para cada palabra del texto original:
- Buscar en un rango de posiciones en la transcripción (±ventana)
- Si se encuentra (exacto o fonético), marcar como correcto
- No afectar palabras posteriores

```python
def find_word_in_window(
    target: str,
    transcribed: list[str],
    start_pos: int,
    window_size: int = 2
) -> tuple[bool, int]:
    """Busca palabra en ventana."""
    for offset in range(-window_size, window_size + 1):
        pos = start_pos + offset
        if 0 <= pos < len(transcribed):
            if is_match(target, transcribed[pos]):
                return True, pos
    return False, -1
```

### 3. Score por Posición Individual

En lugar de alineación estricta:
- Para cada palabra original, verificar presencia en transcripción
- Calcular accuracy: palabras_encontradas / total
- Identificar: palabras_faltantes, palabras_extra

## Implementación

### Nuevos Métodos en TextComparator

```python
class TextComparator:
    # Métodos nuevos:
    def get_phonetic_code(self, word: str) -> str:
        """Algoritmo fonético simplificado."""
        
    def is_word_match(self, original: str, transcribed: str) -> bool:
        """Compara palabras (exacta o fonéticamente)."""
        
    def compare_flexible(
        self, 
        original: str, 
        transcribed: str,
        window_size: int = 2
    ) -> ComparisonResult:
        """Comparación con ventana flexible."""
        
    def compare_per_word(
        self, 
        original: str, 
        transcribed: str
    ) -> ComparisonResult:
        """Comparación palabra por palabra sin alineación."""
```

### Configuración

Agregar parámetros de configuración en `Config`:
- `comparison_window_size`: int = 2 (palabras +/- a buscar)
- `use_phonetic_matching`: bool = True (usar tolerancia fonética)
- `comparison_method`: str = "flexible" | "per_word" | "legacy"

## Tests a Crear

1. `test_compare_with_word_duplication` - Usuario dice "the the" en vez de "the"
2. `test_compare_phonetic_similarity` - "cat" vs "cut" se consideran similares
3. `test_compare_word_offset` - Palabra correcta pero deslocada
4. `test_compare_flexible_window` - Con ventana de búsqueda
5. `test_compare_per_word_accuracy` - Score sin alineación

## Métricas de Éxito

- Reducir falsos positivos (palabras correctas marcadas como error)
- Tolerancia a errores de timing del habla
- Accuracy más representativo de la pronunciación real
