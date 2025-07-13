#!/usr/bin/env python3
"""
Example usage of the cmovies package.

This script demonstrates how to use the various components of the cmovies package
both individually and together.
"""

import asyncio
import logging
from typing import Optional

# Note: These imports will work once dependencies are installed
try:
    from cmovies.movie_search import MovieSearcher, MovieSearchError
    from cmovies.url_extractor import M3U8Extractor, URLExtractionError
    from cmovies.utils import validate_imdb_id, clean_imdb_id, setup_logging
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Dependencies not installed: {e}")
    print("Run 'uv sync' and 'playwright install chromium' to install dependencies")
    DEPENDENCIES_AVAILABLE = False
    # Fallback imports for basic functionality
    try:
        from cmovies.utils import validate_imdb_id, clean_imdb_id
        def setup_logging(level):
            import logging
            logging.basicConfig(level=getattr(logging, level.upper()))
    except ImportError:
        def validate_imdb_id(x): return True
        def clean_imdb_id(x): return x
        def setup_logging(x): pass

def example_movie_search():
    """Example of using the movie search functionality."""
    if not DEPENDENCIES_AVAILABLE:
        return
    
    print("=== Movie Search Example ===")
    
    try:
        searcher = MovieSearcher()
        
        # Search for movies
        query = "The Matrix"
        print(f"Searching for: {query}")
        movies = searcher.search_movies(query)
        
        print(f"Found {len(movies)} movies:")
        for i, movie in enumerate(movies[:5]):  # Show first 5
            title = movie.get('title', 'N/A')
            year = movie.get('year', 'N/A')
            movie_id = movie.movieID
            print(f"  {i+1}. {title} ({year}) - ID: {movie_id}")
        
        # For demo purposes, use the first movie
        if movies:
            selected_id = movies[0].movieID
            print(f"\nSelected movie ID: {selected_id}")
            return selected_id
            
    except MovieSearchError as e:
        print(f"Movie search error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return None

async def example_url_extraction(imdb_id: str):
    """Example of using the URL extraction functionality."""
    if not DEPENDENCIES_AVAILABLE:
        return
    
    print(f"\n=== URL Extraction Example ===")
    print(f"Extracting M3U8 URL for IMDb ID: {imdb_id}")
    
    try:
        extractor = M3U8Extractor(headless=True)
        
        # Build the URL
        url = extractor.build_url(imdb_id)
        print(f"Target URL: {url}")
        
        # Extract M3U8 URL (this would actually run the browser automation)
        print("Note: This would launch a browser and extract the M3U8 URL")
        print("For demo purposes, we're not actually running the extraction")
        
        # Uncomment the line below to actually run the extraction:
        # m3u8_url = await extractor.extract_from_imdb_id(imdb_id)
        # print(f"Extracted M3U8 URL: {m3u8_url}")
        
    except URLExtractionError as e:
        print(f"URL extraction error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def example_validation():
    """Example of using the validation utilities."""
    print("\n=== Validation Examples ===")
    
    # Test IMDb ID validation
    test_ids = ["tt1234567", "1234567", "invalid", "123", "tt12345678"]
    
    print("IMDb ID Validation (now returns with 'tt' prefix):")
    for test_id in test_ids:
        is_valid = validate_imdb_id(test_id)
        cleaned = clean_imdb_id(test_id) if is_valid else "N/A"
        print(f"  '{test_id}' -> Valid: {is_valid}, Cleaned: '{cleaned}'")

def example_cli_usage():
    """Example of CLI usage patterns."""
    print("\n=== CLI Usage Examples ===")
    
    examples = [
        "python cli.py --search",
        "python cli.py --imdb-id tt1234567",
        "python cli.py --imdb-id 1234567 --output movie.m3u8",
        "python cli.py --search --no-headless --verbose",
        "python cli.py --imdb-id tt1234567 --quiet"
    ]
    
    print("Command examples:")
    for example in examples:
        print(f"  {example}")

async def main():
    """Main example function."""
    # Set up logging
    setup_logging("INFO")
    
    print("cmovies Package Usage Examples")
    print("=" * 40)
    
    # Validation examples (always work)
    example_validation()
    
    # CLI usage examples
    example_cli_usage()
    
    if DEPENDENCIES_AVAILABLE:
        # Movie search example
        movie_id = example_movie_search()
        
        # URL extraction example (if we got a movie ID)
        if movie_id:
            await example_url_extraction(movie_id)
    else:
        print("\n=== Dependency Installation Required ===")
        print("To run the full examples, install dependencies:")
        print("1. uv sync")
        print("2. playwright install chromium")

if __name__ == "__main__":
    asyncio.run(main())