"""Константы для suspicion detection."""

# Веса для scoring
SCORE_WEBGL = 40        # WebGL vendor+renderer — очень стабильный
SCORE_SCREEN = 25       # Screen resolution — стабильный
SCORE_PLATFORM = 20     # Platform + cores — стабильный
SCORE_CANVAS = 15       # Canvas — может меняться
SCORE_IP = 30           # IP match
SCORE_UA_BROWSER = 15   # User-Agent browser match
SCORE_UA_OS = 10        # User-Agent OS match
SCORE_TIMING = 50       # Timing correlation (очень сильный сигнал)

# Thresholds
THRESHOLD_PROBABLE = 50
THRESHOLD_HIGH = 70

# Timing window для correlation (минуты)
TIMING_WINDOW_MINUTES = 5
