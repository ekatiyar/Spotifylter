import spotipy
from typing import List, Dict, Tuple
import models
from db import Session_Factory
from threading import Thread

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
auth_manager = spotipy.oauth2.SpotifyOAuth(
    scope=" ".join(scopes_list), cache_path=".tokens"
)
max_plays = 5
max_users = 100


class UserThread:
    def __init__(self, thread: Thread, token_info: Dict):
        self.thread = thread
        self.token_info = token_info
        # self.sp: spotipy.Spotify = gen_spotify(self.token_info)

    def is_alive(self) -> bool:
        return self.thread.is_alive()

    def update_token(self, new_token: Dict) -> None:
        self.token_info = new_token
        # self.sp.set_auth(self.token_info["access_token"])


def get_token(auth_manager: spotipy.oauth2.SpotifyOAuth, refresh_token: str) -> dict:
    token = auth_manager.refresh_access_token(refresh_token)
    return token


def check_refresh(
    auth_manager: spotipy.oauth2.SpotifyOAuth, token: dict
) -> Tuple[Dict, bool]:
    assert token["access_token"]
    if auth_manager.is_token_expired(token):
        return get_token(auth_manager, token["refresh_token"]), True
    else:
        return token, False


def gen_spotify(token_info: dict) -> spotipy.Spotify:
    token_info, mod = check_refresh(auth_manager, token_info)
    spotify = spotipy.Spotify(auth=token_info["access_token"])
    return spotify


def parse_uri(uri: str) -> str:
    ind = uri.find("playlist")
    assert ind != -1
    return uri[ind:].split(":")[-1]


def resolve_playlist(
    spotify: spotipy.Spotify,
    username: str,
    title: str,
    description: str,
    create: bool = False,
    collab: bool = False,
) -> Dict[str, Dict]:
    existing_playlists = spotify.user_playlists(username)
    playlists_list: list = existing_playlists["items"]
    ret: Dict[str, Dict] = dict()
    while playlists_list:
        playlist = playlists_list.pop()
        if playlist["description"] == description and (
            not collab or (collab and playlist.get("collaborative", False))
        ):
            ret[playlist["id"]] = playlist
        if len(playlists_list) == 0 and existing_playlists["next"]:
            existing_playlists = spotify.next(existing_playlists)
            playlists_list = existing_playlists["items"]
        else:
            playlist = None
    if not ret and create:
        playlist = spotify.user_playlist_create(
            username, title, public=False, description=description
        )
        ret[playlist["id"]] = playlist
    return ret


def update_playlists(
    session,
    userdata: models.User,
    add: Dict[str, Dict],
    existing: List[models.Playlist],
    candidate: bool,
    retstring: str = "",
) -> Tuple[models.User, str]:
    checkset = set(add.keys())
    for playlist in existing:
        if playlist.playlist_id in checkset:
            del add[playlist.playlist_id]
        else:
            is_owner = playlist.owner == userdata.username
            if is_owner:
                session.delete(playlist)
            del userdata.playlists[playlist.playlist_id]

    for playlist in add.values():
        is_owner = playlist["owner"]["id"] == userdata.username
        if is_owner:
            userdata.playlists[playlist["id"]] = models.Playlist(
                playlist_id=playlist["id"],
                owner=playlist["owner"]["id"],
                candidate=candidate,
            )
        else:
            existing_playlists = (
                session.query(models.Playlist)
                .filter_by(playlist_id=playlist["id"])
                .first()
            )
            if existing_playlists:
                userdata.playlists[playlist["id"]] = existing_playlists
        if candidate:  # Only one candidate playlist allowed
            break

    return userdata, retstring + f"<h2>Stored Playlists Updated</h2><br>"


def gen_user(
    session, token_info: Dict
) -> str:  # caller is responsible for closing session
    spotify = gen_spotify(token_info)
    refresh_token = token_info["refresh_token"]
    user = spotify.me()
    username = user["id"]
    email = user["email"]

    userdata: models.User = session.query(models.User).filter_by(
        username=user["id"]
    ).first()

    candidates = resolve_playlist(
        spotify,
        username,
        "Spotifylter Playlist",
        "Spotifylter Auto-Curate",
        create=True,
    )
    collabs = resolve_playlist(
        spotify, username, "Spotifylter Collab", "Spotifylter Auto-Collab", collab=True
    )

    if userdata:
        retstring = ""
        if userdata.refresh_token != refresh_token:
            userdata.refresh_token = refresh_token
            retstring += (
                f'<h2>{user["display_name"]}\'s access token has been updated</h2><br>'
            )
        db_curates: List[models.Playlist] = [
            pl for pl in userdata.playlists.values() if pl.candidate == True
        ]
        db_collabs: List[models.Playlist] = [
            pl for pl in userdata.playlists.values() if pl.candidate == False
        ]
        userdata, retstring = update_playlists(
            session, userdata, candidates, db_curates, True, retstring
        )
        userdata, retstring = update_playlists(
            session, userdata, collabs, db_collabs, False, retstring
        )
        if retstring == "":
            return f'<h2>{user["display_name"]} has already been registered</h2>'
        else:
            session.add(userdata)
            session.commit()
            return retstring

    current_users = session.query(models.User).count()
    if current_users < max_users:
        retstring = ""
        new_user = models.User(
            username=username, email=email, refresh_token=refresh_token, last_updated=0,
        )
        session.add(new_user)
        session.commit()
        new_user, retstring = update_playlists(
            session, new_user, candidates, [], True, retstring
        )
        new_user, retstring = update_playlists(
            session, new_user, collabs, [], False, retstring
        )
        session.add(new_user)
        session.commit()
        return retstring + f'<h2>{user["display_name"]} has been created</h2>'
    else:
        return f"<h2>The user limit: {current_users}/{max_users} has been reached. Account creation failed</h2>"


def delete_user(
    session, token_info
) -> bool:  # caller is responsible for closing session
    spotify = gen_spotify(token_info)
    user = spotify.me()
    username = user["id"]
    res = session.query(models.User).filter_by(username=username).delete()
    session.commit()
    return res


def update_song(username: str, song: dict, candidate: bool) -> bool:
    song_id = song["item"]["id"]
    progress = song["progress_ms"] / 1000
    duration = song["item"]["duration_ms"] / 1000
    s = Session_Factory()
    counts: models.Count = s.query(models.Count).filter_by(
        username=username, song=song_id, candidate=candidate
    ).first()
    if counts:
        counts.song_avg = update_avg(counts.song_count, progress, counts.song_avg)
        counts.song_count += 1
    else:
        counts = models.Count(
            username=username,
            song=song_id,
            candidate=candidate,
            song_count=1,
            song_avg=progress,
            song_duration=duration,
            filtered=False,
        )
    s.add(counts)
    ret = counts.song_count >= max_plays
    s.commit()
    s.close()
    return ret


def filter_out(
    username: str, sp: spotipy.Spotify, playlist_id: str, song: dict, preserve: bool
):
    song_id = song["item"]["id"]
    sp.user_playlist_remove_all_occurrences_of_tracks(username, playlist_id, [song_id])
    s = Session_Factory()
    count_row: models.Count = s.query(models.Count).filter_by(
        username=username, song=song_id, candidate=True
    ).first()
    if count_row:
        s.delete(count_row)
        if preserve:  # merge
            new_data: models.Count = s.query(models.Count).filter_by(
                username=username, song=song_id, candidate=False
            ).first()
            if new_data:
                prev_count = new_data.song_count
                new_data.song_count += count_row.song_count
                new_data.song_avg = (
                    (prev_count * new_data.song_avg)
                    + (count_row.song_count * count_row.song_avg)
                ) / new_data.song_count
                count_row.filtered = True
                s.add(new_data)
            else:
                count_row.candidate = False
                count_row.filtered = True
                s.add(count_row)
        s.commit()
    s.close()


def update_avg(prev_count: int, progress: float, avg_progress: float) -> float:
    return (avg_progress * prev_count + progress) / (prev_count + 1)


def get_candidate_songs(sp: spotipy.Spotify, playlist_id: str) -> List[str]:
    playlist = sp.playlist_tracks(playlist_id, fields="items(track(id)), next")
    ret = []
    cond = True
    while cond:
        items = playlist["items"]
        ret.extend([item["track"]["id"] for item in items])
        cond = playlist.get("next")
        playlist = sp.next(playlist)
    return ret
