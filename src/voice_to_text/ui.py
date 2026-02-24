"""UI components for voice-to-text using Rich library."""

import time
from typing import Any, Optional, Union

from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text

from .config import Config
from .constants import (
    COLOR_ACCENT,
    COLOR_SUCCESS,
    COLOR_WARNING,
)
from .i18n import get_text, get_language_label
from .phonetics import get_words_phonetics

MAX_WIDTH = 96
ACCENT = COLOR_ACCENT  # Alias for backward compatibility
BOX_STYLE = ROUNDED


class UI:
    def __init__(self, config: Config):
        self.config = config
        self.console = Console(color_system="auto", force_terminal=True)

    def _create_panel(
        self,
        content: Union[str, Any],
        subtitle: str = "",
        border_style: str = "dim",
        title: str = "",
    ) -> Align:
        """Create a width-capped, centered panel."""
        width = min(MAX_WIDTH, self.console.width - 2)
        panel = Panel(
            content,
            title=f"[{ACCENT}]{title}[/{ACCENT}]" if title else None,
            subtitle=subtitle if subtitle else None,
            box=BOX_STYLE,
            border_style=border_style,
            padding=(0, 2),
            expand=False,
            width=width,
        )
        return Align.center(panel)

    def _menu_table(self, items: list[tuple[str, str]]) -> Table:
        """Build an aligned menu using Table.grid."""
        grid = Table.grid(padding=(0, 2))
        grid.add_column(style=f"bold {ACCENT}", no_wrap=True)
        grid.add_column()
        for key, label in items:
            grid.add_row(key, label)
        return grid

    def show_menu(self) -> str:
        """Show main menu and get user choice."""
        lang = self.config.ui_language

        items = [
            ("[1]", get_text("menu_record", lang)),
            ("[2]", get_text("menu_practice", lang)),
            ("[3]", get_text("menu_config", lang)),
            ("[4]", get_text("menu_exit", lang)),
        ]

        duration_text = f"{self.config.duration}s"
        lang_text = get_language_label(self.config.language, lang)
        model_text = self.config.model_size
        subtitle = f"[dim]{duration_text} | {lang_text} | {model_text}[/dim]"

        self.console.print()
        self.console.print(
            self._create_panel(
                Align.center(self._menu_table(items)),
                subtitle=subtitle,
            )
        )

        try:
            choice = self.console.input(
                f"\n[bold {ACCENT}]{get_text('option', lang)}:[/bold {ACCENT}] "
            )
            return choice.strip()
        except (EOFError, KeyboardInterrupt):
            return "4"

    def show_recording_start(self):
        """Show recording start message."""
        lang = self.config.ui_language
        content = Text()
        content.append(f"\n  {get_text('recording', lang)}\n", style="bold red")
        content.append(f"\n  {get_text('speak_now', lang)}\n", style="bold yellow")
        self.console.print()
        self.console.print(self._create_panel(content, border_style="red"))

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
            console=self.console,
        ) as progress:
            task = progress.add_task(
                f"[{ACCENT}]{lang_label} • {duration}s", total=duration
            )

            for _ in range(duration):
                time.sleep(1)
                progress.update(task, advance=1)

    def show_mic_status(self, working: bool):
        """Show microphone status."""
        lang = self.config.ui_language
        if working:
            self.console.print(
                f"[{COLOR_SUCCESS}]{get_text('mic_check', lang)} {get_text('mic_ready', lang)}[/{COLOR_SUCCESS}]"
            )
        else:
            self.console.print(
                f"[{COLOR_WARNING}]{get_text('mic_check', lang)} {get_text('mic_not_found', lang)}[/{COLOR_WARNING}]"
            )

    def show_lessons_download_progress(self) -> None:
        """Show indeterminate progress for lesson download."""
        lang = self.config.ui_language
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            progress.add_task(
                f"[{ACCENT}]{get_text('lessons_downloading', lang)}",
                total=None,
            )
            time.sleep(0.5)

    def show_lessons_download_complete(self) -> None:
        """Show lesson download complete message."""
        lang = self.config.ui_language
        self.console.print(
            f"[{COLOR_SUCCESS}]{get_text('lessons_download_complete', lang)}[/{COLOR_SUCCESS}]"
        )

    def confirm_lesson_download(self) -> bool:
        """Ask user if they want to download lessons.

        Returns:
            True if user confirms, False otherwise
        """
        lang = self.config.ui_language
        while True:
            choice = self.console.input(
                f"[bold {ACCENT}]{get_text('lessons_download_prompt', lang)}[/bold {ACCENT}] "
            )
            choice_lower = choice.strip().lower()
            if choice_lower in ("y", "yes", get_text("yes", lang).lower()):
                return True
            if choice_lower in ("n", "no", get_text("no", lang).lower()):
                return False

    def show_transcribing(self):
        """Show transcription in progress message."""
        lang = self.config.ui_language
        self.console.print()
        self.console.print(
            f"[bold {ACCENT}]{get_text('transcribing', lang)}...[/bold {ACCENT}]"
        )
        self.console.print()

    def show_segment(self, text: str, segment_num: int):
        """Show a transcribed segment in real-time."""
        self.console.print(f"  [dim][{segment_num}][/dim] {text}")

    def show_transcription(self, text: str):
        """Show transcription result."""
        lang = self.config.ui_language
        lang_label = get_language_label(self.config.language, lang)

        if not text:
            content = (
                f"\n  [bold yellow]{get_text('no_audio', lang)}[/bold yellow]\n\n"
                f"  [dim]{get_text('no_audio_hint', lang)}[/dim]\n"
            )
            self.console.print(self._create_panel(content, border_style="yellow"))
        else:
            content = (
                f"\n  [bold green]{get_text('transcription', lang)} ({lang_label})[/bold green]\n\n"
                f"  {text}\n"
            )
            self.console.print(self._create_panel(content, border_style="green"))

    def show_config(self, has_history: bool = False) -> str:
        """Show configuration menu and get choice."""
        lang = self.config.ui_language
        lang_label = get_language_label(self.config.language, lang)
        model_label = self.config.get_model_label()

        items = [
            ("[1]", f"{get_text('config_duration', lang)} [{self.config.duration}s]"),
            ("[2]", f"{get_text('config_language', lang)} [{lang_label}]"),
            ("[3]", f"Model [{model_label}]"),
            ("[4]", get_text("config_history", lang)),
            ("[5]", get_text("menu_back", lang)),
        ]

        self.console.print()
        self.console.print(self._create_panel(Align.center(self._menu_table(items))))

        try:
            choice = self.console.input(
                f"\n[bold {ACCENT}]{get_text('option', lang)}:[/bold {ACCENT}] "
            )
            return choice.strip()
        except (EOFError, KeyboardInterrupt):
            return "5"

    def show_model_selector(self) -> Optional[str]:
        """Show model selector and return selected model size."""
        lang = self.config.ui_language
        current = self.config.model_size

        items = [
            (
                "[1]",
                f"{get_text('model_tiny', lang)}  {'*' if current == 'tiny' else ''}",
            ),
            (
                "[2]",
                f"{get_text('model_base', lang)}  {'*' if current == 'base' else ''}",
            ),
            (
                "[3]",
                f"{get_text('model_small', lang)}  {'*' if current == 'small' else ''}",
            ),
            (
                "[4]",
                f"{get_text('model_medium', lang)}  {'*' if current == 'medium' else ''}",
            ),
            ("[0]", get_text("menu_back", lang)),
        ]

        self.console.print()
        self.console.print(self._create_panel(Align.center(self._menu_table(items))))

        try:
            choice = self.console.input(
                f"[bold {ACCENT}]{get_text('option', lang)}:[/bold {ACCENT}] "
            )
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
            ("[1]", "English"),
            ("[2]", "Español"),
            ("[3]", "Français"),
            ("[4]", "Deutsch"),
            ("[0]", get_text("menu_back", lang)),
        ]

        self.console.print()
        self.console.print(self._create_panel(Align.center(self._menu_table(items))))

        try:
            choice = self.console.input(
                f"[bold {ACCENT}]{get_text('option', lang)}:[/bold {ACCENT}] "
            )
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
            value = self.console.input(
                f"[bold {ACCENT}]{get_text('config_duration', lang)} [{self.config.duration}]: [/bold {ACCENT}] "
            )
            if value.strip():
                return int(value.strip())
        except (ValueError, EOFError, KeyboardInterrupt):
            pass
        return None

    def show_error(self, message: str):
        """Show error message in a panel."""
        content = f"\n  [bold red]{message}[/bold red]\n"
        self.console.print(self._create_panel(content, border_style="red"))

    def show_warning(self, message: str):
        """Show warning message in a panel."""
        content = f"\n  [bold yellow]{message}[/bold yellow]\n"
        self.console.print(self._create_panel(content, border_style="yellow"))

    def show_success(self, message: str):
        """Show success message in a panel."""
        content = f"\n  [bold green]{message}[/bold green]\n"
        self.console.print(self._create_panel(content, border_style="green"))

    def show_goodbye(self):
        """Show goodbye message."""
        lang = self.config.ui_language
        content = f"\n  [bold {ACCENT}]{get_text('goodbye', lang)}[/bold {ACCENT}]\n"
        self.console.print(self._create_panel(content))

    def show_actions(self) -> str:
        """Show action prompts and get choice."""
        lang = self.config.ui_language
        self.console.print(
            f"\n[dim][D] {get_text('action_duration', lang)} | "
            f"[I] {get_text('action_language', lang)} | "
            f"[S] {get_text('action_exit', lang)}[/dim]"
        )
        try:
            action = self.console.input(
                f"[bold {ACCENT}]{get_text('continue_prompt', lang)}:[/bold {ACCENT}] "
            )
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

        self.console.print()
        self.console.print(
            f"[bold yellow]{get_text('history_confirm_clear', lang)} ({entry_count} entries)[/bold yellow]"
        )

        try:
            response = self.console.input(
                f"[bold {ACCENT}]{get_text('yes', lang)}/{get_text('no', lang)}:[/bold {ACCENT}] "
            )
            return response.strip().lower() in ["y", "yes", "s", "sí", "si"]
        except (EOFError, KeyboardInterrupt):
            return False

    def show_lessons_menu(
        self,
        lessons: list,
        page: int = 0,
        per_page: int = 5,
        is_offline: bool = False,
    ) -> Optional[int]:
        """Show lesson selection menu with pagination.

        Args:
            lessons: List of Lesson objects
            page: Current page (0-indexed)
            per_page: Lessons per page
            is_offline: Whether we're using cached data

        Returns:
            Selected lesson index (0-based), or:
            -1 for refresh
            -2 for next page
            -3 for previous page
            None for back
        """
        lang = self.config.ui_language

        if not lessons:
            content = (
                f"\n  [bold yellow]{get_text('lessons_no_cached', lang)}[/bold yellow]\n\n"
                f"  [dim][R] Refresh | [0] {get_text('menu_back', lang)}[/dim]\n"
            )
            self.console.print()
            self.console.print(
                self._create_panel(
                    content,
                    border_style="yellow",
                    title=get_text("lessons_title", lang),
                )
            )

            try:
                choice = self.console.input(
                    f"[bold {ACCENT}]{get_text('option', lang)}:[/bold {ACCENT}] "
                )
                if choice.strip().lower() == "r":
                    return -1
                return None
            except (EOFError, KeyboardInterrupt):
                return None

        total_pages = (len(lessons) + per_page - 1) // per_page
        start_idx = page * per_page
        end_idx = min(start_idx + per_page, len(lessons))
        page_lessons = lessons[start_idx:end_idx]

        grid = Table.grid(padding=(0, 2))
        grid.add_column(style=f"bold {ACCENT}", no_wrap=True)
        grid.add_column()
        grid.add_column(style="dim")

        if is_offline:
            self.console.print(f"\n[dim]{get_text('lessons_offline', lang)}[/dim]")

        for i, lesson in enumerate(page_lessons):
            global_idx = start_idx + i
            title = (
                lesson.title[:55] + "..." if len(lesson.title) > 55 else lesson.title
            )
            grid.add_row(f"[{global_idx + 1}]", title, lesson.date)

        nav_items = []
        if page > 0:
            nav_items.append(("[P]", get_text("prev_lessons", lang)))
        if page < total_pages - 1:
            nav_items.append(("[N]", get_text("next_lessons", lang)))
        nav_items.append(("[R]", get_text("lessons_refresh", lang)))
        nav_items.append(("[0]", get_text("menu_back", lang)))

        nav_grid = Table.grid(padding=(0, 2))
        nav_grid.add_column(style=f"bold {ACCENT}", no_wrap=True)
        nav_grid.add_column(style="dim")
        for key, label in nav_items:
            nav_grid.add_row(key, label)

        subtitle = f"[dim]{get_text('page', lang)} {page + 1} {get_text('of', lang)} {total_pages}[/dim]"
        content = Group(grid, Text(""), nav_grid)

        self.console.print()
        self.console.print(
            self._create_panel(
                content, subtitle=subtitle, title=get_text("lessons_title", lang)
            )
        )

        try:
            choice = self.console.input(
                f"\n[bold {ACCENT}]{get_text('option', lang)}:[/bold {ACCENT}] "
            )
            choice = choice.strip().lower()

            if choice == "r":
                return -1
            elif choice == "n" and page < total_pages - 1:
                return -2
            elif choice == "p" and page > 0:
                return -3
            elif choice == "0":
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

        levels = lesson.levels if hasattr(lesson, "levels") else ["2", "3"]

        level_labels = {
            "0": "Beginner",
            "1": "Elementary",
            "2": "Pre-Intermediate",
            "3": "Intermediate",
            "4": "Upper-Intermediate",
            "5": "Advanced",
            "6": "Proficient",
        }

        grid = Table.grid(padding=(0, 2))
        grid.add_column(style=f"bold {ACCENT}", no_wrap=True)
        grid.add_column()

        for level in levels:
            label = level_labels.get(level, f"Level {level}")
            grid.add_row(f"[{level}]", f"{get_text('level', lang)} {level} — {label}")

        grid.add_row("[0]", get_text("menu_back", lang))

        subtitle = f"[dim]{lesson.title[:60]}[/dim]"
        self.console.print()
        self.console.print(
            self._create_panel(
                Align.center(grid),
                subtitle=subtitle,
                title=get_text("level_selector", lang),
            )
        )

        try:
            choice = self.console.input(
                f"[bold {ACCENT}]{get_text('option', lang)}:[/bold {ACCENT}] "
            )
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

        content = (
            f"\n  [dim]{get_text('read_aloud', lang)}[/dim]\n\n"
            + "\n".join(f"  {line}" for line in display_text.split("\n")[:15] if line)
            + "\n"
        )

        self.console.print()
        self.console.print(
            self._create_panel(
                content,
                title=f"{get_text('reading_mode', lang)} — {get_text('level', lang)} {level}",
            )
        )

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
            time_str = (
                f"{mins}:{secs:02d} {min_label}" if secs else f"{mins} {min_label}"
            )
        else:
            time_str = f"{estimated_duration} {sec_label}"

        page_info = f"[dim]{get_text('page', lang)} {page_num} {get_text('of', lang)} {total_pages} | {get_text('estimated_time', lang)}: {time_str}[/dim]"

        content = (
            f"\n  [dim]{get_text('read_aloud', lang)}[/dim]\n"
            f"  {page_info}\n\n"
            + "\n".join(f"  {line}" for line in text.split("\n")[:20] if line.strip())
            + "\n"
        )

        self.console.print()
        self.console.print(
            self._create_panel(
                content,
                title=f"{get_text('reading_mode', lang)} — {get_text('level', lang)} {level}",
            )
        )

        nav_parts = []
        if total_pages > 1 and page_num < total_pages:
            nav_parts.append(f"[N] {get_text('next_page', lang)}")
        nav_parts.append(f"[D] {get_text('change_duration', lang)}")
        nav_parts.append(f"[R] {get_text('start_recording', lang)}")
        if page_num > 1:
            nav_parts.append(f"[P] {get_text('prev_page', lang)}")
        nav_parts.append(f"[B] {get_text('menu_back', lang)}")

        self.console.print(f"\n[dim]{' | '.join(nav_parts)}[/dim]")

        try:
            choice = self.console.input(
                f"\n[bold {ACCENT}]{get_text('option', lang)}:[/bold {ACCENT}] "
            )
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

    def prompt_duration_change(
        self, current_duration: int, calculated_duration: int
    ) -> Optional[int]:
        """Prompt user to change recording duration.

        Args:
            current_duration: Current duration setting
            calculated_duration: Calculated duration based on text

        Returns:
            New duration or current_duration if no input
        """
        lang = self.config.ui_language

        content = (
            f"\n  {get_text('record_duration', lang)}: {current_duration}s\n"
            f"  {get_text('estimated_time', lang)}: {calculated_duration}s\n"
        )

        self.console.print()
        self.console.print(
            self._create_panel(content, title=get_text("change_duration", lang))
        )

        try:
            value = self.console.input(
                f"[bold {ACCENT}]{get_text('set_duration', lang)} [{current_duration}]: [/bold {ACCENT}] "
            )
            if value.strip():
                new_duration = int(value.strip())
                if new_duration > 0:
                    return new_duration
                return current_duration
            return current_duration
        except (ValueError, EOFError, KeyboardInterrupt):
            return current_duration

    def show_comparison(self, original: str, transcribed: str, result) -> None:
        """Show comparison results with error highlighting.

        Args:
            original: Original lesson text
            transcribed: User's transcription
            result: ComparisonResult object
        """
        lang = self.config.ui_language

        accuracy_pct = result.accuracy * 100
        accuracy_color = (
            "green" if accuracy_pct >= 80 else "yellow" if accuracy_pct >= 60 else "red"
        )

        orig_error_indices = (
            result.orig_error_indices
            if hasattr(result, "orig_error_indices")
            else set()
        )
        orig_words = result.original_words[:80]
        orig_rich = Text()
        for i, word in enumerate(orig_words):
            orig_rich.append(word + " ", "bold red" if i in orig_error_indices else "")

        trans_error_indices = (
            result.trans_error_indices
            if hasattr(result, "trans_error_indices")
            else set()
        )
        trans_words = result.transcribed_words[:80]
        trans_rich = Text()
        for i, word in enumerate(trans_words):
            trans_rich.append(
                word + " ", "bold red" if i in trans_error_indices else ""
            )

        transcribed_count = len(transcribed.split()) if transcribed else 0

        mispronounced_words: list[tuple[str, str]] = []
        missing_in_middle: list[tuple[str, str]] = []

        if hasattr(result, "errors"):
            for orig_pos, orig_word, error_msg in result.errors:
                if error_msg != "(missing)":
                    mispronounced_words.append((orig_pos, orig_word))
                elif orig_pos < transcribed_count:
                    missing_in_middle.append((orig_pos, orig_word))

        mispronounced_words.sort(key=lambda x: x[0])
        missing_in_middle.sort(key=lambda x: x[0])

        mispronounced_text = Text()
        if mispronounced_words:
            mispronounced_text.append(
                f"\n  {get_text('mispronounced_words', lang)}:\n\n", style="bold red"
            )
            word_list = [w for _, w in mispronounced_words]
            phonetics = get_words_phonetics(word_list)
            for word, ipa in phonetics:
                if ipa:
                    mispronounced_text.append(f"  {word}  →  /{ipa}/\n", style="red")
                else:
                    mispronounced_text.append(
                        f"  {word}  →  (IPA not found)\n", style="dim"
                    )

        missing_text = Text()
        if missing_in_middle:
            missing_text.append(
                f"\n  {get_text('missing_words', lang)}:\n\n", style="bold yellow"
            )
            word_list = [w for _, w in missing_in_middle]
            phonetics = get_words_phonetics(word_list)
            for word, ipa in phonetics:
                if ipa:
                    missing_text.append(f"  {word}  →  /{ipa}/\n", style="yellow")
                else:
                    missing_text.append(f"  {word}  →  (IPA not found)\n", style="dim")

        sep = Text("  " + "─" * 50, style="dim")
        accuracy_line = Text()
        accuracy_line.append(
            f"  {get_text('accuracy', lang)}: {accuracy_pct:.1f}%"
            f" ({result.correct_count}/{result.total_count} {get_text('words_correct', lang)})",
            style=accuracy_color,
        )

        content = Group(
            Text(f"\n  {get_text('comparison_original', lang)}:", style="bold"),
            Text(""),
            orig_rich,
            Text(""),
            Text(f"  {get_text('comparison_yours', lang)}:", style="bold"),
            Text(""),
            trans_rich,
            Text(""),
            sep,
            Text(""),
            accuracy_line,
            mispronounced_text,
            missing_text,
        )

        self.console.print()
        self.console.print(
            self._create_panel(
                content,
                title=get_text("comparison_title", lang),
                border_style=accuracy_color,
            )
        )

    def show_practice_actions(self) -> str:
        """Show practice session action prompts.

        Returns:
            User's choice: 'r' for retry, 'n' for new lesson, 's' for stop
        """
        lang = self.config.ui_language
        self.console.print(
            f"\n[dim][R] {get_text('try_again', lang)} | "
            f"[N] {get_text('new_lesson', lang)} | "
            f"[S] {get_text('action_exit', lang)}[/dim]"
        )
        try:
            action = self.console.input(
                f"[bold {ACCENT}]{get_text('continue_prompt', lang)}:[/bold {ACCENT}] "
            )
            return action.strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "s"

    def show_lessons_loading(self) -> None:
        """Show loading message for lessons."""
        lang = self.config.ui_language
        self.console.print()
        self.console.print(f"[{ACCENT}]{get_text('lessons_loading', lang)}[/{ACCENT}]")

    def show_paragraph_page(
        self,
        text: str,
        level: str = "3",
        start_paragraph: int = 1,
        end_paragraph: int = 1,
        total_paragraphs: int = 1,
        estimated_duration: int = 30,
        current_duration: int = 30,
    ) -> str:
        """Show a page with 1-2 paragraphs with navigation.

        Args:
            text: Combined paragraph text to display
            level: Selected level
            start_paragraph: Starting paragraph number (1-indexed)
            end_paragraph: Ending paragraph number
            total_paragraphs: Total number of paragraphs
            estimated_duration: Estimated reading time in seconds
            current_duration: Current recording duration setting

        Returns:
            User action: 'record', 'next', 'prev', 'duration', 'main_menu', 'back'
        """
        lang = self.config.ui_language

        min_label = get_text("minutes_short", lang)
        sec_label = get_text("seconds_short", lang)

        if estimated_duration >= 60:
            mins = estimated_duration // 60
            secs = estimated_duration % 60
            time_str = (
                f"{mins}:{secs:02d} {min_label}" if secs else f"{mins} {min_label}"
            )
        else:
            time_str = f"{estimated_duration} {sec_label}"

        if start_paragraph == end_paragraph:
            para_label = f"{get_text('paragraph', lang)} {start_paragraph}"
        else:
            para_label = (
                f"{get_text('paragraphs', lang)} {start_paragraph}-{end_paragraph}"
            )

        meta = (
            f"[dim]{para_label} {get_text('of', lang)} {total_paragraphs}"
            f" | {get_text('estimated_time', lang)}: {time_str}"
            f" | {get_text('record_duration', lang)}: {current_duration}s[/dim]"
        )

        content = (
            f"\n  {meta}\n\n"
            f"  [dim]{get_text('read_aloud', lang)}[/dim]\n\n"
            + "\n".join(f"  {line}" for line in text.split("\n")[:20] if line.strip())
            + "\n"
        )

        self.console.print()
        self.console.print(
            self._create_panel(
                content,
                title=f"{get_text('reading_mode', lang)} — {get_text('level', lang)} {level}",
            )
        )

        nav_parts = []
        if end_paragraph < total_paragraphs:
            nav_parts.append(f"[N] {get_text('next_paragraph', lang)}")
        nav_parts.append(f"[D] {get_text('change_duration', lang)}")
        nav_parts.append(f"[R] {get_text('start_recording', lang)}")
        if start_paragraph > 1:
            nav_parts.append(f"[P] {get_text('prev_paragraph', lang)}")
        nav_parts.append(f"[M] {get_text('main_menu', lang)}")
        nav_parts.append(f"[B] {get_text('menu_back', lang)}")

        self.console.print(f"\n[dim]{' | '.join(nav_parts)}[/dim]")

        try:
            choice = self.console.input(
                f"\n[bold {ACCENT}]{get_text('option', lang)}:[/bold {ACCENT}] "
            )
            choice = choice.strip().lower()

            if choice == "r":
                return "record"
            elif choice == "n" and end_paragraph < total_paragraphs:
                return "next"
            elif choice == "p" and start_paragraph > 1:
                return "prev"
            elif choice == "d":
                return "duration"
            elif choice == "m":
                return "main_menu"
            elif choice == "b":
                return "back"
            else:
                return "record"
        except (EOFError, KeyboardInterrupt):
            return "back"

    def show_paragraph_actions(self) -> None:
        """Show actions after recording a paragraph (not the last one)."""
        lang = self.config.ui_language
        self.console.print(
            f"\n[dim][R] {get_text('try_again', lang)} | "
            f"[N] {get_text('next_paragraph', lang)} | "
            f"[S] {get_text('action_exit', lang)}[/dim]"
        )

    def show_last_paragraph_actions(self) -> None:
        """Show actions after recording the last paragraph."""
        lang = self.config.ui_language
        self.console.print(
            f"\n[dim][R] {get_text('try_again', lang)} | "
            f"[N] {get_text('new_lesson', lang)} | "
            f"[S] {get_text('action_exit', lang)}[/dim]"
        )

    def show_lesson_complete(self) -> None:
        """Show message when all paragraphs are completed."""
        lang = self.config.ui_language
        content = f"\n  [bold green]{get_text('lesson_complete', lang)}[/bold green]\n"
        self.console.print()
        self.console.print(self._create_panel(content, border_style="green"))
