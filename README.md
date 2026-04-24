# YouTube Plugin for Daydream Scope

Adds a `youtube` input source mode to Scope source nodes. Paste a YouTube URL and it plays the video on loop as a regular video input.

- **url**: any `youtube.com` or `youtu.be` URL (watch, shorts, or embed form).
- **cache**: the video is downloaded once via `yt-dlp` into Scope's asset cache (`<scope-home>/cache/youtube/<video-id>.mp4`) and reused on subsequent connects.
- **playback**: decoding and looping are handled by Scope's built-in video-file input source.

Only `youtube.com` and `youtu.be` hosts are accepted. Requires `yt-dlp` and `av` to be importable.

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
