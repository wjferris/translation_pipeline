"""Opt-in process titles for demo-launched BabelFish workers."""

from __future__ import annotations

import os

from setproctitle import setproctitle


PROCESS_TITLE_ENV = "BABELFISH_PROCESS_TITLE"


def set_demo_process_title(title: str | None = None) -> str | None:
    """Set an explicitly requested demo-only process title, if configured.

    Standalone CLI workers do not set :data:`PROCESS_TITLE_ENV`, so their
    existing operating-system process identity remains unchanged.
    """
    title = title or os.environ.get(PROCESS_TITLE_ENV)
    if not title:
        return None
    setproctitle(title)
    return title
