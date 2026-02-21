"""Configuration manager for voice-to-text."""

from .config import Config
from .history import HistoryManager
from .i18n import get_language_label, get_text
from .ui import UI


class ConfigManager:
    """Manages configuration settings."""

    def __init__(
        self,
        config: Config,
        ui: UI,
        history: HistoryManager,
    ):
        self.config = config
        self.ui = ui
        self.history = history

    def run(self) -> None:
        """Handle configuration menu."""
        while True:
            stats = self.history.get_stats()
            total_entries = stats["total"] + len(self.history.get_entries())
            choice = self.ui.show_config(has_history=total_entries > 0)

            if choice == "1":
                new_duration = self.ui.prompt_duration()
                if new_duration:
                    validated = self.config.validate_duration(str(new_duration))
                    if validated != self.config.duration:
                        self.config.duration = validated
                        self.ui.show_success(f"{self.config.duration}s")
            elif choice == "2":
                lang_code = self.ui.show_language_selector()
                if lang_code:
                    self.config.language = lang_code
                    lang_label = get_language_label(lang_code, self.config.ui_language)
                    self.ui.show_success(lang_label)
            elif choice == "3":
                model_size = self.ui.show_model_selector()
                if model_size:
                    self.config.model_size = model_size
                    self.ui.show_success(self.config.get_model_label())
            elif choice == "4":
                if self.ui.confirm_clear_history(total_entries):
                    if self.history.clear_all():
                        self.ui.show_success(get_text("history_cleared", self.config.ui_language))
                    else:
                        self.ui.show_error("Failed to clear history")
            else:
                break
