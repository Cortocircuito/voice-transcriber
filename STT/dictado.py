#!/usr/bin/env python3
"""Voice to Text - Speech transcription using faster-whisper."""

import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).parent.resolve()
VENV_PYTHON = SCRIPT_DIR.parent / "whisper_venv" / "bin" / "python3"

if VENV_PYTHON.exists() and str(VENV_PYTHON) != sys.executable:
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve())] + sys.argv[1:])

from faster_whisper import WhisperModel

DURATION: int = 15
LANGUAGE: str = "en"
SAMPLE_RATE = 16000
CHANNELS = 1
RECORDING_DEVICE = "default"

LANG_MAP = {
    "1": ("en", "Inglés"),
    "2": ("es", "Español"),
    "3": ("fr", "Francés"),
    "4": ("de", "Alemán"),
}

model: Optional[WhisperModel] = None
interrupted = False


def signal_handler(signum, frame):
    global interrupted
    interrupted = True
    print("\nInterrumpido.")


def validate_duration(value: str) -> int:
    try:
        dur = int(value)
        if 1 <= dur <= 300:
            return dur
    except ValueError:
        pass
    print("⚠️ Duración inválida. Usando 15s por defecto.")
    return 15


def get_lang_label(lang_code: str) -> str:
    for code, label in LANG_MAP.values():
        if code == lang_code:
            return label
    return lang_code


def check_mic() -> bool:
    print("🎤 Mic: ", end="", flush=True)
    try:
        result = subprocess.run(
            ["arecord", "-D", RECORDING_DEVICE, "-f", "S16_LE", "-r", str(SAMPLE_RATE), "-c", str(CHANNELS), "-d", "1", "/dev/null"],
            capture_output=True,
            timeout=2,
        )
        if result.returncode == 0:
            print("✅")
            return True
    except Exception:
        pass
    print("⚠️")
    return False


def record_audio(duration: int) -> Optional[str]:
    global interrupted
    
    check_mic()
    print("Iniciando... ¡HABLA AHORA!")
    
    audio_path = tempfile.mktemp(suffix=".wav")
    
    try:
        proc = subprocess.Popen(
            ["arecord", "-D", RECORDING_DEVICE, "-f", "S16_LE", "-r", str(SAMPLE_RATE), "-c", str(CHANNELS), audio_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        for i in range(duration, 0, -1):
            if interrupted:
                proc.terminate()
                proc.wait()
                return None
            print(f"\rRestante: {i} s", end="", flush=True)
            import time
            time.sleep(1)
        print()
        
        proc.terminate()
        proc.wait()
        
        return audio_path
        
    except Exception as e:
        print(f"Error grabando: {e}")
        return None


def transcribe(audio_path: str, model: WhisperModel) -> bool:
    try:
        segments, _ = model.transcribe(audio_path, language=LANGUAGE)
        
        text = "\n".join(segment.text.strip() for segment in segments)
        
        if not text:
            print("-" * 35)
            print("⚠️ No se detectó ningún audio. ¿Hablaste durante la grabación?")
            print("-" * 35)
            return False
        
        print("-" * 35)
        print(f"✅ Transcripción ({get_lang_label(LANGUAGE)}):")
        print(text)
        print("-" * 35)
        return True
        
    except Exception as e:
        print(f"Error transcribiendo: {e}")
        return False


def configure_settings():
    global DURATION, LANGUAGE
    
    print()
    print(f"--- CONFIGURACIÓN (D:{DURATION}s | L:{get_lang_label(LANGUAGE)}) ---")
    print("1) Duración (segundos)")
    print("2) Idioma (1:en 2:es 3:fr 4:de)")
    
    choice = input("Opción: ").strip()
    
    if choice == "1":
        new_dur = input(f"Segundos [{DURATION}]: ").strip()
        if new_dur:
            DURATION = validate_duration(new_dur)
    elif choice == "2":
        lang_opt = input("1)Inglés 2)Español 3)Francés 4)Alemán: ").strip()
        if lang_opt in LANG_MAP:
            LANGUAGE = LANG_MAP[lang_opt][0]


def run_dictation(model: WhisperModel):
    global interrupted, DURATION, LANGUAGE
    
    while True:
        print()
        print(f"--- GRABANDO ({DURATION}s, {get_lang_label(LANGUAGE)}) ---")
        
        interrupted = False
        audio_path = record_audio(DURATION)
        
        if audio_path is None:
            continue
            
        transcribe(audio_path, model)
        
        try:
            os.unlink(audio_path)
        except:
            pass
        
        print("D)uración | I)dioma | S)alir")
        try:
            action = input("Continuar: ").strip().lower()
        except EOFError:
            break
        
        if action == "d":
            new_dur = input(f"Segundos [{DURATION}]: ").strip()
            if new_dur:
                DURATION = validate_duration(new_dur)
        elif action == "i":
            lang_opt = input("1)en 2)es 3:fr 4:de: ").strip()
            if lang_opt in LANG_MAP:
                LANGUAGE = LANG_MAP[lang_opt][0]
        elif action == "s":
            break


def show_menu(model: WhisperModel):
    while True:
        print()
        print("=== MENÚ ===")
        print("1) Grabar")
        print(f"2) Configurar (D:{DURATION}s L:{get_lang_label(LANGUAGE)})")
        print("3) Salir")
        
        try:
            opt = input("Opción: ").strip()
        except EOFError:
            break
        
        if opt == "1":
            run_dictation(model)
        elif opt == "2":
            configure_settings()
        elif opt == "3":
            print("¡Hasta luego!")
            break


def main():
    global model
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Cargando modelo Whisper...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    
    print("Entorno activado. Ctrl+C para salir.")
    show_menu(model)


if __name__ == "__main__":
    main()
