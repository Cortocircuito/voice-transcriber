"""Internationalization module for voice-to-text."""

from typing import Dict

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "es": {
        "app_title": "🎤 VOZ A TEXTO",
        "menu_record": "Grabar",
        "menu_config": "Configurar",
        "menu_exit": "Salir",
        "menu_back": "Volver",
        "menu_duration": "Duración",
        "menu_language": "Idioma",
        "recording": "GRABANDO",
        "speak_now": "¡HABLA AHORA!",
        "transcribing": "Transcribiendo",
        "transcription": "TRANSCRIPCIÓN",
        "no_audio": "No se detectó audio",
        "no_audio_hint": "¿Hablaste durante la grabación?",
        "mic_check": "Mic:",
        "mic_ready": "Listo",
        "mic_not_found": "No detectado",
        "config_title": "CONFIGURACIÓN",
        "config_duration": "Duración",
        "config_language": "Idioma",
        "option": "Opción",
        "goodbye": "¡Hasta luego!",
        "ready": "Entorno activado. Ctrl+C para salir.",
        "loading_model": "Cargando modelo Whisper...",
        "action_duration": "Duración",
        "action_language": "Idioma",
        "action_exit": "Salir",
        "continue_prompt": "Continuar",
        "language_en": "Inglés",
        "language_es": "Español",
        "language_fr": "Francés",
        "language_de": "Alemán",
        "history_saved": "Historial guardado",
        "history_empty": "No hay transcripciones para guardar",
    },
    "en": {
        "app_title": "🎤 VOICE TO TEXT",
        "menu_record": "Record",
        "menu_config": "Configure",
        "menu_exit": "Exit",
        "menu_back": "Back",
        "menu_duration": "Duration",
        "menu_language": "Language",
        "recording": "RECORDING",
        "speak_now": "SPEAK NOW!",
        "transcribing": "Transcribing",
        "transcription": "TRANSCRIPTION",
        "no_audio": "No audio detected",
        "no_audio_hint": "Did you speak during recording?",
        "mic_check": "Mic:",
        "mic_ready": "Ready",
        "mic_not_found": "Not detected",
        "config_title": "CONFIGURATION",
        "config_duration": "Duration",
        "config_language": "Language",
        "option": "Option",
        "goodbye": "Goodbye!",
        "ready": "Environment ready. Ctrl+C to exit.",
        "loading_model": "Loading Whisper model...",
        "action_duration": "Duration",
        "action_language": "Language",
        "action_exit": "Exit",
        "continue_prompt": "Continue",
        "language_en": "English",
        "language_es": "Spanish",
        "language_fr": "French",
        "language_de": "German",
        "history_saved": "History saved",
        "history_empty": "No transcriptions to save",
    },
}


def get_text(key: str, lang: str = "es") -> str:
    """Get translated text for a key."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["es"]).get(key, key)


def get_language_label(lang_code: str, ui_lang: str = "es") -> str:
    """Get language label in the UI language."""
    key = f"language_{lang_code}"
    return get_text(key, ui_lang)
