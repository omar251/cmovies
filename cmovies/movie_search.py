"""Movie search functionality using IMDb API."""

import logging
from typing import List, Optional, Tuple
from imdb import IMDb
from pyfzf.pyfzf import FzfPrompt

from .utils import format_movie_info, extract_imdb_id_from_selection
from .config import MAX_SEARCH_RESULTS

logger = logging.getLogger(__name__)

class MovieSearchError(Exception):
    """Custom exception for movie search errors."""
    pass

class MovieSearcher:
    """Handles movie searching and selection using IMDb."""
    
    def __init__(self):
        """Initialize the MovieSearcher."""
        try:
            self.imdb = IMDb()
            self.fzf = FzfPrompt()
            logger.info("MovieSearcher initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MovieSearcher: {e}")
            raise MovieSearchError(f"Failed to initialize movie search: {e}")
    
    def search_movies(self, query: str) -> List:
        """
        Search for movies using IMDb.
        
        Args:
            query: The search query
            
        Returns:
            List of movie objects
            
        Raises:
            MovieSearchError: If search fails
        """
        if not query or not query.strip():
            raise MovieSearchError("Search query cannot be empty")
        
        try:
            logger.info(f"Searching for movies with query: '{query}'")
            movies = self.imdb.search_movie(query)
            
            if not movies:
                raise MovieSearchError(f"No movies found for query: '{query}'")
            
            # Limit results to avoid overwhelming the user
            movies = movies[:MAX_SEARCH_RESULTS]
            logger.info(f"Found {len(movies)} movies")
            
            return movies
        except Exception as e:
            logger.error(f"Movie search failed: {e}")
            raise MovieSearchError(f"Failed to search for movies: {e}")
    
    def select_movie(self, movies: List) -> Optional[str]:
        """
        Allow user to select a movie from search results.
        
        Args:
            movies: List of movie objects from IMDb search
            
        Returns:
            Selected movie's IMDb ID or None if no selection
            
        Raises:
            MovieSearchError: If selection fails
        """
        try:
            # Prepare movie list for fzf
            movie_list = [format_movie_info(movie) for movie in movies]
            
            logger.info("Presenting movie selection to user")
            selected_movie_info = self.fzf.prompt(movie_list)
            
            if not selected_movie_info:
                logger.info("No movie selected by user")
                return None
            
            # Extract IMDb ID from selection
            movie_id = extract_imdb_id_from_selection(selected_movie_info[0])
            
            if not movie_id:
                raise MovieSearchError("Failed to extract movie ID from selection")
            
            logger.info(f"User selected movie with ID: {movie_id}")
            return movie_id
            
        except Exception as e:
            logger.error(f"Movie selection failed: {e}")
            raise MovieSearchError(f"Failed to select movie: {e}")
    
    def search_and_select(self, query: str) -> Optional[str]:
        """
        Combined search and selection workflow.
        
        Args:
            query: The search query
            
        Returns:
            Selected movie's IMDb ID or None if no selection
            
        Raises:
            MovieSearchError: If search or selection fails
        """
        movies = self.search_movies(query)
        return self.select_movie(movies)

def interactive_movie_search() -> Optional[str]:
    """
    Interactive movie search workflow.
    
    Returns:
        Selected movie's IMDb ID or None if cancelled
    """
    try:
        searcher = MovieSearcher()
        
        while True:
            query = input("Enter movie title (or 'quit' to exit): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                logger.info("User cancelled movie search")
                return None
            
            if not query:
                print("Please enter a valid movie title.")
                continue
            
            try:
                movie_id = searcher.search_and_select(query)
                if movie_id:
                    return movie_id
                else:
                    print("No movie selected. Try again or type 'quit' to exit.")
            except MovieSearchError as e:
                print(f"Search error: {e}")
                print("Please try again with a different search term.")
                
    except KeyboardInterrupt:
        logger.info("Movie search interrupted by user")
        print("\nSearch cancelled.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in movie search: {e}")
        print(f"An unexpected error occurred: {e}")
        return None