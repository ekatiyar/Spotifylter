import os
import spotipy
from typing import List, Dict
from time import time
import models
import db

scopes_list = [
    "playlist-modify-public",
    "playlist-modify-private",
    "user-read-currently-playing",
    "user-read-playback-state",
    "user-library-read",
    "user-read-email",
    "user-top-read"
]


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
    spotify = spotipy.Spotify(token_info['access_token'])
    return spotify


def get_env(key: str) -> str:
    val = os.getenv(key)
    assert(val != None)
    return str(val)


def parse_uri(uri: str) -> str:
    ind = uri.find("playlist")
    assert(ind != -1)
    return uri[ind:].split(':')[-1]


def gen_user(session, token_info: Dict) -> str:  # caller is responsible for closing session
    spotify = gen_spotify(token_info)
    refresh_token = token_info["refresh_token"]
    user = spotify.me()
    username = user["id"]
    email = user["email"]

    userdata = session.query(
        models.Users).filter_by(username=user["id"]).first()

    if userdata:
        if userdata.refresh_token != refresh_token:
            userdata.refresh_token = refresh_token
            session.add(userdata)
            session.commit()
            return f'<h2>{user["display_name"]} has been updated</h2>'
        else:
            return f'<h2>{user["display_name"]} has already been registered</h2>'

    current_users = session.query(models.Users).count()
    if current_users < 255:
        playlist = spotify.user_playlist_create(
            username, "Spotifylter Playlist", description="Candidate Playlist for Spotifylter")
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
