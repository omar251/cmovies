from imdb import IMDb
from pyfzf.pyfzf import FzfPrompt

# Create an instance of the IMDb class
ia = IMDb()

# Search for a movie
query = input("Enter movie title: ")
movies = ia.search_movie(query)

# Prepare the data for fzf
movie_list = []
for movie in movies:
    movie_info = f"Title: {movie.get('title', 'N/A')}, Year: {movie.get('year', 'N/A')}, IMDb ID: {movie.movieID}"
    movie_list.append(movie_info)

# Use FzfPrompt to select a movie
fzf = FzfPrompt()
selected_movie_info = fzf.prompt(movie_list)

if selected_movie_info:
    selected_movie = selected_movie_info[0]
    movie_id = selected_movie.split("IMDb ID: ")[1]
    print(f"Selected Movie ID: {movie_id}")
else:
    print("No movie selected.")
