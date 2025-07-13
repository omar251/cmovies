# cmovies - M3U8 URL Extractor for vidsrc.xyz

A Python application that extracts M3U8 video stream URLs from vidsrc.xyz embed pages using browser automation. The application provides both a unified CLI interface and modular Python APIs for movie search and URL extraction.

## Features

- **Interactive Movie Search**: Search and select movies using IMDb integration with fuzzy search
- **Direct IMDb ID Input**: Extract URLs directly using IMDb IDs
- **Robust Error Handling**: Comprehensive validation and error reporting
- **Configurable Browser**: Option to run in headless or visible mode
- **Flexible Output**: Save URLs to files or output to stdout
- **Modular Design**: Well-structured codebase with separate concerns

## Quick Start

1. **Install dependencies**:
   ```bash
   uv sync
   playwright install chromium
   ```

2. **Run interactive search**:
   ```bash
   python run.py --search
   ```

3. **Or use direct IMDb ID**:
   ```bash
   python run.py --imdb-id tt0133093
   ```

## How It Works

The application automates the complex multi-step process required to extract video URLs from vidsrc.xyz:

1. **Initial Page Load**: Loads the vidsrc.xyz embed page containing an iframe with movie poster
2. **First Interaction**: Clicks the play button to trigger the next step
3. **Second Iframe**: Waits for the dynamic creation of the actual video player iframe
4. **Video Activation**: Interacts with the video player to start playback
5. **Network Monitoring**: Captures the M3U8 URL when the video player requests the stream
6. **URL Extraction**: Returns the final M3U8 video stream URL
