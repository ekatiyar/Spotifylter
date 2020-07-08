import os
import spotipy

# TODO: Replace this with some front-end way to authenticate on heroku

scopes_list = [
    "playlist-modify-public",
    "playlist-modify-private",
    "user-read-currently-playing",
    "user-read-playback-state",
    "user-library-read",
    "user-read-email"
]


def setup() -> None:
    scopes = " ".join(scopes_list)
    cid = input("SPOTIPY CLIENT ID: ")
    csec = input("SPOTIPY CLIENT SECRET: ")
    cuser = input("SPOTIFY USERNAME: ")
    cred = "http://localhost:8080"

    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=cid,
        client_secret=csec,
        redirect_uri= cred,
        username = cuser, 
        scope=scopes)
    token = auth_manager.get_cached_token()
    if token==None:
        token = auth_manager.get_access_token()

    print("Add the following items to the heroku config vars\n")
    print("SPOTIPY_CLIENT_ID", cid)
    print("SPOTIPY_CLIENT_SECRET", csec)
    print("SPOTIPY_REDIRECT_URI", cred)
    print("SPOTIFY_USERNAME", cuser)
    print("SPOTIFY_REFRESH", token["refresh_token"])

    input("Press Enter once you have copied these values over")




if __name__ == "__main__":
    setup()