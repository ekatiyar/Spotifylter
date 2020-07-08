import spotipy
import os
import common
import time

# import mock
# mock.set_vars()

auth_manager = common.environ_auth_manager(common.scopes_list)
token = common.get_token(auth_manager)

sp = spotipy.Spotify(auth=token["access_token"])

cached_song = None

while(True):
    results = sp.currently_playing()
    if False and (results == None or not results["is_playing"]):
        time.sleep(5 * 60)
        cached_current = results
        continue

    if cached_song == None or results["item"]["id"] == cached_song["item"]["id"]:
        time.sleep(5)
        cached_current = results
        continue

    song_id = results["item"]["id"]

    in_saved = sp.current_user_saved_tracks_contains([song_id])

    print(in_saved)

    cached_song = results
