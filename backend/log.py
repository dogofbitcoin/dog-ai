"""Project logger.

Single named logger so every module emits to the same handler. Backend stdout
under uvicorn, or journalctl under systemd. No file handler in v0.1.
"""

from __future__ import annotations

import logging
import os
import sys

_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

_handler = logging.StreamHandler(stream=sys.stdout)
_handler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
)

log = logging.getLogger("dob")
log.setLevel(_LEVEL)
log.addHandler(_handler)
log.propagate = False
