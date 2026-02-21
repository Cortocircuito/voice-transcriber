#!/bin/bash

# --- Configuración ---
DIR_BASE="$HOME/Code/Python/voz_a_texto"
VENV_NAME="whisper_venv"
AUDIO_FILE="comando.wav"
RAW_TRANSCRIPTION="transcripcion_bruta.txt"
CLEAN_TRANSCRIPTION="texto_puro_final.txt"
RECORDING_DEVICE="default"

DURATION=15
LANGUAGE="en"

declare -A LANG_MAP
LANG_MAP=(
    [1]="en"
    [2]="es"
    [3]="fr"
    [4]="de"
)

# --- Dependencias ---
check_dependencies() {
    if ! command -v arecord &>/dev/null; then
        echo "Error: 'arecord' no está instalado."
        exit 1
    fi
}

# --- Utilidades ---
cleanup() {
    rm -f "$AUDIO_FILE" "$RAW_TRANSCRIPTION"
}

clean_transcription() {
    grep -v '^[[:digit:]]\+$' "$RAW_TRANSCRIPTION" | grep -v -- '-->' | grep -v '^$' > "$CLEAN_TRANSCRIPTION"
}

get_lang_label() {
    case "$1" in
        en) echo "Inglés" ;;
        es) echo "Español" ;;
        fr) echo "Francés" ;;
        de) echo "Alemán" ;;
        *) echo "$1" ;;
    esac
}

validate_duration() {
    local dur="$1"
    if [[ ! "$dur" =~ ^[0-9]+$ ]] || [[ "$dur" -lt 1 ]] || [[ "$dur" -gt 300 ]]; then
        echo "⚠️ Duración inválida. Usando 15s por defecto."
        echo "15"
        return 1
    fi
    echo "$dur"
}

check_mic_level() {
    echo -n "🎤 Mic: "
    timeout 0.5 arecord -D "$RECORDING_DEVICE" -f S16_LE -r 16000 -c 1 /dev/null 2>/dev/null
    local status=$?
    # 124 = timeout (mic working), 0 = completed (unlikely for arecord)
    if [[ $status -eq 124 ]] || [[ $status -eq 0 ]]; then
        echo "✅"
        return 0
    else
        echo "⚠️"
        return 1
    fi
}

configure_settings() {
    echo ""
    echo "--- CONFIGURACIÓN (D:${DURATION}s | L:$(get_lang_label $LANGUAGE)) ---"
    echo "1) Duración (segundos)"
    echo "2) Idioma (1:en 2:es 3:fr 4:de)"
    read -p "Opción: " opt
    
    case "$opt" in
        1)
            read -p "Segundos [$DURATION]: " new_dur
            if [[ -n "$new_dur" ]]; then
                validated=$(validate_duration "$new_dur")
                DURATION=$validated
            fi
            ;;
        2)
            read -p "1)Inglés 2)Español 3)Francés 4)Alemán: " lang_opt
            [[ -n "${LANG_MAP[$lang_opt]}" ]] && LANGUAGE="${LANG_MAP[$lang_opt]}"
            ;;
    esac
}

# --- Grabación ---
record_audio() {
    local duration="$1"
    check_mic_level
    echo "Iniciando... ¡HABLA AHORA!"
    
    trap 'echo; echo "Interrumpido."; kill $PID 2>/dev/null; wait $PID 2>/dev/null; trap - INT; return 1' INT
    
    arecord -D "$RECORDING_DEVICE" -f S16_LE -r 16000 -c 1 "$AUDIO_FILE" 2>/dev/null &
    PID=$!
    
    for ((i=duration; i>0; i--)); do
        echo -ne "\rRestante: $i s"
        sleep 1
    done
    echo
    
    kill $PID 2>/dev/null
    wait $PID 2>/dev/null
    trap - INT
}

# --- Transcripción ---
transcribe() {
    faster-whisper "$AUDIO_FILE" --language "$LANGUAGE" -o "$RAW_TRANSCRIPTION" 2>/dev/null
    clean_transcription
    
    if [[ ! -s "$CLEAN_TRANSCRIPTION" ]]; then
        echo "-----------------------------------"
        echo "⚠️ No se detectó ningún audio. ¿Hablaste durante la grabación?"
        echo "-----------------------------------"
        return 1
    fi
    
    echo "-----------------------------------"
    echo "✅ Transcripción ($(get_lang_label $LANGUAGE)):"
    cat "$CLEAN_TRANSCRIPTION"
    echo "-----------------------------------"
    return 0
}

# --- Flujo Principal ---
run_dictation() {
    while true; do
        echo ""
        echo "--- GRABANDO (${DURATION}s, $(get_lang_label $LANGUAGE)) ---"
        
        record_audio "$DURATION" || continue
        transcribe
        
        echo "D)uración | I)dioma | S)alir"
        read -n 1 -s -r -p "Continuar: " action
        echo
        
        case "$action" in
            [Dd]) 
                read -p "Segundos [$DURATION]: " new_dur
                if [[ -n "$new_dur" ]]; then
                    validated=$(validate_duration "$new_dur")
                    DURATION=$validated
                fi
                ;;
            [Ii]) 
                read -p "1)en 2)es 3)fr 4)de: " lang_opt
                [[ -n "${LANG_MAP[$lang_opt]}" ]] && LANGUAGE="${LANG_MAP[$lang_opt]}"
                ;;
            [Ss]) break ;;
        esac
    done
}

show_menu() {
    echo ""
    echo "=== MENÚ ==="
    echo "1) Grabar"
    echo "2) Configurar (D:${DURATION}s L:$(get_lang_label $LANGUAGE))"
    echo "3) Salir"
    read -p "Opción: " opt
    
    case "$opt" in
        1) run_dictation ;;
        2) configure_settings ;;
        3) echo "¡Hasta luego!"; exit 0 ;;
    esac
}

# --- Inicio ---
check_dependencies
cleanup
cd "$DIR_BASE" || { echo "Error: Directorio no válido: $DIR_BASE"; exit 1; }
source "$VENV_NAME/bin/activate" || { echo "Error: No se pudo activar $VENV_NAME"; exit 1; }

if ! command -v faster-whisper &>/dev/null; then
    echo "Error: 'faster-whisper' no está instalado en el entorno virtual."
    exit 1
fi

echo "Entorno activado. Ctrl+C para salir."

while true; do
    show_menu
done
