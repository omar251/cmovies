# cmovies - M3U8 URL Extractor for vidsrc.xyz

A Python application that extracts M3U8 video stream URLs from vidsrc.xyz embed pages using browser automation. The application provides both a unified CLI interface and modular Python APIs for movie search and URL extraction.

## Features

- **Interactive Movie Search**: Search and select movies using IMDb integration with fuzzy search
- **Direct IMDb ID Input**: Extract URLs directly using IMDb IDs
- **Robust Error Handling**: Comprehensive validation and error reporting
- **Configurable Browser**: Option to run in headless or visible mode
- **Flexible Output**: Save URLs to files or output to stdout
- **Modular Design**: Well-structured codebase with separate concerns

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd cmovies
```

2. Install dependencies:
```bash
uv sync
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

## Usage

### Command Line Interface

The application provides a unified CLI with multiple input methods:

#### Interactive Movie Search
```bash
python cli.py --search
```
This will prompt you to enter a movie title, search IMDb, and select from results using fuzzy search.

#### Direct IMDb ID
```bash
python cli.py --imdb-id tt1234567
# or without 'tt' prefix
python cli.py --imdb-id 1234567
```

#### Show Browser Window (for debugging)
```bash
python cli.py --imdb-id tt1234567 --no-headless
```

#### Save Output to File
```bash
python cli.py --search --output movie_url.txt
```

#### Quiet Mode (minimal output)
```bash
python cli.py --imdb-id tt1234567 --quiet
```

#### Verbose Logging
```bash
python cli.py --search --verbose
```

### Python API

You can also use the components programmatically:

```python
from movie_search import MovieSearcher
from url_extractor import extract_m3u8_url
from utils import validate_imdb_id

# Movie search
searcher = MovieSearcher()
movies = searcher.search_movies("The Matrix")
movie_id = searcher.select_movie(movies)

# URL extraction
if movie_id and validate_imdb_id(movie_id):
    m3u8_url = extract_m3u8_url(movie_id)
    print(f"M3U8 URL: {m3u8_url}")
```

## How It Works

The application automates the complex multi-step process required to extract video URLs from vidsrc.xyz:

1. **Initial Page Load**: Loads the vidsrc.xyz embed page containing an iframe with movie poster
2. **First Interaction**: Clicks the play button to trigger the next step
3. **Second Iframe**: Waits for the dynamic creation of the actual video player iframe
4. **Video Activation**: Interacts with the video player to start playback
5. **Network Monitoring**: Captures the M3U8 URL when the video player requests the stream
6. **URL Extraction**: Returns the final M3U8 video stream URL

## Project Structure

```
cmovies/
├── cli.py              # Unified command-line interface
├── movie_search.py     # IMDb movie search functionality
├── url_extractor.py    # M3U8 URL extraction using Playwright
├── utils.py           # Utility functions and validation
├── config.py          # Configuration constants
├── __init__.py        # Package initialization
├── main.py            # Legacy script (deprecated)
├── movie.py           # Legacy script (deprecated)
├── pyproject.toml     # Project configuration
└── README.md          # This file
```

## Configuration

Key settings can be modified in `config.py`:

- **Timeouts**: Navigation, element wait, and request timeouts
- **Selectors**: CSS selectors for page elements
- **URLs**: Base URLs and endpoints
- **Logging**: Log format and levels

## Error Handling

The application includes comprehensive error handling:

- **Input Validation**: Validates IMDb IDs and URLs before processing
- **Network Timeouts**: Configurable timeouts for all network operations
- **Browser Errors**: Handles browser automation failures gracefully
- **User Interruption**: Proper cleanup on Ctrl+C
- **Detailed Logging**: Configurable logging levels for debugging

## Troubleshooting

### Common Issues

1. **Playwright not installed**: Run `playwright install chromium`
2. **Timeout errors**: The website may be slow; try increasing timeouts in `config.py`
3. **Element not found**: The website structure may have changed; check selectors in `config.py`
4. **No M3U8 found**: The video may not be available or the site may be blocking automation

### Debug Mode

Run with `--no-headless` to see the browser window and debug issues:
```bash
python cli.py --imdb-id tt1234567 --no-headless --verbose
```

## Legal Notice

This tool is for educational purposes only. Users are responsible for ensuring their use complies with:
- Website terms of service
- Copyright laws
- Local regulations

The authors do not encourage or condone the use of this tool for accessing copyrighted content without proper authorization.

## Dependencies

- **playwright**: Browser automation
- **imdbpy**: IMDb movie database access
- **pyfzf**: Fuzzy search interface
- **requests**: HTTP requests (future use)

## Contributing

1. Follow the existing code structure and style
2. Add appropriate error handling and logging
3. Update tests and documentation
4. Ensure all imports and dependencies are properly managed

## License

[Add your license information here]