"""Plugin class wiring YouTubeInputSource into the Scope node registry."""

import logging

from scope.core.plugins import hookimpl

from .source import YouTubeInputSource

logger = logging.getLogger(__name__)


class YouTubePlugin:
    """Registers the YouTube input source."""

    @hookimpl
    def register_nodes(self, register):
        register(YouTubeInputSource)
        logger.info("Registered YouTube input source")
