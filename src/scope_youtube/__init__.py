"""YouTube input source plugin for Daydream Scope."""

from .plugin import YouTubePlugin

# Read by Scope to decide whether the plugin should run locally
# (source-kind) or in the cloud. Pre-install: AST-parsed from this
# file. Post-install: read from the imported module.
__scope_kind__ = "source"

plugin = YouTubePlugin()

__all__ = ["plugin", "YouTubePlugin", "__scope_kind__"]
