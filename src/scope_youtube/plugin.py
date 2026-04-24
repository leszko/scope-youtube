"""Plugin entry point for scope-youtube."""

from scope.core.plugins import hookimpl

from .source import YouTubeInputSource


@hookimpl
def register_nodes(register):
    register(YouTubeInputSource)
