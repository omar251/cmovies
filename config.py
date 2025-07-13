# Configuration constants for the cmovies application

# Timeout settings (in milliseconds)
NAVIGATION_TIMEOUT = 45000
ELEMENT_WAIT_TIMEOUT = 20000
CLICK_TIMEOUT = 10000
M3U8_REQUEST_TIMEOUT = 60000

# Selectors
INITIAL_IFRAME_SELECTOR = "iframe"
PLAY_BUTTON_SELECTOR = "#pl_but_background"
PLAYER_IFRAME_SELECTOR = 'iframe[id="player_iframe"]'

# URLs
VIDSRC_BASE_URL = "https://vidsrc.xyz/embed/movie/"

# Logging
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# Movie search settings
MAX_SEARCH_RESULTS = 50