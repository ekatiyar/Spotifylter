# Spotifylter Curation Service
Spotify Listening History driven reccomendation and analysis service.

Sign up on [Spotifylter](https://spotifylter.herokuapp.com).

## Current Features
1. Spotifylter Playlist: Add songs you want to listen to and possibly add to your library. If you like the song, add it to your library. After 5 listens, the song is removed.

2. Collaborative Playlist: Auto-add music you seem to like, and auto-remove music that the group likes the least.


## Planned Features
1. Spotifylter Playlist: Auto-add songs that aren't in your library but you seem to like

2. Spotifylter Playlist: Auto-add new albums from your favorite artists

3. Data Dashboard: Provide analytics about your favorite and least favorite music in your library, so you can clear our stale music


## Personal Setup Instructions
If you're interested in running the app yourself, here are instructions for getting it set up:

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
