"""Constants for voice-to-text application."""

# Display limits for text truncation
TITLE_MAX_LENGTH = 50
TITLE_SHORT_LENGTH = 30
TITLE_SUBTITLE_LENGTH = 60

# Lesson/pagination limits
LESSON_DISPLAY_COUNT = 10
LESSON_FETCH_COUNT = 6
LESSONS_PER_PAGE = 5
PARAGRAPHS_PER_PAGE = 2

# Text display limits
TEXT_BLOCK_MAX_COUNT = 8
WORD_DISPLAY_LIMIT = 80
TEXT_LINES_PREVIEW = 20
LESSON_TEXT_LINES_PREVIEW = 15
MENU_ITEMS_PREVIEW = 8

# Recording
MIN_AUDIO_FILE_SIZE = 1000
TEST_RECORDING_DURATION = 2
DEFAULT_TEST_DURATION = 2

# Menu action codes (returned by UI methods)
MENU_REFRESH = -1
MENU_NEXT_PAGE = -2
MENU_PREV_PAGE = -3

# Audio level thresholds
LEVEL_HIGH = 0.7
LEVEL_MEDIUM = 0.4

# UI formatting
LEVEL_BAR_WIDTH = 20

# Reading speed (words per minute)
WORDS_PER_MINUTE = 150
WORDS_PER_PAGE_MIN = 100
WORDS_PER_PAGE_MAX = 150

# Minimum/maximum recording duration
MIN_DURATION = 1
MAX_DURATION = 300

# =============================================================================
# COLOR PALETTE
# =============================================================================
# Primary accent color - used for titles, prompts, and highlights
COLOR_ACCENT = "bright_blue"

# Semantic colors - have specific meaning
COLOR_SUCCESS = "green"      # Success messages, high accuracy (>=80%)
COLOR_WARNING = "yellow"     # Warning messages, medium accuracy (60-79%)
COLOR_ERROR = "red"          # Error messages, low accuracy (<60%), recording

# UI colors
COLOR_DIM = "dim"            # Secondary text, navigation hints
