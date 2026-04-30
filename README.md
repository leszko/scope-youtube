# YouTube Source

A [Daydream Scope](https://daydream.live) plugin that adds **YouTube** as an input source. Paste any YouTube URL into a Source node and Scope plays the video on loop as a regular video input — feed it into any pipeline that takes video.

The video is downloaded once via [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) into Scope's asset cache and reused on subsequent connects, so swapping back to a previously-used URL is instant.

## Features

- **Drop-in video input** — works anywhere a Source node does; no graph changes needed.
- **Local cache** — each video is downloaded once into `<scope-home>/cache/youtube/` and reused.
- **Looped playback** — frame decoding and looping are handled by Scope's built-in video-file source, so playback is identical to a local file.
- **Safe URL handling** — only `youtube.com` and `youtu.be` hosts are accepted (watch, shorts, and embed forms supported).
- **Concurrent-safe** — per-video locks prevent the same URL being downloaded twice in parallel.

## Installation

Install directly from GitHub in the Scope UI, or via the CLI:

```bash
uv run daydream-scope install https://github.com/leszko/scope-youtube
```

Restart Scope. **YouTube** then appears as a Source mode in the workflow builder.

## Usage

1. Install the plugin and restart Scope.
2. Add a **Source** node to your graph and pick **YouTube** as the source mode.
3. Paste a YouTube URL (e.g. `https://www.youtube.com/watch?v=dQw4w9WgXcQ`) into the URL field.
4. Wire the source's `video` output into any downstream pipeline or sink.

A ready-to-load example graph is in [`examples/youtube-passthrough.scope-workflow.json`](examples/youtube-passthrough.scope-workflow.json).

```
YouTube Source (url)  ─►  Pipeline / Sink
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| URL | string | A YouTube URL — `youtube.com/watch?v=...`, `youtu.be/...`, `/shorts/...`, or `/embed/...`. |

## Ports

| Port | Direction | Type | Description |
|------|-----------|------|-------------|
| `video` | output | video | Decoded RGB frames from the YouTube video, looped. |

## Cache

Videos are cached at `<scope-home>/cache/youtube/<video-id>.mp4` (default `<scope-home>` is `~/.daydream-scope`, override with the `DAYDREAM_SCOPE_HOME` env var). Delete a file from that directory to force a re-download on the next connect.

The default download format is `bv*[ext=mp4][height<=1080]+ba[ext=m4a]` — best mp4 video + m4a audio at ≤1080p, with sensible fallbacks.

## Requirements

- `yt-dlp` (installed automatically as a dependency)
- `av` (provided by Scope)
- `ffmpeg` — install via your system package manager

## Development

Clone and install locally for development:

```bash
git clone https://github.com/leszko/scope-youtube
uv run daydream-scope install -e ./scope-youtube
```

After editing the code, use the **Reload** button in the Scope Plugins settings tab.

## License

Apache-2.0 — see [LICENSE](LICENSE).
