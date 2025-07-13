"""
cmovies - M3U8 URL Extractor for vidsrc.xyz

A Python package for extracting M3U8 video stream URLs from vidsrc.xyz embed pages.
"""

__version__ = "0.1.0"
__author__ = "cmovies"
__description__ = "extract the M3U8 video stream URL from a movie website"

from .movie_search import MovieSearcher, interactive_movie_search
from .url_extractor import M3U8Extractor, extract_m3u8_url
from .utils import validate_imdb_id, clean_imdb_id, validate_url

__all__ = [
    "MovieSearcher",
    "interactive_movie_search", 
    "M3U8Extractor",
    "extract_m3u8_url",
    "validate_imdb_id",
    "clean_imdb_id",
    "validate_url",
]