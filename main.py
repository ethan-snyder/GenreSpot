import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
import os
from dotenv import load_dotenv
from time import sleep

# This function is a bulk API reqesuest that asks for the genres for 50 artists in one go
def get_artists_genres(sp, artist_ids):
    genres = {}
    for i in range(0, len(artist_ids), 50):
        batch = artist_ids[i:i+50]
        max_retries = 5
        for attempt in range(max_retries):
            try:
                results = sp.artists(batch)
                for artist in results['artists']:
                    genres[artist['id']] = set(artist['genres'])
                break
            except SpotifyException as e:
                if e.http_status == 429:
                    retry_after = int(e.headers.get('Retry-After', 1))
                    print(f"Rate limited. Retrying after {retry_after} seconds.")
                    sleep(retry_after)
                else:
                    raise
    return genres

# Getting api and secret from .env and Authenticating
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

playlist_url = 'https://open.spotify.com/playlist/3z3ssAyKVkPBtThG44BcaX?si=5fc999cf17f246b0'
playlist_id = playlist_url.split('/')[-1].split('?')[0]


# Get all tracks from the playlist
results = sp.playlist_tracks(playlist_id)
tracks = results['items']

# Since the API call gets 100 songs at a time we need to keep sending requests until there isn't anything left
while results['next']:
    results = sp.next(results)
    tracks.extend(results['items'])
    track_count = len(tracks)


artist_ids = list(set(artist['id'] for track in tracks for artist in track['track']['artists']))
all_genres = get_artists_genres(sp, artist_ids)

#Asking user which genre they want to select from a playlist
print("Enter the genre you want to filter by: ")
selected_genre = input()

# Print all track names, artists, and genres on a song by song basis
for track in tracks:
    track_name = track['track']['name']
    artists = track['track']['artists']
    artist_names = ', '.join([artist['name'] for artist in artists])

    genres = set()
    for artist in artists:
        genres.update(all_genres.get(artist['id'], set()))

    genres_str = ', '.join(genres) if genres else 'No genre information'
    if selected_genre in genres_str.lower():
        # Writing results to a file
        with open('genreSortedSongs/filteredList.txt', 'a') as file:
            file.write(f"{track_name} by {artist_names} - Genres: {genres_str}\n")
        print(f"{track_name} by {artist_names} - Genres: {genres_str}")
