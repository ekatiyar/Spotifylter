import spotipy
import os
import time

import common
# import mock
# mock.set_vars()

# Global variables


def main_user_loop() -> None:
    auth_manager = common.environ_auth_manager(common.scopes_list)
    token = common.get_token(auth_manager)
    sp = spotipy.Spotify(auth=token["access_token"])
    user: dict = sp.me()

    candidate_playlist = os.getenv("CANDIDATE_PLAYLIST")
    cached_song = None
    while(True):

        # Refresh token if needed:
        new_token = common.check_refresh(auth_manager, token)
        if token["access_token"] != new_token["access_token"]:
            sp.set_auth(new_token["access_token"])
            token = new_token

        results = sp.currently_playing()

        # If null (no devices using spotify) or not playing, sleep for 5 mins
        if False and (not results or not results["is_playing"]):
            cached_song = results
            time.sleep(5 * 60)
            continue

        # if no difference, update cache and sleep
        if False and (not cached_song or results["item"]["id"] == cached_song["item"]["id"]):
            cached_song = results
            time.sleep(5)
            continue

        song_id = results["item"]["id"]

        in_saved = sp.current_user_saved_tracks_contains([song_id])
        uri = common.parse_uri(results['context']["uri"])
        in_candidate = results['context'] and results['context']['type'] == 'playlist' and uri == candidate_playlist

        if in_candidate and in_saved[0]:
            sp.user_playlist_remove_all_occurrences_of_tracks(
                user["id"], candidate_playlist, [song_id])

        cached_song = results  # NOTE: This must be the last line of the for loop
        time.sleep(5)


if __name__ == "__main__":
    main_user_loop()
