import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import os
from dotenv import load_dotenv

# Getting api and secret from .env and Authenticating
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

playlist_url = 'https://open.spotify.com/playlist/0MOS9KmbPlPKpHpYJ52f9w?si=eba3ea44c4b14e86'
playlist_id = playlist_url.split('/')[-1].split('?')[0]

# Get all tracks from the playlist
results = sp.playlist_tracks(playlist_id)
tracks = results['items']

# If there are more tracks, keep fetching
while results['next']:
    results = sp.next(results)
    tracks.extend(results['items'])

# Print all track names, artists, and genres on a song by song basis
for track in tracks:
    track_name = track['track']['name']
    artists = track['track']['artists']
    artist_names = ', '.join([artist['name'] for artist in artists])

    genres = set()
    for artist in artists:
        artist_info = sp.artist(artist['id'])
        genres.update(artist_info['genres'])

    genres_str = ', '.join(genres) if genres else 'No genre information'


    print(f"{track_name} by {artist_names} - Genres: {genres_str}")



