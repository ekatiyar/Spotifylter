from os import urandom, remove
from flask import Flask, session, request, redirect, url_for
from flask_session import Session
import spotipy
from db import Scoped_Session
import common

app = Flask(__name__)
app.config["SECRET_KEY"] = urandom(64)
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

hosted_by = '<br><a href="https://www.ocf.berkeley.edu"> \
    <img src="https://www.ocf.berkeley.edu/hosting-logos/ocf-hosted-penguin.svg" \
        alt="Hosted by the OCF" style="border: 0;" /> \
</a>'


@app.route("/")
def index():
    try:
        remove(".tokens")
    except:
        pass

    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope=" ".join(common.scopes_list), cache_path=".tokens"
    )
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    if request.args.get("code"):
        session["token_info"] = auth_manager.get_access_token(request.args["code"])
        return redirect("/")

    if not session.get("token_info"):
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>' f"{hosted_by}"

    session["token_info"], mod = common.check_refresh(
        auth_manager, session.get("token_info")
    )

    spotify.set_auth(session.get("token_info")["access_token"])
    return (
        f'<h2>Hi {spotify.me()["display_name"]}, '
        f'<small><a href="/sign_out">[sign out]<a/></small></h2>'
        f'<a href="/setup">Create/Update Spotifylter Account</a>'
        f'<br><a href="/top">My Top Songs</a>'
        f'<br><a href="/filtered">Filtered Out Songs</a>'
        f'<br><a href="/remove">Delete Account</a>'
        f"{hosted_by}"
    )


@app.route("/sign_out")
def sign_out():
    session.clear()
    return redirect("/")


@app.route("/setup")
def playlists():
    token_info = session.get("token_info")
    if not token_info:
        return redirect("/")
    return (
        f"{common.gen_user(Scoped_Session, token_info)}"
        f'<a href="/">[HOME]<a/>'
        f"{hosted_by}"
    )


template = '<iframe src="https://open.spotify.com/embed/track/{track_id}" width="300" height="80" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'


@app.route("/filtered")
def filtered():
    token_info = session.get("token_info")
    if not token_info:
        return redirect("/")

    songs = common.get_filtered(Scoped_Session, token_info)

    if not songs:
        return "<h2>No Filtered Songs Available</h2>"
    ret = ""
    for song in songs:
        ret += template.format(track_id=song.song)
        ret += f'<p>Song Score: {song.song_count * (song.song_avg/song.song_duration) : .2f} | <a href="{url_for("remove_song", song_id = song.song)}">Delete Song</a></p>'

    return f"{ret}" f'<br><a href="/">[HOME]<a/>' f"{hosted_by}"


@app.route("/remove_song/<string:song_id>")
def remove_song(song_id):
    token_info = session.get("token_info")
    if not token_info:
        return redirect("/")
    common.remove_song(Scoped_Session, token_info, song_id)
    return redirect("/filtered")


@app.route("/top")
def top_songs():
    token_info = session.get("token_info")
    if not token_info:
        return redirect("/")

    top_songs = common.get_top_songs(Scoped_Session, token_info)

    if not top_songs:
        return "<h>Top Songs Unavailable</h2>"
    ret = ""
    for song in top_songs:
        ret += template.format(track_id=song.song)
        ret += f"<p>Song Score: {song.song_count * (song.song_avg/song.song_duration) : .2f}</p>"

    return f"{ret}" f'<br><a href="/">[HOME]<a/>' f"{hosted_by}"


@app.route("/remove")
def remove_user():
    token_info = session.get("token_info")
    if not token_info:
        return redirect("/")
    res = common.delete_user(Scoped_Session, token_info)
    if res:
        return (
            f"<h2>Deletion Successful, {res} Accounts Deleted</h2>"
            f'<a href="/">[HOME]<a/>'
            f"{hosted_by}"
        )
    else:
        return (
            f"<h2>Deletion Failed, {res} Accounts Matched</h2>"
            f'<a href="/">[HOME]<a/>'
            f"{hosted_by}"
        )


@app.teardown_appcontext
def cleanup(resp_or_exec):
    Scoped_Session.remove()
