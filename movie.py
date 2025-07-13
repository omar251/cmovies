from imdb import IMDb

# Create an instance of the IMDb class
ia = IMDb()
movie = input("Enter movie title: ")
# Search for a movie
movies = ia.search_movie(movie)

# Print the search results
for movie in movies:
    print(f"Title: {movie['title']}, Year: {movie.get('year')}, IMDb ID: {movie.movieID}")

# If you want to get the first result
if movies:
    first_movie = movies[0]
    print(f"First result - Title: {first_movie['title']}, Year: {first_movie.get('year')}, IMDb ID: {first_movie.movieID}")
