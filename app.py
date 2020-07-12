import os
from flask import Flask, session, request, redirect
from flask_session import Session
import spotipy
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import time

import common
# import mock
# mock.set_vars()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Session(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class UsersModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    email = db.Column(db.String())
    playlist_id = db.Column(db.String())
    refresh_token = db.Column(db.String())
    last_email = db.Column(db.Integer())

    def __init__(self, username: str, email: str, playlist_id: str, refresh_token: str, last_email: int):
        self.username = username
        self.email = email
        self.playlist_id = playlist_id
        self.refresh_token = refresh_token
        self.last_email = last_email

    def __repr__(self):
        return f"<User {self.username} last emailed {self.email} at {self.last_email} >"


@app.route('/')
def index():
    try:
        os.remove(".tokens")
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
    userdata = UsersModel.query.filter_by(username=user["id"]).first()
    if userdata and userdata.refresh_token != refresh_token:
        userdata.refresh_token = refresh_token
        db.session.add(userdata)
        db.session.commit()
        return f'<h2>{user["display_name"]} has been updated</h2>'
    playlist = spotify.user_playlist_create(
        username, "Spotifylter Playlist", description="Candidate Playlist for Spotifylter")
    new_user = UsersModel(username=username, email=email, playlist_id=playlist["id"],
                          refresh_token=refresh_token, last_email=int(time.mktime(time.gmtime())))
    db.session.add(new_user)
    db.session.commit()
    return f'<h2>{user["display_name"]} has been created</h2>'
