import spotipy
from os import getenv
from time import sleep
from typing import Dict
import threading

import common
from models import User, Playlist
from db import Session_Factory

# Global variables
auth_manager = spotipy.oauth2.SpotifyOAuth(
    scope=" ".join(common.scopes_list), cache_path=".tokens"
)
active_wait = 1
inactive_wait = 60


# This function monitors user listening history
def listeningd(sp: spotipy.Spotify, userinfo: User, token_info: dict) -> None:

    cached_song: Dict = dict()
    username = userinfo.username

    while True:

        # Refresh token if needed:
        new_token = common.check_refresh(auth_manager, token_info)
        if token_info["access_token"] != new_token["access_token"]:
            sp.set_auth(new_token["access_token"])
            token_info = new_token

        results = sp.currently_playing()

        # If null (no devices using spotify) or not playing, deactivate thread
        if not results or not results["is_playing"]:
            print(f"Spinning down thread for {username}")
            return

        # if no difference or item unavailable, update cache and sleep
        try:
            if (
                not "item" in cached_song
                or not "item" in results
                or not "id" in results["item"]
                or not "id" in cached_song["item"]
                or results["item"]["id"] == cached_song["item"]["id"]
            ):
                cached_song = results
                sleep(active_wait)
                continue
        except TypeError as e:
            print(f"cached song: {cached_song}")
            print(f"results: {results}")
            print(e)
            return

        # Store cached song to db so we can update
        song_id = cached_song["item"]["id"]

        in_saved = sp.current_user_saved_tracks_contains([song_id])[0]
        candidate = False
        if cached_song.get("context") and cached_song["context"]["type"] == "playlist":
            playlist: Playlist = userinfo.playlists.get(
                common.parse_uri(cached_song["context"]["uri"])
            )
            if playlist:
                candidate = playlist.candidate

        if in_saved and candidate:
            common.filter_out(username, sp, playlist.playlist_id, cached_song, True)
            # common.update_song(username, cached_song, False) # Don't update stats, just remove since it might be skipped since it's saved
        elif candidate:
            flagged = common.update_song(username, cached_song, True)
            if flagged:
                common.filter_out(
                    username, sp, playlist.playlist_id, cached_song, False
                )
        else:
            common.update_song(username, cached_song, False)

        cached_song = results  # NOTE: This must be the last line of the for loop
        sleep(active_wait)


def service_manager():
    s = Session_Factory()
    threads: Dict[str, common.UserThread] = dict()
    while True:
        for user in s.query(User).all():
            try:
                if user.username in threads and threads[user.username].is_alive():
                    continue
                elif user.username in threads:
                    token_info = common.check_refresh(
                        auth_manager, threads[user.username].token_info
                    )
                else:
                    token_info = common.get_token(auth_manager, user.refresh_token)
            except spotipy.exceptions.SpotifyException as e:
                print(f"Failed to get token for {user.username}: {e}")
                continue

            sp = common.gen_spotify(token_info)
            results = sp.currently_playing()
            if results and results["is_playing"]:
                print(f"Spinning up thread for {user.username}")
                thread = threading.Thread(
                    target=listeningd, args=(sp, user, token_info), daemon=True
                )
                threads[user.username] = common.UserThread(thread, token_info)
                thread.start()
        sleep(inactive_wait)

    s.close()  # TODO: Implement signal handling


if __name__ == "__main__":
    service_manager()
