import logging
from pathlib import Path
from datetime import datetime

# --------------------------------------------------
# Create logs directory if it doesn't exist
# --------------------------------------------------

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# --------------------------------------------------
# Daily log file
# --------------------------------------------------

LOG_FILE = LOG_DIR / f"pipeline_{datetime.now().strftime('%Y-%m-%d')}.log"

# --------------------------------------------------
# Logger
# --------------------------------------------------

logger = logging.getLogger("livehooah")

if not logger.handlers:

    # ==================================================
    # CHANGE 1
    # Show DEBUG, INFO, WARNING, ERROR and CRITICAL
    # ==================================================
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # ==================================================
    # File logging
    # ==================================================

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # ==================================================
    # Console logging
    # ==================================================

    console_handler = logging.StreamHandler()

    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # ==================================================
    # Attach handlers
    # ==================================================

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # ==================================================
    # Prevent duplicate logging
    # ==================================================

    logger.propagate = False