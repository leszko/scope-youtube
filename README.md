# scope-youtube

Scope plugin that adds a `youtube` input source mode to source nodes.

Downloads a YouTube video via `yt-dlp` to a per-video cache, then reuses
the built-in video-file decoder to play it back on loop.

## Install

```bash
uv pip install -e /path/to/scope-youtube
```

Restart Scope. The `youtube` source mode is then accepted by source nodes.

## Usage in a graph

```json
{
  "id": "input",
  "type": "source",
  "source_mode": "youtube",
  "source_name": "https://www.youtube.com/watch?v=<video-id>"
}
```
