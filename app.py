from os import urandom, remove
from flask import Flask, session, request, redirect
from flask_session import Session
import spotipy
from time import mktime, gmtime
from db import Scoped_Session
from models import Users

import common
# import mock
# mock.set_vars()

app = Flask(__name__)
app.config['SECRET_KEY'] = urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)


@app.route('/')
def index():
    try:
        remove(".tokens")
    except:
        pass

    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope=" ".join(common.scopes_list), cache_path='.tokens')
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    if request.args.get("code"):
        session['token_info'] = auth_manager.get_access_token(
            request.args["code"])
        return redirect('/')

    if not session.get('token_info'):
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'
    
    session['token_info'] = common.check_refresh(auth_manager, session.get('token_info'))

    spotify.set_auth(session.get('token_info')["access_token"])
    return f'<h2>Hi {spotify.me()["display_name"]}, ' \
           f'<small><a href="/sign_out">[sign out]<a/></small></h2>' \
           f'<a href="/setup">Create/Update Sptoifylter Account</a>'


@app.route('/sign_out')
def sign_out():
    session.clear()
    return redirect('/')


@app.route('/setup')
def playlists():
    if not session.get('token_info'):
        return redirect('/')
    spotify = spotipy.Spotify(session.get('token_info')['access_token'])
    refresh_token = session.get('token_info')["refresh_token"]
    user = spotify.me()
    username = user["id"]
    email = user["email"]

    userdata = Scoped_Session.query(
        Users).filter_by(username=user["id"]).first()

    if userdata:
        if userdata.refresh_token != refresh_token:
            userdata.refresh_token = refresh_token
            Scoped_Session.add(userdata)
            Scoped_Session.commit()
            return f'<h2>{user["display_name"]} has been updated</h2>'
        else:
            return f'<h2>{user["display_name"]} has already been registered</h2>'

    playlist = spotify.user_playlist_create(
        username, "Spotifylter Playlist", description="Candidate Playlist for Spotifylter")
    new_user = Users(username=username, email=email, playlist_id=playlist["id"],
                     refresh_token=refresh_token, last_email=int(mktime(gmtime())))
    Scoped_Session.add(new_user)
    Scoped_Session.commit()
    return f'<h2>{user["display_name"]} has been created</h2>'


@app.teardown_appcontext
def cleanup(resp_or_exec):
    Scoped_Session.remove()
