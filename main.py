import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from spotipy.exceptions import SpotifyException
import os
from dotenv import load_dotenv
from time import sleep
from collections import Counter
import itertools

# Getting api and secret from .env and Authenticating
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://127.0.0.1:8888/callback")
client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

scope = "user-library-read playlist-modify-public"
try:
    sp2 = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=scope
    ))
except Exception as e:
    print(f"Authentication Error: {e}")
    exit()

# Get authenticated user's ID
user_info = sp2.me()
auth_user_id = user_info['id']

# get_artists_genres is a bulk API request that asks for the genres for 50 artists in one go
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

# Asking user which playlist they want filtered
print("\u001b[38;5;87mEnter the playlist you want to filter: \u001b[0m")
playlist_url = input()
playlist_id = playlist_url.split('/')[-1].split('?')[0]

# Get all tracks from the playlist
try:
    results = sp.playlist_tracks(playlist_id)
except spotipy.exceptions.SpotifyException as e:
    if e.http_status == 404:
        print("Playlist not found. Please check if the playlist exists and is public.")
    else:
        print(f"An error occurred: {e}")
    exit()

tracks = results['items']

# Since the API call gets 100 songs at a time we need to keep sending requests until there isn't anything left
while results['next']:
    results = sp.next(results)
    tracks.extend(results['items'])
    track_count = len(tracks)

artist_ids = list(set(artist['id'] for track in tracks for artist in track['track']['artists']))
all_genres = get_artists_genres(sp, artist_ids)

# Create playlist function that creates a new playlist and adds the filtered songs to it
def create_playlist(sp2, username, playlist_name, playlist_description, filtered_songs):
    playlist = sp2.user_playlist_create(username, playlist_name, description=playlist_description, public=True)
    sp2.user_playlist_add_tracks(username, playlist['id'], filtered_songs)
    return playlist['id']

# Process all tracks and collect genre information
all_track_genres = []
for track in tracks:
    artists = track['track']['artists']
    genres = set()
    for artist in artists:
        genres.update(all_genres.get(artist['id'], set()))
    all_track_genres.append(genres)

# Count occurrences of each genre
genre_counts = Counter(genre for genres in all_track_genres for genre in genres)

# Sort genres by count in descending order
sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)

print(f"Number of songs in your playlist: {len(tracks)}")
print("Here is the count of songs for each genre in your playlist:")
for genre, count in sorted_genres:
    print(f"{genre}: {count}, ", end="")

print(f"\nTotal unique genres: {len(genre_counts)}")

# Taking in user input for genres they want added, playlist name, & playlist description
print("\u001b[38;5;87mEnter the genre(s) you want to add to a new playlist. If there are multiple genres you'd"
      " like to add, enter it as a comma seperated list: \u001b[0m")
genre_input = input()
selected_genres = set(genre.strip().lower() for genre in genre_input.split(','))

print("\u001b[38;5;87mEnter the name of your playlist: \u001b[0m")
playlist_name_input = input()

print("\u001b[38;5;87mEnter a description of your playlist (Optional): \u001b[0m")
playlist_description_input = input()

# Filter songs based on selected genres
filtered_songs_ids = []
for track, genres in zip(tracks, all_track_genres):
    track_id = track['track']['id']
    # Convert genres to lowercase for case-insensitive comparison
    lower_genres = set(genre.lower() for genre in genres)
    if lower_genres.intersection(selected_genres):
        filtered_songs_ids.append(track_id)

# Create the new playlist with filtered songs
new_playlist_id = create_playlist(sp2, auth_user_id, playlist_name_input, playlist_description_input,
                                  filtered_songs_ids)
print(f"New Playlist '{playlist_name_input}' created successfully with ID: {new_playlist_id}")
print(f"Number of songs in the new playlist: {len(filtered_songs_ids)}")
