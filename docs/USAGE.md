# Usage Guide

## Command Line Interface

### Interactive Movie Search
```bash
python run.py --search
```
This will prompt you to enter a movie title, search IMDb, and select from results using fuzzy search.

### Direct IMDb ID
```bash
python run.py --imdb-id tt1234567
# or without 'tt' prefix
python run.py --imdb-id 1234567
```

### Show Browser Window (for debugging)
```bash
python run.py --imdb-id tt1234567 --show-browser
```

### Save Output to File
```bash
python run.py --search --output movie_url.txt
```

### Quiet Mode (minimal output)
```bash
python run.py --imdb-id tt1234567 --quiet
```

### Verbose Logging
```bash
python run.py --search --verbose
```

## Python API

You can also use the components programmatically:

```python
from cmovies import MovieSearcher, extract_m3u8_url, validate_imdb_id

# Movie search
searcher = MovieSearcher()
movies = searcher.search_movies("The Matrix")
movie_id = searcher.select_movie(movies)

# URL extraction
if movie_id and validate_imdb_id(movie_id):
    m3u8_url = extract_m3u8_url(movie_id)
    print(f"M3U8 URL: {m3u8_url}")
```

## Configuration

Key settings can be modified in `cmovies/config.py`:

- **Timeouts**: Navigation, element wait, and request timeouts
- **Selectors**: CSS selectors for page elements
- **URLs**: Base URLs and endpoints
- **Logging**: Log format and levels

## Troubleshooting

### Common Issues

1. **Dependencies not installed**: Run `uv sync && playwright install chromium`
2. **Timeout errors**: The website may be slow; try increasing timeouts in config
3. **Element not found**: The website structure may have changed; check selectors
4. **No M3U8 found**: The video may not be available or the site may be blocking automation

### Debug Mode

Run with `--show-browser` to see the browser window and debug issues:
```bash
python run.py --imdb-id tt1234567 --show-browser --verbose
```