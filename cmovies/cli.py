#!/usr/bin/env python3
"""
Unified CLI interface for the cmovies application.

This script provides a command-line interface that integrates movie search
and M3U8 URL extraction functionality.
"""

import argparse
import sys
import logging
from typing import Optional

from .utils import setup_logging, validate_imdb_id, clean_imdb_id
from .movie_search import interactive_movie_search, MovieSearchError
from .url_extractor import extract_m3u8_url, URLExtractionError

def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Extract M3U8 video stream URLs from vidsrc.xyz",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --search                    # Interactive movie search
  %(prog)s --imdb-id tt1234567         # Direct IMDb ID input
  %(prog)s --imdb-id 1234567 --no-headless  # Show browser window
  %(prog)s --url "https://vidsrc.xyz/embed/movie/1234567"  # Direct URL
        """
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--search", "-s",
        action="store_true",
        help="Interactive movie search using IMDb"
    )
    input_group.add_argument(
        "--imdb-id", "-i",
        type=str,
        help="IMDb ID (with or without 'tt' prefix)"
    )
    input_group.add_argument(
        "--url", "-u",
        type=str,
        help="Direct vidsrc.xyz embed URL"
    )
    
    # Browser options
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Show browser window (useful for debugging)"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Save M3U8 URL to file"
    )
    
    # Logging options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all output except the M3U8 URL"
    )
    
    return parser

def handle_movie_search() -> Optional[str]:
    """
    Handle interactive movie search workflow.
    
    Returns:
        IMDb ID if movie selected, None otherwise
    """
    try:
        return interactive_movie_search()
    except MovieSearchError as e:
        logging.error(f"Movie search failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return None
    except KeyboardInterrupt:
        print("\nSearch cancelled by user.", file=sys.stderr)
        return None

def handle_imdb_id_input(imdb_id: str) -> Optional[str]:
    """
    Handle direct IMDb ID input.
    
    Args:
        imdb_id: The provided IMDb ID
        
    Returns:
        Cleaned IMDb ID if valid, None otherwise
    """
    if not validate_imdb_id(imdb_id):
        print(f"Error: Invalid IMDb ID format: {imdb_id}", file=sys.stderr)
        print("IMDb IDs should be 7-8 digits, optionally prefixed with 'tt'", file=sys.stderr)
        return None
    
    return clean_imdb_id(imdb_id)

def extract_and_output_url(imdb_id: str = None, url: str = None, headless: bool = True, 
                          output_file: str = None, quiet: bool = False) -> bool:
    """
    Extract M3U8 URL and handle output.
    
    Args:
        imdb_id: IMDb ID to use for extraction
        url: Direct URL to use for extraction
        headless: Whether to run browser in headless mode
        output_file: File to save URL to
        quiet: Whether to suppress non-essential output
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not quiet:
            print("Starting M3U8 URL extraction...")
        
        # Extract the URL
        if imdb_id:
            m3u8_url = extract_m3u8_url(imdb_id, headless=headless)
        else:
            # For direct URL extraction, we'd need to modify the extractor
            # For now, this is a placeholder
            print("Error: Direct URL extraction not yet implemented", file=sys.stderr)
            return False
        
        if not m3u8_url:
            if not quiet:
                print("Failed to extract M3U8 URL", file=sys.stderr)
            return False
        
        # Output the URL
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(m3u8_url + '\n')
                if not quiet:
                    print(f"M3U8 URL saved to: {output_file}")
            except IOError as e:
                print(f"Error saving to file: {e}", file=sys.stderr)
                return False
        
        # Always print the URL (unless quiet mode and saved to file)
        if not (quiet and output_file):
            print(m3u8_url)
        
        return True
        
    except URLExtractionError as e:
        logging.error(f"URL extraction failed: {e}")
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        if not quiet:
            print(f"Unexpected error: {e}", file=sys.stderr)
        return False

def main() -> int:
    """
    Main CLI entry point.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # Set up logging
    if args.quiet:
        log_level = "ERROR"
    elif args.verbose:
        log_level = "DEBUG"
    else:
        log_level = "INFO"
    
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Determine the IMDb ID or URL to use
        imdb_id = None
        url = None
        
        if args.search:
            if not args.quiet:
                print("Starting interactive movie search...")
            imdb_id = handle_movie_search()
            if not imdb_id:
                if not args.quiet:
                    print("No movie selected. Exiting.")
                return 1
        elif args.imdb_id:
            imdb_id = handle_imdb_id_input(args.imdb_id)
            if not imdb_id:
                return 1
            # Ensure we have the 'tt' prefix for consistency
            imdb_id = clean_imdb_id(imdb_id)
        elif args.url:
            url = args.url
            # For now, we'll extract IMDb ID from the URL if it's a vidsrc.xyz URL
            if "vidsrc.xyz/embed/movie/" in url:
                try:
                    # Extract the digits from the URL
                    url_imdb_id = url.split("/")[-1]
                    if not validate_imdb_id(url_imdb_id):
                        print(f"Error: Could not extract valid IMDb ID from URL: {url}", file=sys.stderr)
                        return 1
                    # Clean and ensure 'tt' prefix
                    imdb_id = clean_imdb_id(url_imdb_id)
                except Exception:
                    print(f"Error: Could not parse IMDb ID from URL: {url}", file=sys.stderr)
                    return 1
            else:
                print("Error: Direct URL extraction not yet implemented for non-vidsrc URLs", file=sys.stderr)
                return 1
        
        # Extract and output the M3U8 URL
        success = extract_and_output_url(
            imdb_id=imdb_id,
            url=url,
            headless=not args.no_headless,
            output_file=args.output,
            quiet=args.quiet
        )
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        if not args.quiet:
            print("\nOperation cancelled by user.", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        if not args.quiet:
            print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())