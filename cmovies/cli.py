#!/usr/bin/env python3
"""
Unified CLI interface for the cmovies application.

This script provides a command-line interface that integrates movie search
and M3U8 URL extraction functionality.
"""

import argparse
import sys
import logging
import subprocess
import importlib.resources
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
  %(prog)s "The Matrix"            # Default: search, play with lowest quality
  %(prog)s --search                # Interactive movie search
  %(prog)s --search "Inception"    # Quiet search for "Inception"
  %(prog)s --imdb-id tt1234567     # Direct IMDb ID input
  %(prog)s --imdb-id 1234567 --show-browser  # Show browser window
  %(prog)s --url "https://vidsrc.xyz/embed/movie/1234567"  # Direct URL
        """
    )

    # Positional argument for default mode
    parser.add_argument(
        "movie_title",
        nargs="?",  # 0 or 1 argument
        type=str,
        help="Movie title for default mode: search, play with lowest quality, quiet output"
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group() # Removed required=True
    input_group.add_argument(
        "--search", "-s",
        nargs="?",  # Makes the argument optional
        const="",   # Value if argument is present but no value given
        type=str,
        help="Interactive movie search using IMDb. Provide a query for silent mode."
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
        "--show-browser",
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
    
    # ytdl-plus integration
    ytdl_plus_group = parser.add_argument_group(
        "ytdl-plus integration",
        "Options to play, stream, or download the extracted URL using ytdl-plus.sh"
    )
    ytdl_plus_group.add_argument(
        "--play",
        action="store_true",
        help="Play the video with a media player (e.g., mpv, vlc)"
    )
    ytdl_plus_group.add_argument(
        "--stream",
        action="store_true",
        help="Stream the video directly to the player without saving"
    )
    ytdl_plus_group.add_argument(
        "--download",
        action="store_true",
        help="Download the video using yt-dlp"
    )
    ytdl_plus_group.add_argument(
        "--record",
        action="store_true",
        help="Record the video stream using mpv's built-in recorder"
    )
    ytdl_plus_group.add_argument(
        "--player",
        type=str,
        default="mpv",
        help="Player to use (mpv, vlc, etc.) [default: mpv]"
    )
    ytdl_plus_group.add_argument(
        "--ytdlp-format",
        type=str,
        help="yt-dlp format code (e.g., 'best', '136+140')"
    )
    
    return parser

def handle_error(message: str, e: Optional[Exception] = None, quiet: bool = False) -> None:
    """Log and print an error message."""
    logging.error(f"{message}: {e}" if e else message)
    if not quiet:
        print(f"Error: {message}", file=sys.stderr)

def get_imdb_id(args: argparse.Namespace) -> Optional[str]:
    """Determine the IMDb ID from command-line arguments."""
    if args.search is not None:
        query = args.search
        if not query and not args.quiet:
            # Interactive mode: prompt for query
            imdb_id = interactive_movie_search(silent_mode=args.quiet)
        elif not query and args.quiet:
            # Quiet mode without query: error
            handle_error("Search query required for quiet mode (--search with --quiet)", quiet=args.quiet)
            return None
        else:
            # Quiet mode with query: pass query directly
            imdb_id = interactive_movie_search(silent_mode=args.quiet, search_query=query)
        return imdb_id
    
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

def handle_ytdl_plus(m3u3_url: str, movie_title: str, args: argparse.Namespace) -> bool:
    """Handle the ytdl-plus.sh script execution."""
    
    # Get the path to ytdl-plus.sh from the installed package
    ytdl_plus_script_path = str(importlib.resources.files('cmovies').joinpath('ytdl-plus.sh'))
    command = [ytdl_plus_script_path]
    
    if args.stream:
        command.append("--stream")
    elif args.play:
        command.append("--play")
        command.extend(["-o", f"cmovies-{movie_title}"])
    elif args.download:
        # ytdl-plus.sh default behavior is to download
        command.extend(["-o", f"cmovies-{movie_title}"])
    elif args.record:
        command.append("--record")
        command.extend(["-o", f"cmovies-{movie_title}"])

    # Pass --quiet flag to ytdl-plus.sh
    if args.quiet:
        command.append("--quiet")
        
    if args.player:
        command.extend(["--player", args.player])
        
    # Handle format selection clearly
    if args.ytdlp_format:
        command.extend(["--format", args.ytdlp_format])
    elif args.quiet:
        # In quiet mode, default to lowest quality for faster processing
        command.extend(["--format", "worst"])
    # If neither specified, let ytdl-plus.sh handle format selection
        
    command.append(m3u3_url)
    
    if not args.quiet:
        print(f"Executing ytdl-plus.sh command: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
        return True
    except FileNotFoundError:
        handle_error("ytdl-plus.sh not found. Make sure it's in the installed package.", quiet=args.quiet)
        return False
    except subprocess.CalledProcessError as e:
        handle_error(f"ytdl-plus.sh failed with exit code {e.returncode}", quiet=args.quiet)
        return False
    except Exception as e:
        handle_error(f"Unexpected error running ytdl-plus.sh: {e}", quiet=args.quiet)
        return False

def extract_and_output_url(imdb_id: str, headless: bool, output_file: Optional[str], quiet: bool, args: argparse.Namespace) -> bool:
    """Extract M3U8 URL and handle output."""
    try:
        if not quiet:
            print("Starting M3U8 URL extraction...")
        
        extraction_result = extract_m3u8_url(imdb_id, headless=headless)
        
        if not extraction_result:
            handle_error("Failed to extract M3U8 URL", quiet=quiet)
            return False
            
        m3u3_url, movie_title = extraction_result
        
        if args.play or args.stream or args.download or args.record:
            return handle_ytdl_plus(m3u3_url, movie_title, args)
            
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(m3u3_url + '\n')
                if not quiet:
                    print(f"M3U8 URL saved to: {output_file}")
            except IOError as e:
                handle_error(f"Error saving to file: {e}", quiet=quiet)
                return False
        
        if not (quiet and output_file):
            print(m3u3_url)
            
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


    # Handle default mode (positional argument)
    if args.movie_title:
        if any([args.search is not None, args.imdb_id, args.url]):
            handle_error("Cannot use movie title with --search, --imdb-id, or --url", quiet=False)
            return 1
        
        # Validate movie title
        if not args.movie_title.strip():
            handle_error("Movie title cannot be empty", quiet=False)
            return 1
        
        # Make default mode behavior explicit
        if not args.quiet:
            print(f"Default mode: searching '{args.movie_title}', playing with lowest quality")
        
        args.search = args.movie_title
        args.play = True
        args.quiet = True
    
    # Ensure at least one input method is provided if not in default mode
    if not any([args.search is not None, args.imdb_id, args.url]):
        handle_error("No input method provided. Use --search, --imdb-id, --url, or a movie title.", quiet=False)
        parser.print_help()
        return 1

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
            headless=not args.show_browser,
            output_file=args.output,
            quiet=args.quiet,
            args=args
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