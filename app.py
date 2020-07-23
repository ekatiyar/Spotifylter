from os import urandom, remove
from flask import Flask, session, request, redirect
from flask_session import Session
import spotipy
from db import Scoped_Session
from models import Users

import common

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

    session['token_info'] = common.check_refresh(
        auth_manager, session.get('token_info'))

    spotify.set_auth(session.get('token_info')["access_token"])
    return f'<h2>Hi {spotify.me()["display_name"]}, ' \
           f'<small><a href="/sign_out">[sign out]<a/></small></h2>' \
           f'<a href="/setup">Create/Update Spotifylter Account</a>' \
           f'<br><a href="/remove">Delete Account</a>'


@app.route('/sign_out')
def sign_out():
    session.clear()
    return redirect('/')


@app.route('/setup')
def playlists():
    token_info = session.get('token_info')
    if not token_info:
        return redirect('/')
    return common.gen_user(Scoped_Session, token_info) + f'<a href="/">[HOME]<a/>'


@app.route('/remove')
def remove_user():
    token_info = session.get('token_info')
    if not token_info:
        return redirect('/')
    res = common.delete_user(Scoped_Session, token_info)
    if res:
        return f'<h2>Deletion Successful, {res} Accounts Deleted</h2>' \
               f'<a href="/">[HOME]<a/>'
    else:
        return f'<h2>Deletion Failed, {res} Accounts Matched</h2>' \
               f'<a href="/">[HOME]<a/>'


@app.teardown_appcontext
def cleanup(resp_or_exec):
    Scoped_Session.remove()
