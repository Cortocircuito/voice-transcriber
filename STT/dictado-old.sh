#!/bin/bash

# --- Configuración de Ruta y Archivos ---
DIR_BASE="$HOME/Code/Python/voz_a_texto" 
VENV_NAME="whisper_venv" 
ARCHIVO_AUDIO="comando.wav"
ARCHIVO_BRUTO="transcripcion_bruta.txt"
ARCHIVO_PURO="texto_puro_final.txt"

# Variable Global para la duración (Inicialmente 0, indicando que no está configurada)
DURACION_GRABACION=0 
DISPOSITIVO_GRABACION="default" 

# --- Funciones ---

# Limpia archivos temporales
cleanup_files() {
    rm -f "$ARCHIVO_AUDIO" "$ARCHIVO_BRUTO"
}

# Muestra la duración actual en formato legible
get_current_duration_label() {
    case $DURACION_GRABACION in
        10) echo "Corto (10s)";;
        15) echo "Medio (15s)";;
        30) echo "Largo (30s)";;
        # Si tiene otro valor, asume que es personalizado
        *) echo "Personalizado ($DURACION_GRABACION s)";;
    esac
}

# Configura la duración de la grabación (Usada para la configuración inicial y el menú)
configure_duration() {
    echo ""
    echo "--- CONFIGURAR DURACIÓN DE GRABACIÓN ---"
    # Solo se muestra si ya está configurado
    if [ "$DURACION_GRABACION" -ne 0 ]; then
        echo "Duración actual: $(get_current_duration_label)"
    fi
    echo "1) Corto (10 segundos)"
    echo "2) Medio (15 segundos)"
    echo "3) Largo (30 segundos)"
    echo "----------------------------------------"
    read -p "Elige una opción: " DURATION_OPTION

    case $DURATION_OPTION in
        1) DURACION_GRABACION=10; echo "Duración establecida a 10s (Corto).";;
        2) DURACION_GRABACION=15; echo "Duración establecida a 15s (Medio).";;
        3) DURACION_GRABACION=30; echo "Duración establecida a 30s (Largo).";;
        *) echo "Opción no válida. Duración sin cambios.";;
    esac
}


# Realiza la grabación y transcripción
run_dictation() {
    # 1. Configuración Inicial (SOLO se ejecuta si DURACION_GRABACION es 0)
    if [ "$DURACION_GRABACION" -eq 0 ]; then
        echo "--- PRIMERA CONFIGURACIÓN ---"
        echo "Por favor, establece la duración por defecto para la grabación."
        configure_duration
        read -n 1 -s -r -p "Pulsa cualquier tecla para comenzar a grabar..."
    fi

    # 2. Bucle interno: se repite hasta que el usuario pulse 'S' para volver al menú
    while true; do
        echo ""
        echo "--- INICIANDO GRABACIÓN ---"
        echo "Duración actual: $(get_current_duration_label)"
        echo "Tienes $DURACION_GRABACION segundos. ¡HABLA AHORA!"
        
        # Grabar audio 
        arecord -D "$DISPOSITIVO_GRABACION" -d "$DURACION_GRABACION" -f S16_LE -r 16000 -c 1 "$ARCHIVO_AUDIO" 2>/dev/null
        
        echo "Grabación finalizada. Transcribiendo..."

        # Transcribir con faster-whisper
        faster-whisper "$ARCHIVO_AUDIO" --language en -o "$ARCHIVO_BRUTO" 2>/dev/null
        
        # Limpiar y filtrar el texto puro 
        grep -v '^[[:digit:]]\+$' "$ARCHIVO_BRUTO" | grep -v -- '-->' | grep -v '^$' > "$ARCHIVO_PURO"
        
        echo "-----------------------------------"
        echo "✅ Transcripción:"
        cat "$ARCHIVO_PURO"
        echo "-----------------------------------"
        
        # 3. Preguntar al usuario: 'S' para salir del bucle, 1/2/3 para cambiar duración, otra tecla para repetir

        echo "OPCIONES:"
        echo " (1) Corto (10s) | (2) Medio (15s) | (3) Largo (30s)"
        read -n 1 -s -r -p "Pulsa 'S' para volver al MENÚ, o CUALQUIER OTRA TECLA para grabar de nuevo: " NEXT_ACTION
        echo ""
        
        case "$NEXT_ACTION" in
            # Opciones de configuración rápida de duración
            1) DURACION_GRABACION=10; echo "Duración establecida a 10s (Corto).";;
            2) DURACION_GRABACION=15; echo "Duración establecida a 15s (Medio).";;
            3) DURACION_GRABACION=30; echo "Duración establecida a 30s (Largo).";;
            
            # Opción para volver al menú
            [Ss]) 
                break # Sale del bucle de dictado y vuelve al menú principal
                ;;
            
            # Cualquier otra tecla continúa la grabación
            *) 
                echo "Continuando con la grabación. Duración: $(get_current_duration_label)";
                ;;
        esac
        
    done
}

# Muestra el menú principal
show_menu() {
    echo ""
    echo "==================================="
    echo "     MENÚ DE DICTADO POR VOZ       "
    echo "==================================="
    echo "1) Iniciar Speech to Text (Grabar)"
    echo "2) Salir del programa"
    echo "-----------------------------------"
    read -p "Elige una opción: " OPTION
    
    case $OPTION in
        1)
            run_dictation
            ;;
        2)
            echo "Saliendo del programa. ¡Hasta pronto!"
            exit 0
            ;;
        *)
            echo "Opción no válida. Inténtalo de nuevo."
            ;;
    esac
}

# --- Flujo Principal de Inicialización ---

# 0. Limpieza inicial 
cleanup_files

# 1. Cambiar al directorio y activar entorno
cd "$DIR_BASE" || { echo "Error: No se pudo cambiar al directorio $DIR_BASE. Verifica la ruta: $DIR_BASE"; exit 1; }

source "$VENV_NAME/bin/activate" || { echo "Error: No se pudo activar el entorno virtual $VENV_NAME. Asegúrate de que existe en $DIR_BASE"; exit 1; }

echo "Entorno virtual $VENV_NAME activado. Pulsa Ctrl + C para salir en cualquier momento."

# Bucle infinito: Muestra el menú y ejecuta la acción seleccionada
while true; do
    show_menu
done
