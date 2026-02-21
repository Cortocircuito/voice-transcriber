"""UI components for voice-to-text using Rich library."""

import time
import unicodedata
from typing import Optional

from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.text import Text

from .config import Config
from .i18n import get_text, get_language_label

console = Console(color_system="auto", force_terminal=True)
BOX_STYLE = ROUNDED
MIN_MENU_WIDTH = 40


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
        )

    def _build_menu_content(self, items: list[tuple[str, str, str]]) -> str:
        """Build menu content with aligned items."""
        max_item_width = max(
            _display_width(f"  {num}  {emoji}  {label}") for num, emoji, label in items
        )
        console_width = console.width - 4
        width = max(max_item_width, console_width - 10, MIN_MENU_WIDTH)

        lines = [""]
        for num, emoji, label in items:
            line = f"  {num}  {emoji}  {label}"
            line_width = _display_width(line)
            padding = width - line_width
            lines.append(line + " " * max(0, padding))
            lines.append("")

        return "\n".join(lines)

    def show_menu(self) -> str:
        """Show main menu and get user choice."""
        lang = self.config.ui_language

        items = [
            ("[1]", "🎙️", get_text("menu_record", lang)),
            ("[2]", "📚", get_text("menu_practice", lang)),
            ("[3]", "⚙️", get_text("menu_config", lang)),
            ("[4]", "🚪", get_text("menu_exit", lang)),
        ]

        content = self._build_menu_content(items)

        duration_text = f"{self.config.duration}s"
        lang_text = get_language_label(self.config.language, lang)
        model_text = self.config.model_size
        subtitle = f"{duration_text} | {lang_text} | {model_text}"

        console.print()
        console.print(self._create_panel(content, subtitle=subtitle))

        try:
            choice = console.input(f"\n[bold cyan]{get_text('option', lang)}:[/bold cyan] ")
            return choice.strip()
        except (EOFError, KeyboardInterrupt):
            return "4"

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

    def show_transcribing(self):
        """Show transcription in progress message."""
        lang = self.config.ui_language
        console.print()
        console.print(f"[bold cyan]🔄 {get_text('transcribing', lang)}...[/bold cyan]")
        console.print()

    def show_segment(self, text: str, segment_num: int):
        """Show a transcribed segment in real-time."""
        console.print(f"  [dim][{segment_num}][/dim] {text}")

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

    def show_config(self, has_history: bool = False) -> str:
        """Show configuration menu and get choice."""
        lang = self.config.ui_language
        lang_label = get_language_label(self.config.language, lang)
        model_label = self.config.get_model_label()

        items = [
            ("[1]", "⏱️", f"{get_text('config_duration', lang)} [{self.config.duration}s]"),
            ("[2]", "🌐", f"{get_text('config_language', lang)} [{lang_label}]"),
            ("[3]", "💾", f"Model [{model_label}]"),
            ("[4]", "🗑️", f"{get_text('config_history', lang)}"),
            ("[5]", "←", get_text("menu_back", lang)),
        ]

        content = self._build_menu_content(items)

        console.print()
        console.print(self._create_panel(content, border_style="magenta"))

        try:
            choice = console.input(f"\n[bold cyan]{get_text('option', lang)}:[/bold cyan] ")
            return choice.strip()
        except (EOFError, KeyboardInterrupt):
            return "5"

    def show_model_selector(self) -> Optional[str]:
        """Show model selector and return selected model size."""
        lang = self.config.ui_language
        current = self.config.model_size

        items = [
            ("[1]", "⚡", f"{get_text('model_tiny', lang)}  {'✓' if current == 'tiny' else ''}"),
            ("[2]", "📦", f"{get_text('model_base', lang)}  {'✓' if current == 'base' else ''}"),
            ("[3]", "🚀", f"{get_text('model_small', lang)}  {'✓' if current == 'small' else ''}"),
            ("[4]", "💪", f"{get_text('model_medium', lang)}  {'✓' if current == 'medium' else ''}"),
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

    def confirm_clear_history(self, entry_count: int) -> bool:
        """Show confirmation dialog for clearing history.
        
        Args:
            entry_count: Number of entries in history
            
        Returns:
            True if user confirms, False otherwise
        """
        lang = self.config.ui_language
        
        if entry_count == 0:
            self.show_warning(get_text("history_no_entries", lang))
            return False
        
        console.print()
        console.print(f"[bold yellow]🗑️  {get_text('history_confirm_clear', lang)} ({entry_count} entries)[/bold yellow]")
        
        try:
            response = console.input(
                f"[bold cyan]{get_text('yes', lang)}/{get_text('no', lang)}:[/bold cyan] "
            )
            return response.strip().lower() in ["y", "yes", "s", "sí", "si"]
        except (EOFError, KeyboardInterrupt):
            return False

    def show_lessons_menu(self, lessons: list, is_offline: bool = False) -> Optional[int]:
        """Show lesson selection menu.
        
        Args:
            lessons: List of Lesson objects
            is_offline: Whether we're using cached data
            
        Returns:
            Selected lesson index (0-based), or None for refresh/back
        """
        lang = self.config.ui_language
        
        if not lessons:
            lines = [
                "",
                f"  [bold yellow]📚 {get_text('lessons_no_cached', lang)}[/bold yellow]",
                "",
                "  [R] 🔄 Refresh from web",
                "  [0] ← Back",
                "",
            ]
            console.print()
            console.print(self._create_panel("\n".join(lines), border_style="yellow"))
            
            try:
                choice = console.input(f"[bold cyan]{get_text('option', lang)}:[/bold cyan] ")
                if choice.strip().lower() == "r":
                    return -1
                return None
            except (EOFError, KeyboardInterrupt):
                return None
        
        lines = ["", f"  [bold cyan]📚 {get_text('lessons_title', lang)}[/bold cyan]", ""]
        
        if is_offline:
            lines.append(f"  [dim]⚠️  {get_text('lessons_offline', lang)}[/dim]")
            lines.append("")
        
        for i, lesson in enumerate(lessons[:8]):
            title = lesson.title[:50] + "..." if len(lesson.title) > 50 else lesson.title
            lines.append(f"  [{i+1}] {title}")
            lines.append(f"      [dim]{lesson.date}[/dim]")
            lines.append("")
        
        lines.append(f"  [R] 🔄 {get_text('lessons_refresh', lang)}")
        lines.append(f"  [0] ← {get_text('menu_back', lang)}")
        lines.append("")
        
        console.print()
        console.print(self._create_panel("\n".join(lines), border_style="blue"))
        
        try:
            choice = console.input(f"\n[bold cyan]{get_text('option', lang)}:[/bold cyan] ")
            choice = choice.strip().lower()
            
            if choice == "r":
                return -1
            if choice == "0":
                return None
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(lessons):
                    return idx
            except ValueError:
                pass
            
            return None
        except (EOFError, KeyboardInterrupt):
            return None

    def show_level_selector(self, lesson) -> Optional[str]:
        """Show level selector for a lesson.
        
        Args:
            lesson: Lesson object
            
        Returns:
            Selected level string, or None for back
        """
        lang = self.config.ui_language
        
        levels = lesson.levels if hasattr(lesson, 'levels') else ["2", "3"]
        
        lines = [
            "",
            f"  [bold cyan]📖 {get_text('level_selector', lang)}[/bold cyan]",
            "",
            f"  [dim]{lesson.title[:60]}[/dim]",
            "",
        ]
        
        level_labels = {
            "0": "Beginner",
            "1": "Elementary", 
            "2": "Pre-Intermediate",
            "3": "Intermediate",
            "4": "Upper-Intermediate",
            "5": "Advanced",
            "6": "Proficient",
        }
        
        for level in levels:
            label = level_labels.get(level, f"Level {level}")
            lines.append(f"  [{level}] {get_text('level', lang)} {level} - {label}")
            lines.append("")
        
        lines.append(f"  [0] ← {get_text('menu_back', lang)}")
        lines.append("")
        
        console.print()
        console.print(self._create_panel("\n".join(lines), border_style="cyan"))
        
        try:
            choice = console.input(f"[bold cyan]{get_text('option', lang)}:[/bold cyan] ")
            choice = choice.strip()
            
            if choice == "0":
                return None
            
            if choice in levels:
                return choice
            
            return None
        except (EOFError, KeyboardInterrupt):
            return None

    def show_lesson_text(self, text: str, level: str) -> None:
        """Show lesson text for reading practice.
        
        Args:
            text: Lesson text to display
            level: Selected level
        """
        lang = self.config.ui_language
        
        words = text.split()
        display_text = " ".join(words[:100])
        if len(words) > 100:
            display_text += "..."
        
        lines = [
            "",
            f"  [bold cyan]📖 {get_text('reading_mode', lang)} - {get_text('level', lang)} {level}[/bold cyan]",
            "",
            f"  [dim]{get_text('read_aloud', lang)}[/dim]",
            "",
        ]
        
        text_lines = display_text.split("\n")
        for line in text_lines[:15]:
            lines.append(f"  {line}")
        
        if len(text_lines) > 15:
            lines.append(f"  [dim]... ({len(text_lines) - 15} more lines)[/dim]")
        
        lines.append("")
        
        console.print()
        console.print(self._create_panel("\n".join(lines), border_style="green"))

    def show_lesson_page(
        self,
        text: str,
        level: str,
        page_num: int,
        total_pages: int,
        estimated_duration: int,
    ) -> str:
        """Show a page of lesson text with navigation.
        
        Args:
            text: Page text to display
            level: Selected level
            page_num: Current page number (1-indexed)
            total_pages: Total number of pages
            estimated_duration: Estimated reading time in seconds
            
        Returns:
            User action: 'record', 'next', 'prev', 'duration', 'back'
        """
        lang = self.config.ui_language
        
        min_label = get_text("minutes_short", lang)
        sec_label = get_text("seconds_short", lang)
        
        if estimated_duration >= 60:
            mins = estimated_duration // 60
            secs = estimated_duration % 60
            if secs > 0:
                time_str = f"{mins}:{secs:02d} {min_label}"
            else:
                time_str = f"{mins} {min_label}"
        else:
            time_str = f"{estimated_duration} {sec_label}"
        
        lines = [
            "",
            f"  [bold cyan]📖 {get_text('reading_mode', lang)} - {get_text('level', lang)} {level}[/bold cyan]",
            "",
            f"  [dim]{get_text('read_aloud', lang)}[/dim]",
            f"  [dim]{get_text('page', lang)} {page_num} {get_text('of', lang)} {total_pages} | {get_text('estimated_time', lang)}: {time_str}[/dim]",
            "",
        ]
        
        text_lines = text.split("\n")
        for line in text_lines[:20]:
            if line.strip():
                lines.append(f"  {line}")
        
        lines.append("")
        
        console.print()
        console.print(self._create_panel("\n".join(lines), border_style="green"))
        
        nav_parts = []
        if total_pages > 1 and page_num < total_pages:
            nav_parts.append(f"[N] {get_text('next_page', lang)}")
        nav_parts.append(f"[D] {get_text('change_duration', lang)}")
        nav_parts.append(f"[R] {get_text('start_recording', lang)}")
        if page_num > 1:
            nav_parts.append(f"[P] {get_text('prev_page', lang)}")
        nav_parts.append(f"[B] {get_text('menu_back', lang)}")
        
        nav_str = " │ ".join(nav_parts)
        
        console.print(f"\n[dim]{nav_str}[/dim]")
        
        try:
            choice = console.input(f"\n[bold cyan]{get_text('option', lang)}:[/bold cyan] ")
            choice = choice.strip().lower()
            
            if choice == "r":
                return "record"
            elif choice == "n" and page_num < total_pages:
                return "next"
            elif choice == "p" and page_num > 1:
                return "prev"
            elif choice == "d":
                return "duration"
            elif choice == "b":
                return "back"
            else:
                return "record"
        except (EOFError, KeyboardInterrupt):
            return "back"

    def prompt_duration_change(self, current_duration: int, calculated_duration: int) -> Optional[int]:
        """Prompt user to change recording duration.
        
        Args:
            current_duration: Current duration setting
            calculated_duration: Calculated duration based on text
            
        Returns:
            New duration or None
        """
        lang = self.config.ui_language
        
        console.print()
        
        lines = [
            "",
            f"  [bold cyan]⏱️ {get_text('change_duration', lang)}[/bold cyan]",
            "",
            f"  {get_text('current_duration', lang)}: {current_duration}s",
            f"  {get_text('estimated_time', lang)}: {calculated_duration}s",
            "",
        ]
        
        console.print(self._create_panel("\n".join(lines), border_style="cyan"))
        
        try:
            value = console.input(f"[bold cyan]{get_text('set_duration', lang)} [{calculated_duration}]: [/bold cyan] ")
            if value.strip():
                new_duration = int(value.strip())
                if new_duration > 0:
                    return new_duration
        except (ValueError, EOFError, KeyboardInterrupt):
            pass
        
        return None

    def show_comparison(self, original: str, transcribed: str, result) -> None:
        """Show comparison results with error highlighting.
        
        Args:
            original: Original lesson text
            transcribed: User's transcription
            result: ComparisonResult object
        """
        from rich.console import Group
        from rich.text import Text as RichText
        
        lang = self.config.ui_language
        
        accuracy_pct = result.accuracy * 100
        accuracy_color = "green" if accuracy_pct >= 80 else "yellow" if accuracy_pct >= 60 else "red"
        
        header_lines = [
            "",
            f"  [bold cyan]📊 {get_text('comparison_title', lang)}[/bold cyan]",
            "",
        ]
        
        orig_error_indices = result.orig_error_indices if hasattr(result, 'orig_error_indices') else set()
        orig_words = result.original_words[:80]
        orig_rich = RichText()
        for i, word in enumerate(orig_words):
            if i in orig_error_indices:
                orig_rich.append(word + " ", "bold red")
            else:
                orig_rich.append(word + " ", "")
        
        trans_error_indices = result.trans_error_indices if hasattr(result, 'trans_error_indices') else set()
        trans_words = result.transcribed_words[:80]
        trans_rich = RichText()
        for i, word in enumerate(trans_words):
            if i in trans_error_indices:
                trans_rich.append(word + " ", "bold red")
            else:
                trans_rich.append(word + " ", "")
        
        content_lines = [
            f"  [bold]📖 {get_text('comparison_original', lang)}:[/bold]",
            "",
            orig_rich,
        ]
        
        if len(result.original_words) > 80:
            content_lines.append("  [dim]...[/dim]")
        
        content_lines.extend([
            "",
            f"  [bold]📝 {get_text('comparison_yours', lang)}:[/bold]",
            "",
            trans_rich,
        ])
        
        if len(result.transcribed_words) > 80:
            content_lines.append("  [dim]...[/dim]")
        
        content_lines.extend([
            "",
            "  " + "─" * 50,
            "",
            f"  [{accuracy_color}]📈 {get_text('accuracy', lang)}: {accuracy_pct:.1f}% ({result.correct_count}/{result.total_count} {get_text('words_correct', lang)})[/{accuracy_color}]",
        ])
        
        full_content = "\n".join(header_lines) + "\n" + "\n".join([str(x) if not isinstance(x, RichText) else "" for x in content_lines])
        
        console.print()
        console.print(self._create_panel(Group(*content_lines), border_style="magenta"))

    def show_practice_actions(self) -> str:
        """Show practice session action prompts.
        
        Returns:
            User's choice: 'r' for retry, 'n' for new lesson, 's' for stop
        """
        lang = self.config.ui_language
        console.print(f"\n[dim][R]{get_text('try_again', lang)} │ [N]{get_text('new_lesson', lang)} │ [S]{get_text('action_exit', lang)}[/dim]")
        try:
            action = console.input(f"[bold cyan]{get_text('continue_prompt', lang)}:[/bold cyan] ")
            return action.strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "s"

    def show_lessons_loading(self) -> None:
        """Show loading message for lessons."""
        lang = self.config.ui_language
        console.print()
        console.print(f"[bold cyan]📚 {get_text('lessons_loading', lang)}[/bold cyan]")

    def show_paragraph_page(
        self,
        text: str,
        level: str,
        paragraph_num: int,
        total_paragraphs: int,
        estimated_duration: int,
    ) -> str:
        """Show a single paragraph with navigation.
        
        Args:
            text: Paragraph text to display
            level: Selected level
            paragraph_num: Current paragraph number (1-indexed)
            total_paragraphs: Total number of paragraphs
            estimated_duration: Estimated reading time in seconds
            
        Returns:
            User action: 'record', 'next', 'prev', 'duration', 'back'
        """
        lang = self.config.ui_language
        
        min_label = get_text("minutes_short", lang)
        sec_label = get_text("seconds_short", lang)
        
        if estimated_duration >= 60:
            mins = estimated_duration // 60
            secs = estimated_duration % 60
            if secs > 0:
                time_str = f"{mins}:{secs:02d} {min_label}"
            else:
                time_str = f"{mins} {min_label}"
        else:
            time_str = f"{estimated_duration} {sec_label}"
        
        lines = [
            "",
            f"  [bold cyan]📖 {get_text('reading_mode', lang)} - {get_text('level', lang)} {level}[/bold cyan]",
            "",
            f"  [dim]{get_text('paragraph', lang)} {paragraph_num} {get_text('of', lang)} {total_paragraphs}[/dim]",
            f"  [dim]{get_text('estimated_time', lang)}: {time_str}[/dim]",
            "",
            f"  [dim]{get_text('read_aloud', lang)}[/dim]",
            "",
        ]
        
        text_lines = text.split("\n")
        for line in text_lines[:15]:
            if line.strip():
                lines.append(f"  {line}")
        
        if len(text_lines) > 15:
            lines.append(f"  [dim]...[/dim]")
        
        lines.append("")
        
        console.print()
        console.print(self._create_panel("\n".join(lines), border_style="green"))
        
        nav_parts = []
        if paragraph_num < total_paragraphs:
            nav_parts.append(f"[N] {get_text('next_paragraph', lang)}")
        nav_parts.append(f"[D] {get_text('change_duration', lang)}")
        nav_parts.append(f"[R] {get_text('start_recording', lang)}")
        if paragraph_num > 1:
            nav_parts.append(f"[P] {get_text('prev_paragraph', lang)}")
        nav_parts.append(f"[B] {get_text('menu_back', lang)}")
        
        nav_str = " │ ".join(nav_parts)
        
        console.print(f"\n[dim]{nav_str}[/dim]")
        
        try:
            choice = console.input(f"\n[bold cyan]{get_text('option', lang)}:[/bold cyan] ")
            choice = choice.strip().lower()
            
            if choice == "r":
                return "record"
            elif choice == "n" and paragraph_num < total_paragraphs:
                return "next"
            elif choice == "p" and paragraph_num > 1:
                return "back"
            elif choice == "d":
                return "duration"
            elif choice == "b":
                return "back"
            else:
                return "record"
        except (EOFError, KeyboardInterrupt):
            return "back"
    
    def show_paragraph_actions(self) -> None:
        """Show actions after recording a paragraph (not the last one)."""
        lang = self.config.ui_language
        console.print(
            f"\n[dim][R]{get_text('try_again', lang)} │ "
            f"[N/{get_text('next_paragraph_short', lang)}]{get_text('next_paragraph', lang)} │ "
            f"[S]{get_text('action_exit', lang)}[/dim]"
        )
    
    def show_last_paragraph_actions(self) -> None:
        """Show actions after recording the last paragraph."""
        lang = self.config.ui_language
        console.print(
            f"\n[dim][R]{get_text('try_again', lang)} │ "
            f"[N]{get_text('new_lesson', lang)} │ "
            f"[S]{get_text('action_exit', lang)}[/dim]"
        )
    
    def show_lesson_complete(self) -> None:
        """Show message when all paragraphs are completed."""
        lang = self.config.ui_language
        lines = [
            "",
            f"  [bold green]🎉 {get_text('lesson_complete', lang)}[/bold green]",
            "",
        ]
        console.print()
        console.print(self._create_panel("\n".join(lines), border_style="green"))
