# Spotifylter Curation Service
Spotify Listening History driven reccomendation and analysis service. Not only does it figure out what music you like (which others already do), it additionally figures out what music you don't like, maintaining library and playlist quality.

I wanted to build this because I found myself skipping songs so often, and I wanted to inform this process with automation and data analysis.

Sign up for the service on [Spotifylter](https://eashman.apphost.ocf.berkeley.edu/). Currently the service is in an pre-alpha state.

## Current Features
1. Spotifylter Playlist: Add songs to this playlist that you want to listen to and possibly add to your library. If you like the song, add it to your library. After 5 listens, the song is removed from the playlist. Listening history in this playlist is sandboxed from the rest of your listening history.

2. Collaborative Playlist: Auto-add music each member seem to like, and auto-remove music that the group likes the least on a twice-monthly basis.


## Planned Features
THe following is not an exhaustive list:

1. Spotifylter Playlist: Auto-add songs to playlist that aren't in your library but you seem to like

2. Spotifylter Playlist: Auto-add new albums from your favorite artists to the playlist

3. Spotifylter Playlist: Currently Spotifylter Playlist is empty on service registration. Add some songs to the playlist to get the user familiar with the service.

4. Data Dashboard: Provide analytics about your favorite and least favorite music in your library, so you can clear our stale music


## Personal Setup Instructions
If you're interested in running the app yourself, here are instructions for getting it set up on heroku:

1. Follow the instructions [here](https://developer.spotify.com/documentation/web-api/quick-start/) to set up your account and create your application
<img src="https://raw.githubusercontent.com/ekatiyar/Spotifylter/master/images/app_create.PNG" alt="Image of App Creation" width="300"/>

2. Deploy app to heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

3. Set the client id, client secret, and redirect urls as environment variables in heroku.

<img src="https://raw.githubusercontent.com/ekatiyar/Spotifylter/master/images/idsecret.png" alt="Image of App Credentials" width="300"/>
<img src="https://raw.githubusercontent.com/ekatiyar/Spotifylter/master/images/redirecturi.png" alt="Image of Redirect URI" width="300"/>


## Additional Information
For the curious, here is a simple diagram detailing the eventual completed product

<img src="https://raw.githubusercontent.com/ekatiyar/Spotifylter/master/images/Diagram.png" alt="App Diagram" width="600"/>
