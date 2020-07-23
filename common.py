import os
import spotipy
from typing import List, Dict
from time import time
import models
import db
from threading import Thread

# import mock
# mock.set_vars()

# Global Variables
scopes_list = [
    "user-read-playback-state",
    "user-read-email",
    "playlist-read-collaborative",
    "user-top-read",
    "user-read-currently-playing",
    "playlist-read-private",
    "playlist-modify-private",
    "user-library-read",
]
max_plays = 5
max_users = 10


class UserThread:
    def __init__(self, thread: Thread, token_info: dict):
        self.thread = thread
        self.token_info = token_info

    def is_alive(self) -> bool:
        return self.thread.is_alive()


def get_token(auth_manager: spotipy.oauth2.SpotifyOAuth, refresh_token: str) -> dict:
    token = auth_manager.refresh_access_token(refresh_token)
    return token


def check_refresh(auth_manager: spotipy.oauth2.SpotifyOAuth, token: dict) -> dict:
    assert(token["access_token"])
    if auth_manager.is_token_expired(token):
        return get_token(auth_manager, token["refresh_token"])
    else:
        return token


def gen_spotify(token_info: dict) -> spotipy.Spotify:
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope=" ".join(scopes_list), cache_path='.tokens')
    token_info = check_refresh(auth_manager, token_info)
    spotify = spotipy.Spotify(auth=token_info['access_token'])
    return spotify


def get_env(key: str) -> str:
    val = os.getenv(key)
    assert(val != None)
    return str(val)


def parse_uri(uri: str) -> str:
    ind = uri.find("playlist")
    assert(ind != -1)
    return uri[ind:].split(':')[-1]


def resolve_playlist(spotify: spotipy.Spotify, username: str, title: str, description: str, create: bool = False) -> dict:
    existing_playlists = spotify.user_playlists(username)
    playlists_list: list = existing_playlists["items"]
    while(playlists_list):
        playlist = playlists_list.pop()
        if playlist["description"] == description:
            break
        if len(playlists_list) == 0 and existing_playlists["next"]:
            existing_playlists = spotify.next(existing_playlists)
            playlists_list = existing_playlists["items"]
        else:
            playlist = None
    if not playlist and create:
        playlist = spotify.user_playlist_create(
            username, title, public=False, description=description)
    return playlist


def gen_user(session, token_info: Dict) -> str:  # caller is responsible for closing session
    spotify = gen_spotify(token_info)
    refresh_token = token_info["refresh_token"]
    user = spotify.me()
    username = user["id"]
    email = user["email"]

    userdata: models.User = session.query(
        models.User).filter_by(username=user["id"]).first()

    playlist = resolve_playlist(
        spotify, username, "Spotifylter Playlist", "Spotifylter Auto-Curate", True)
    collab = resolve_playlist(
        spotify, username, "Spotifylter Collab", "Spotifylter Auto-Collab")
    if not collab.get("collaborative"):
        collab = None
    if userdata:
        retstring = ""
        if userdata.refresh_token != refresh_token:
            userdata.refresh_token = refresh_token
            session.add(userdata)
            session.commit()
            retstring += f'<h2>{user["display_name"]}\'s access token has been updated</h2><br>'
        db_curate = userdata.playlists.get("curate")
        db_collab = userdata.playlists.get("collab")
        if db_curate.playlist_id != playlist["id"]:
            session.delete(db_curate)
            db_curate.playlist_id = playlist["id"]
            session.add(db_curate)
            session.commit()
            retstring += f'<h2>{user["display_name"]}\'s target playlist has been updated</h2><br>'
        if collab and (not db_collab or db_collab.playlist_id != collab["id"]):
            is_owner = collab["owner"]["id"] == username
            if not db_collab:
                new_collab = models.Playlist(
                    playlist_id=collab["id"], username=username, owner=is_owner, playlist_type="collab")
                session.add(new_collab)
                session.commit()
                retstring += f'<h2>{user["display_name"]}\'s collab playlist has been added</h2><br>'
            else:
                session.delete(db_collab)
                db_collab.playlist_id = collab["id"]
                db_collab.owner = collab["owner"]
                session.add(db_collab)
                session.commit()
                retstring += f'<h2>{user["display_name"]}\'s collab playlist has been updated</h2><br>'
        if retstring == "":
            return f'<h2>{user["display_name"]} has already been registered</h2>'
        else:
            return retstring

    current_users = session.query(models.User).count()
    if current_users < max_users:
        is_owner = playlist["owner"]["id"] == username
        new_user = models.User(username=username, email=email,
                               refresh_token=refresh_token, last_updated=int(time()))
        new_user.playlists["curate"] = models.Playlist(
            playlist_id=playlist["id"], username=username, owner=is_owner, playlist_type="curate")
        if collab:
            is_owner = collab["owner"]["id"] == username
            new_user.playlists["collab"] = models.Playlist(
                playlist_id=collab["id"], username=username, owner=is_owner, playlist_type="collab")
        session.add(new_user)
        session.commit()
        return f'<h2>{user["display_name"]} has been created</h2>'
    else:
        return f'<h2>The user limit: {current_users}/{max_users} has been reached. Account creation failed</h2>'


def delete_user(session, token_info) -> bool:  # caller is responsible for closing session
    spotify = gen_spotify(token_info)
    user = spotify.me()
    username = user["id"]
    res = session.query(models.User).filter_by(
        username=username).delete(synchronize_session=False)
    session.commit()
    return res


def update_song(username: str, song: dict, location: str) -> bool:
    song_id = song["item"]["id"]
    progress = song["progress_ms"]/1000
    duration = song["item"]["duration_ms"]/1000
    s = db.Session_Factory()
    counts: models.Count = s.query(
        models.Count).filter_by(username=username, song=song_id, localtion=location).first()
    if counts:
        counts.song_avg = update_avg(
            counts.song_count, progress, counts.song_avg)
        counts.song_count += 1
    else:
        counts = models.Count(username=username, song=song_id, location=location,
                              song_count=1, song_avg=progress, song_duration=duration, filtered=False)
    s.add(counts)
    ret = counts.song_count >= max_plays
    s.commit()
    s.close()
    return ret


def filter_out(username: str, sp: spotipy.Spotify, playlist_id: str, song: dict, new_location: str):
    song_id = song["item"]["id"]
    sp.user_playlist_remove_all_occurrences_of_tracks(
        username, playlist_id, [song_id])
    s = db.Session_Factory()
    count_row: models.Count = s.query(
        models.Count).filter_by(username=username, song=song_id, location=playlist_id).first()
    if count_row:
        s.delete(count_row)
        new_data: models.Count = s.query(models.Count).filter_by(
            username=username, song=song_id, location=new_location).first()
        if new_data:  # merge
            prev_count = new_data.song_count
            new_data.song_count += count_row.song_count
            new_data.song_avg = ((prev_count*new_data.song_avg) +
                                 (count_row.song_count*count_row.song_avg))/new_data.song_count
            count_row.filtered = True
            s.add(new_data)
        else:
            count_row.location = new_location
            count_row.filtered = True
            s.add(count_row)
        s.commit()
    s.close()


def update_avg(prev_count: int, progress: float, avg_progress: float) -> float:
    return (avg_progress*prev_count + progress)/(prev_count+1)


def get_candidate_songs(sp: spotipy.Spotify, playlist_id: str) -> List[str]:
    playlist = sp.playlist_tracks(playlist_id, fields="items(track(id)), next")
    ret = []
    cond = True
    while(cond):
        items = playlist["items"]
        ret.extend([item["track"]["id"] for item in items])
        cond = playlist.get("next")
        playlist = sp.next(playlist)
    return ret
