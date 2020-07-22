import spotipy
from os import getenv
from time import sleep, strftime, localtime
from typing import List, Dict
import threading

import common
from models import Users
from db import Session_Factory

# Global variables
auth_manager = spotipy.oauth2.SpotifyOAuth(
    scope=" ".join(common.scopes_list), cache_path='.tokens')
active_wait = 1
inactive_wait = 60


# This function monitors user listening history
def main_user_loop(sp: spotipy.Spotify, username: str, token_info: dict, playlist_id: str, last_email: int) -> None:

    cached_song: Dict = dict()
    in_playlist = common.get_candidate_songs(sp, playlist_id)
    while(True):

        # Refresh token if needed:
        new_token = common.check_refresh(auth_manager, token_info)
        if token_info["access_token"] != new_token["access_token"]:
            sp.set_auth(new_token["access_token"])
            token_info = new_token

        results = sp.currently_playing()

        # If null (no devices using spotify) or not playing, deactivate thread
        if not results or not results["is_playing"]:
            print(f'Spinning down thread for {username}')
            return

        # if no difference or item unavailable, update cache and sleep
        if not "item" in cached_song or not "item" in results or results["item"]["id"] == cached_song["item"]["id"]:
            cached_song = results
            sleep(active_wait)
            continue

        # Store cached song to db so we can update
        song_id = cached_song["item"]["id"]

        in_saved = sp.current_user_saved_tracks_contains([song_id])[0]
        in_candidate = song_id in in_playlist

        if in_saved and in_candidate:
            common.update_filtered(
                username, sp, playlist_id, cached_song, "library")
            in_playlist = [pid for pid in in_playlist if pid != song_id]
            common.update_song(username, cached_song, "library")
        elif in_saved:
            common.update_song(username, cached_song, "library")
        elif in_candidate:
            flagged = common.update_song(username, cached_song, "playlist")
            if flagged:
                common.update_filtered(
                    username, sp, playlist_id, cached_song, "other")
        else:
            common.update_song(username, cached_song, "other")

        cached_song = results  # NOTE: This must be the last line of the for loop
        sleep(active_wait)


def users_manager():
    s = Session_Factory()
    threads: Dict[str, common.UserThread] = dict()
    while(True):
        for user in s.query(Users).all():
            try:
                if user.username in threads and threads[user.username].is_alive():
                    continue
                elif user.username in threads:
                    token_info = common.check_refresh(
                        auth_manager, threads[user.username].token_info)
                else:
                    token_info = common.get_token(
                        auth_manager, user.refresh_token)
            except spotipy.exceptions.SpotifyException as e:
                print(f"Failed to get token for {user.username}: {e}")
                continue

            sp = common.gen_spotify(token_info)
            results = sp.currently_playing()
            if results and results["is_playing"]:
                print(f'Spinning up thread for {user.username}')
                thread = threading.Thread(target=main_user_loop, args=(
                    sp, user.username, token_info, user.playlist_id, user.last_email), daemon=True)
                threads[user.username] = common.UserThread(thread, token_info)
                thread.start()
        sleep(inactive_wait)

    s.close()  # TODO: Implement signal handling


if __name__ == "__main__":
    users_manager()
