import spotipy
from os import getenv
from time import sleep, strftime, localtime
from typing import List, Dict
import threading

import common
from models import Users
from db import Session_Factory
# import mock
# mock.set_vars()

# Global variables
auth_manager = spotipy.oauth2.SpotifyOAuth(
    scope=" ".join(common.scopes_list), cache_path='.tokens')
active_wait = 1
inactive_wait = 60*5


# This function monitors user listening history
def main_user_loop(token_info: dict, playlist_id: str, last_email: int) -> None:
    sp = common.gen_spotify(token_info)
    user: dict = sp.me()

    cached_song = None
    while(True):

        # Refresh token if needed:
        new_token = common.check_refresh(auth_manager, token_info)
        if token_info["access_token"] != new_token["access_token"]:
            sp.set_auth(new_token["access_token"])
            token_info = new_token

        results = sp.currently_playing()

        # If null (no devices using spotify) or not playing, deactivate thread
        if not results or not results["is_playing"]:
            return

        # if no difference, update cache and sleep
        if not cached_song or results["item"]["id"] == cached_song["item"]["id"]:
            cached_song = results
            sleep(active_wait)
            continue

        song_id = cached_song["item"]["id"]

        in_saved = sp.current_user_saved_tracks_contains([song_id])
        if in_saved[0]:
            common.update_library(user["id"], cached_song)
        in_candidate = cached_song.get('context') and cached_song['context']['type'] == 'playlist' and common.parse_uri(
            cached_song['context']["uri"]) == playlist_id
        if in_candidate:
            flagged = common.update_playlist(
                user["id"], cached_song)

        if not in_candidate and not in_saved[0]:
            common.update_other(user["id"], cached_song)

        if (in_candidate and in_saved[0]) or flagged:
            common.update_filtered(user["id"], sp, playlist_id, song_id)

        cached_song = results  # NOTE: This must be the last line of the for loop
        sleep(active_wait)


def users_manager():
    s = Session_Factory()
    threads: Dict[str, threading.Thread] = dict()
    while(True):
        for user in s.query(Users).all():
            if threads.get(user.username) and threads[user.username].is_alive:
                continue
            token_info = common.get_token(auth_manager, user.refresh_token)
            sp = common.gen_spotify(token_info)
            if sp.currently_playing():
                print(f'Spinning up thread for {user.username}')
                thread = threading.Thread(target=main_user_loop, args=(
                    token_info, user.playlist_id, user.last_email))
                threads[user.username] = thread
                thread.start()
        sleep(inactive_wait)
    s.close()


if __name__ == "__main__":
    users_manager()
