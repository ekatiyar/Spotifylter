import os
import spotipy
from typing import List, Dict
from time import time
import models
import db

# import mock
# mock.set_vars()

# Global Variables
scopes_list = [
    "user-read-playback-state",
    "user-read-email",
    "user-top-read",
    "user-read-currently-playing",
    "playlist-read-private",
    "playlist-modify-private",
    "user-library-read",
]
max_plays = 5
max_users = 10


def get_token(auth_manager: spotipy.oauth2.SpotifyOAuth, refresh_token: str) -> dict:
    token = auth_manager.refresh_access_token(refresh_token)
    return token


def check_refresh(auth_manager: spotipy.oauth2.SpotifyOAuth, token: dict) -> dict:
    assert(token["access_token"])
    if auth_manager.is_token_expired(token):
        return get_token(auth_manager, token["refresh_token"])
    else:
        return token


def gen_spotify(token_info: dict) -> spotipy.Spotify:
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope=" ".join(scopes_list), cache_path='.tokens')
    token_info = check_refresh(auth_manager, token_info)
    spotify = spotipy.Spotify(auth=token_info['access_token'])
    return spotify


def get_env(key: str) -> str:
    val = os.getenv(key)
    assert(val != None)
    return str(val)


def parse_uri(uri: str) -> str:
    ind = uri.find("playlist")
    assert(ind != -1)
    return uri[ind:].split(':')[-1]


def resolve_playlist(spotify: spotipy.Spotify, username: str, title: str, description: str) -> dict:
    existing_playlists = spotify.user_playlists(username)
    playlists_list: list = existing_playlists["items"]
    while(playlists_list):
        playlist = playlists_list.pop()
        if playlist["name"] == title and playlist["description"] == description:
            break
        if len(playlists_list) == 0 and existing_playlists["next"]:
            existing_playlists = spotify.next(existing_playlists)
            playlists_list = existing_playlists["items"]
        else:
            playlist = None
    if not playlist:
        playlist = spotify.user_playlist_create(
            username, title, public=False, description=description)
    return playlist


def gen_user(session, token_info: Dict) -> str:  # caller is responsible for closing session
    spotify = gen_spotify(token_info)
    refresh_token = token_info["refresh_token"]
    user = spotify.me()
    username = user["id"]
    email = user["email"]

    userdata: models.Users = session.query(
        models.Users).filter_by(username=user["id"]).first()

    playlist = resolve_playlist(
        spotify, username, "Spotifylter Playlist", "Candidate Playlist for Spotifylter")

    if userdata:
        if userdata.refresh_token != refresh_token:
            userdata.refresh_token = refresh_token
            session.add(userdata)
            session.commit()
            return f'<h2>{user["display_name"]}\'s access token has been updated</h2>'
        elif userdata.playlist_id != playlist["id"]:
            userdata.playlist_id = playlist["id"]
            session.add(userdata)
            session.commit()
            return f'<h2>{user["display_name"]}\'s target playlist has been updated</h2>'
        else:
            return f'<h2>{user["display_name"]} has already been registered</h2>'

    current_users = session.query(models.Users).count()
    if current_users < max_users:

        new_user = models.Users(username=username, email=email, playlist_id=playlist["id"],
                                refresh_token=refresh_token, last_email=int(time()))
        session.add(new_user)
        session.commit()
        return f'<h2>{user["display_name"]} has been created</h2>'
    else:
        return f'<h2>The user limit has been reached. Account creation failed</h2>'


def delete_user(session, token_info) -> bool:  # caller is responsible for closing session
    spotify = gen_spotify(token_info)
    user = spotify.me()
    username = user["id"]
    res = session.query(models.Users).filter_by(
        username=username).delete(synchronize_session=False)
    session.commit()
    return res

# TODO: Lots of copied code here... fix pls


def update_song(username: str, song: dict, location: str) -> bool:
    song_id = song["item"]["id"]
    progress = song["progress_ms"]/1000
    duration = song["item"]["duration_ms"]/1000
    s = db.Session_Factory()
    counts: models.Counts = s.query(
        models.Counts).filter_by(username=username, song=song_id).first()
    if counts:
        counts.song_avg = update_avg(
            counts.song_count, progress, counts.song_avg)
        counts.song_count += 1
        counts.location = location
    else:
        counts = models.Counts(username=username, song=song_id, location=location,
                               song_count=1, song_avg=progress, song_duration=duration, filtered=False)
    s.add(counts)
    ret = counts.song_count >= max_plays
    s.commit()
    s.close()
    return ret


def update_filtered(username: str, sp: spotipy.Spotify, playlist_id: str, song: dict, new_location: str):
    song_id = song["item"]["id"]
    sp.user_playlist_remove_all_occurrences_of_tracks(
        username, playlist_id, [song_id])
    s = db.Session_Factory()
    counts: models.Counts = s.query(
        models.Counts).filter_by(username=username, song=song_id).first()
    if counts:
        counts.location = new_location
        counts.song_count = 0
        counts.song_avg = 0
        counts.filtered = True
        s.add(counts)
        s.commit()
    s.close()


def update_avg(prev_count: int, progress: float, avg_progress: float) -> float:
    return (avg_progress*prev_count + progress)/(prev_count+1)
