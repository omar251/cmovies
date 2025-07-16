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

def handle_error(message: str, e: Optional[Exception] = None, quiet: bool = False) -> None:
    """Log and print an error message."""
    logging.error(f"{message}: {e}" if e else message)
    if not quiet:
        print(f"Error: {message}", file=sys.stderr)

def get_imdb_id(args: argparse.Namespace) -> Optional[str]:
    """Determine the IMDb ID from command-line arguments."""
    if args.search:
        if not args.quiet:
            print("Starting interactive movie search...")
        try:
            return interactive_movie_search()
        except MovieSearchError as e:
            handle_error("Movie search failed", e, args.quiet)
            return None
        except KeyboardInterrupt:
            print("\nSearch cancelled by user.", file=sys.stderr)
            return None
    
    if args.imdb_id:
        if not validate_imdb_id(args.imdb_id):
            handle_error(f"Invalid IMDb ID format: {args.imdb_id}", quiet=args.quiet)
            return None
        return clean_imdb_id(args.imdb_id)
        
    if args.url:
        if "vidsrc.xyz/embed/movie/" in args.url:
            try:
                url_imdb_id = args.url.split("/")[-1]
                if not validate_imdb_id(url_imdb_id):
                    handle_error(f"Could not extract valid IMDb ID from URL: {args.url}", quiet=args.quiet)
                    return None
                return clean_imdb_id(url_imdb_id)
            except Exception:
                handle_error(f"Could not parse IMDb ID from URL: {args.url}", quiet=args.quiet)
                return None
        else:
            handle_error("Direct URL extraction not yet implemented for non-vidsrc URLs", quiet=args.quiet)
            return None
            
    return None

def extract_and_output_url(imdb_id: str, headless: bool, output_file: Optional[str], quiet: bool) -> bool:
    """Extract M3U8 URL and handle output."""
    try:
        if not quiet:
            print("Starting M3U8 URL extraction...")
        
        m3u8_url = extract_m3u8_url(imdb_id, headless=headless)
        
        if not m3u8_url:
            handle_error("Failed to extract M3U8 URL", quiet=quiet)
            return False
            
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(m3u8_url + '\n')
                if not quiet:
                    print(f"M3U8 URL saved to: {output_file}")
            except IOError as e:
                handle_error(f"Error saving to file: {e}", quiet=quiet)
                return False
        
        if not (quiet and output_file):
            print(m3u8_url)
            
        return True
        
    except URLExtractionError as e:
        handle_error("URL extraction failed", e, quiet)
        return False
    except Exception as e:
        handle_error("An unexpected error occurred", e, quiet)
        return False

def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    log_level = "ERROR" if args.quiet else "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)
    
    try:
        imdb_id = get_imdb_id(args)
        
        if not imdb_id:
            if not args.quiet:
                print("Could not determine IMDb ID. Exiting.", file=sys.stderr)
            return 1
            
        success = extract_and_output_url(
            imdb_id=imdb_id,
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
        handle_error("An unexpected error occurred in main", e, args.quiet)
        return 1

if __name__ == "__main__":
    sys.exit(main())