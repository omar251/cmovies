"""Utility functions for input validation and common operations."""

import re
import logging
from typing import Optional

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)

def validate_imdb_id(imdb_id: str) -> bool:
    """
    Validate IMDb ID format.
    
    Args:
        imdb_id: The IMDb ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not imdb_id:
        return False
    
    # IMDb IDs are typically 7-8 digits, sometimes prefixed with 'tt'
    pattern = r'^(tt)?(\d{7,8})$'
    return bool(re.match(pattern, imdb_id.strip()))

def clean_imdb_id(imdb_id: str) -> str:
    """
    Clean and normalize IMDb ID.
    
    Args:
        imdb_id: The IMDb ID to clean
        
    Returns:
        Cleaned IMDb ID with 'tt' prefix
    """
    if not imdb_id:
        return ""
    
    # Remove any whitespace and convert to lowercase
    cleaned = imdb_id.strip().lower()
    
    # Remove 'tt' prefix if present to get just the digits
    if cleaned.startswith('tt'):
        digits = cleaned[2:]
    else:
        digits = cleaned
    
    # Return with 'tt' prefix
    return f"tt{digits}"

def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: The URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(url_pattern, url))

def format_movie_info(movie) -> str:
    """
    Format movie information for display.
    
    Args:
        movie: IMDb movie object
        
    Returns:
        Formatted movie information string
    """
    title = movie.get('title', 'N/A')
    year = movie.get('year', 'N/A')
    movie_id = movie.movieID
    
    # Add additional info if available
    kind = movie.get('kind', '')
    if kind and kind != 'movie':
        title += f" ({kind})"
    
    return f"Title: {title}, Year: {year}, IMDb ID: {movie_id}"

def extract_imdb_id_from_selection(selection: str) -> Optional[str]:
    """
    Extract IMDb ID from formatted movie selection string.
    
    Args:
        selection: The formatted movie selection string
        
    Returns:
        Extracted IMDb ID or None if not found
    """
    try:
        return selection.split("IMDb ID: ")[1].strip()
    except (IndexError, AttributeError):
        return None