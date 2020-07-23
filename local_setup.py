import os
import spotipy
import common


def setup() -> None:
    cid = input("SPOTIPY CLIENT ID: ")
    csec = input("SPOTIPY CLIENT SECRET: ")
    cuser = input("SPOTIFY USERNAME: ")
    cplaylist = common.parse_uri(input("CANDIDATE PLAYLIST URI: "))
    cred = "http://localhost:8080"

    auth_manager = common.gen_auth_manager(
        cid, csec, cred, cuser, common.scopes_list)
    auth_manager.get_auth_response()
    token = auth_manager.get_cached_token()

    print("Add the following items to the heroku config vars\n")
    print("SPOTIPY_CLIENT_ID", cid)
    print("SPOTIPY_CLIENT_SECRET", csec)
    print("SPOTIPY_REDIRECT_URI", cred)
    print("SPOTIFY_USERNAME", cuser)
    print("CANDIDATE_PLAYLIST", cplaylist)
    print("SPOTIFY_REFRESH", token["refresh_token"])

    input("Press Enter once you have copied these values over")


if __name__ == "__main__":
    setup()
