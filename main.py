import spotipy
import os
import common

# common.set_vars()

auth_manager = common.environ_auth_manager(common.scopes_list)
token = common.get_token(auth_manager)

sp = spotipy.Spotify(auth=token["access_token"])

results = sp.current_user_saved_tracks()
for idx, item in enumerate(results['items']):
    track = item['track']
    print(idx, track['artists'][0]['name'], " – ", track['name'])

