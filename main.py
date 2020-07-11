import spotipy
import os
import common
import time

# import mock
# mock.set_vars()

# Global variables
auth_manager = common.environ_auth_manager(common.scopes_list)
token = common.get_token(auth_manager)
sp = spotipy.Spotify(auth=token["access_token"])
email = sp.current_user()["email"]


def main() -> None:
    cached_song = None
    while(True):

        # Refresh token if needed:
        new_token = common.check_refresh(auth_manager)
        if token["access_token"] != new_token["access_token"]:
            sp.set_auth(new_token["access_token"])

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

        in_candidate = False
        if song_id['context'] and song_id['context']['type'] == 'playlist':
            in_candidate = common.parse_uri(
                song_id['context']) == os.getenv("CANDIDATE_PLAYLIST")

        cached_song = results  # NOTE: This must be the last line of the for loop
        time.sleep(5)


if __name__ == "__main__":
    main()
