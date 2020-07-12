import os
import spotipy
from typing import List, Dict
import models

scopes_list = [
    "playlist-modify-public",
    "playlist-modify-private",
    "user-read-currently-playing",
    "user-read-playback-state",
    "user-library-read",
    "user-read-email"
]


def gen_auth_manager(client_id: str, client_secret: str, redirect_uri: str, username: str, scopes: list) -> spotipy.oauth2.SpotifyOAuth:
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        username=username,
        scope=" ".join(scopes))

    return auth_manager


def environ_auth_manager(scopes: list) -> spotipy.oauth2.SpotifyOAuth:
    return gen_auth_manager(
        get_env("SPOTIPY_CLIENT_ID"),
        get_env("SPOTIPY_CLIENT_SECRET"),
        get_env("SPOTIPY_REDIRECT_URI"),
        get_env("SPOTIPY_USERNAME"),
        scopes
    )


def get_token(auth_manager: spotipy.oauth2.SpotifyOAuth) -> dict:
    token = auth_manager.refresh_access_token(os.getenv("SPOTIFY_REFRESH"))
    return token


def check_refresh(auth_manager: spotipy.oauth2.SpotifyOAuth, token: dict) -> dict:
    assert(token["access_token"])
    if auth_manager.is_token_expired(token):
        return get_token(auth_manager)
    else:
        return token


def get_env(key: str) -> str:
    val = os.getenv(key)
    assert(val != None)
    return str(val)


def parse_uri(uri: str) -> str:
    ind = uri.find("playlist")
    assert(ind != -1)
    return uri[ind:-1].split(':')[-1]
