"""UI components for voice-to-text using Rich library."""

import time
import unicodedata
from typing import Optional

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.text import Text

from .config import Config
from .i18n import get_text, get_language_label

console = Console()
BOX_STYLE = ROUNDED


def _display_width(text: str) -> int:
    """Calculate display width accounting for wide characters and emoji."""
    import re
    
    clean = re.sub(r"\[/?[^\]]*\]", "", text)
    width = 0
    for char in clean:
        if unicodedata.east_asian_width(char) in ("F", "W"):
            width += 2
        elif ord(char) > 127:
            width += 2
        else:
            width += 1
    return width


class UI:
    def __init__(self, config: Config):
        self.config = config

    def _create_panel(self, content: str, subtitle: str = "", border_style: str = "cyan") -> Panel:
        """Create a panel that expands to full console width."""
        return Panel(
            content,
            subtitle=subtitle,
            box=BOX_STYLE,
            border_style=border_style,
            padding=(0, 2),
            expand=True,
            width=console.width,
        )

    def _build_menu_content(self, items: list[tuple[str, str, str]]) -> str:
        """Build menu content with aligned items."""
        max_width = max(_display_width(f"  {num}  {emoji}  {label}") for num, emoji, label in items)
        console_width = console.width - 4
        width = max(max_width, console_width - 10)
        
        lines = [""]
        for num, emoji, label in items:
            line = f"  {num}  {emoji}  {label}"
            padding = width - _display_width(line)
            lines.append(line + " " * padding)
            lines.append("")
        
        return "\n".join(lines)

    def show_menu(self) -> str:
        """Show main menu and get user choice."""
        lang = self.config.ui_language

        items = [
            ("[1]", "🎙️", get_text("menu_record", lang)),
            ("[2]", "⚙️", get_text("menu_config", lang)),
            ("[3]", "🚪", get_text("menu_exit", lang)),
        ]

        content = self._build_menu_content(items)

        duration_text = f"{self.config.duration}s"
        lang_text = get_language_label(self.config.language, lang)
        subtitle = f"{duration_text} | {lang_text}"

        console.print()
        console.print(self._create_panel(content, subtitle=subtitle))

        try:
            choice = console.input(f"\n[bold cyan]{get_text('option', lang)}:[/bold cyan] ")
            return choice.strip()
        except (EOFError, KeyboardInterrupt):
            return "3"

    def show_recording_start(self):
        """Show recording start message."""
        lang = self.config.ui_language

        lines = [
            "",
            f"  [bold red]🎙️  {get_text('recording', lang)}[/bold red]",
            "",
            f"  [bold yellow]{get_text('speak_now', lang)}[/bold yellow]",
            "",
        ]

        console.print()
        console.print(self._create_panel("\n".join(lines), border_style="red"))

    def show_progress(self, duration: int, mic_level: Optional[float] = None):
        """Show recording progress with countdown."""
        lang = self.config.ui_language
        lang_label = get_language_label(self.config.language, lang)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task(f"[cyan]{lang_label} • {duration}s", total=duration)

            for _ in range(duration):
                time.sleep(1)
                progress.update(task, advance=1)

    def show_mic_status(self, working: bool):
        """Show microphone status."""
        lang = self.config.ui_language
        if working:
            console.print(f"[green]🎤 {get_text('mic_check', lang)} ✅ {get_text('mic_ready', lang)}[/green]")
        else:
            console.print(f"[yellow]🎤 {get_text('mic_check', lang)} ⚠️  {get_text('mic_not_found', lang)}[/yellow]")

    def show_transcription(self, text: str):
        """Show transcription result."""
        lang = self.config.ui_language
        lang_label = get_language_label(self.config.language, lang)

        if not text:
            lines = [
                "",
                f"  [bold yellow]⚠️  {get_text('no_audio', lang)}[/bold yellow]",
                "",
                f"  [dim]{get_text('no_audio_hint', lang)}[/dim]",
                "",
            ]
            console.print(self._create_panel("\n".join(lines), border_style="yellow"))
        else:
            lines = [
                "",
                f"  [bold green]✅ {get_text('transcription', lang)} ({lang_label})[/bold green]",
                "",
                f"  {text}",
                "",
            ]
            console.print(self._create_panel("\n".join(lines), border_style="green"))

    def show_config(self) -> str:
        """Show configuration menu and get choice."""
        lang = self.config.ui_language
        lang_label = get_language_label(self.config.language, lang)
        model_label = self.config.get_model_label()

        items = [
            ("[1]", "⏱️", f"{get_text('config_duration', lang)} [{self.config.duration}s]"),
            ("[2]", "🌐", f"{get_text('config_language', lang)} [{lang_label}]"),
            ("[3]", "🧠", f"Model [{model_label}]"),
            ("[4]", "←", get_text("menu_back", lang)),
        ]

        content = self._build_menu_content(items)

        console.print()
        console.print(self._create_panel(content, border_style="magenta"))

        try:
            choice = console.input(f"\n[bold cyan]{get_text('option', lang)}:[/bold cyan] ")
            return choice.strip()
        except (EOFError, KeyboardInterrupt):
            return "4"

    def show_model_selector(self) -> Optional[str]:
        """Show model selector and return selected model size."""
        lang = self.config.ui_language

        items = [
            ("[1]", "🧠", f"tiny ({'≈75MB'})"),
            ("[2]", "🧠", f"base ({'≈150MB'})"),
            ("[3]", "🧠", f"small ({'≈500MB'})"),
            ("[4]", "🧠", f"medium ({'≈1.5GB'})"),
            ("[0]", "←", get_text("menu_back", lang)),
        ]

        content = self._build_menu_content(items)

        console.print()
        console.print(self._create_panel(content, border_style="cyan"))

        try:
            choice = console.input(f"[bold cyan]{get_text('option', lang)}:[/bold cyan] ")
            if choice.strip() == "0":
                return None
            model_map = {"1": "tiny", "2": "base", "3": "small", "4": "medium"}
            return model_map.get(choice.strip())
        except (EOFError, KeyboardInterrupt):
            return None

    def show_language_selector(self) -> Optional[str]:
        """Show language selector and return selected language code."""
        lang = self.config.ui_language

        items = [
            ("[1]", "🇬🇧", "English"),
            ("[2]", "🇪🇸", "Español"),
            ("[3]", "🇫🇷", "Français"),
            ("[4]", "🇩🇪", "Deutsch"),
            ("[0]", "←", get_text("menu_back", lang)),
        ]

        content = self._build_menu_content(items)

        console.print()
        console.print(self._create_panel(content, border_style="cyan"))

        try:
            choice = console.input(f"[bold cyan]{get_text('option', lang)}:[/bold cyan] ")
            if choice.strip() == "0":
                return None
            lang_map = {"1": "en", "2": "es", "3": "fr", "4": "de"}
            return lang_map.get(choice.strip())
        except (EOFError, KeyboardInterrupt):
            return None

    def prompt_duration(self) -> Optional[int]:
        """Prompt for duration input."""
        lang = self.config.ui_language
        try:
            value = console.input(f"[bold cyan]{get_text('config_duration', lang)} [{self.config.duration}]: [/bold cyan] ")
            if value.strip():
                return int(value.strip())
        except (ValueError, EOFError, KeyboardInterrupt):
            pass
        return None

    def show_error(self, message: str):
        """Show error message in a panel."""
        lines = ["", f"  [bold red]❌ {message}[/bold red]", ""]
        console.print(self._create_panel("\n".join(lines), border_style="red"))

    def show_warning(self, message: str):
        """Show warning message in a panel."""
        lines = ["", f"  [bold yellow]⚠️  {message}[/bold yellow]", ""]
        console.print(self._create_panel("\n".join(lines), border_style="yellow"))

    def show_success(self, message: str):
        """Show success message in a panel."""
        lines = ["", f"  [bold green]✅ {message}[/bold green]", ""]
        console.print(self._create_panel("\n".join(lines), border_style="green"))

    def show_goodbye(self):
        """Show goodbye message."""
        lang = self.config.ui_language
        lines = ["", f"  [bold cyan]{get_text('goodbye', lang)} 👋[/bold cyan]", ""]
        console.print(self._create_panel("\n".join(lines), border_style="cyan"))

    def show_actions(self) -> str:
        """Show action prompts and get choice."""
        lang = self.config.ui_language
        console.print(f"\n[dim][D]{get_text('action_duration', lang)} │ [I]{get_text('action_language', lang)} │ [S]{get_text('action_exit', lang)}[/dim]")
        try:
            action = console.input(f"[bold cyan]{get_text('continue_prompt', lang)}:[/bold cyan] ")
            return action.strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "s"
