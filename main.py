import spotipy
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
active_wait = 0.01  # 1% of current song duration
inactive_wait = 90  # 1/2 of average song length


# This function monitors user listening history
def listeningd(userinfo: User, sp=spotipy.Spotify, token_info=dict) -> None:

    cached_song: Dict = dict()
    username = userinfo.username

    while True:
        try:
            results: dict = sp.currently_playing()
        except spotipy.exceptions.SpotifyException as e:
            print(e)
            token_info, mod = common.check_refresh(auth_manager, token_info)
            print("refreshed")
            if mod:
                sp.set_auth(token_info["access_token"])
            print("reset auth")
            results = sp.currently_playing()
            print("Results: ", results)

        # If null (no devices using spotify) or not playing, deactivate thread
        if not results or not results["is_playing"]:
            print(f"Spinning down thread for {username}")
            return

        # Playing something without an item (an ad?), just continue
        if results.get("item", None) == None:
            continue

        # if no difference or item unavailable, update cache and sleep
        try:
            if (
                cached_song.get("item", None) == None
                or results["item"]["id"] == cached_song["item"]["id"]
            ):
                cached_song = results
                wait_time = (results["item"]["duration_ms"] / 1000) * active_wait
                sleep(wait_time)
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
        wait_time = (results["item"]["duration_ms"] / 1000) * active_wait
        sleep(wait_time)


def service_manager():
    threads: Dict[str, common.UserThread] = dict()
    s = Session_Factory()
    while True:
        for user in s.query(User).all():
            try:
                if user.username in threads:
                    # Refresh token if needed:
                    token_info, mod = common.check_refresh(
                        auth_manager, threads[user.username].token_info
                    )
                    if mod:
                        threads[user.username].update_token(token_info)
                    if (
                        threads[user.username].thread
                        and threads[user.username].is_alive()
                    ):
                        continue
                else:
                    token_info = common.get_token(auth_manager, user.refresh_token)
                    threads[user.username] = common.UserThread(None, token_info)
            except spotipy.exceptions.SpotifyException as e:
                print(f"Failed to get token for {user.username}: {e}")
                continue

            sp = common.gen_spotify(threads[user.username].token_info)
            common.check_user(sp, s, user)
            results = sp.currently_playing()
            if results and results["is_playing"]:
                print(f"Spinning up thread for {user.username}")
                thread = threading.Thread(
                    target=listeningd,
                    args=(user, sp, threads[user.username].token_info),
                    daemon=True,
                )
                threads[user.username].thread = thread
                thread.start()
        sleep(inactive_wait)
    s.close()


if __name__ == "__main__":
    service_manager()
