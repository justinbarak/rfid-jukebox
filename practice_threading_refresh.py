import datetime
import time
import threading
from dotenv import load_dotenv
import os

# Initialize
load_dotenv()
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:7070"

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint

scope = "user-read-playback-state,user-modify-playback-state"

# sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,redirect_uri=REDIRECT_URI))
sp = spotipy.Spotify(
    client_credentials_manager=SpotifyOAuth(
        scope=scope,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
    )
)
username = 1214410063

sp_oauth = SpotifyOAuth(
    username=username,
    scope=scope,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
)
token_info = sp_oauth.get_cached_token()


class ThreadRefresh:
    def __init__(self, token_info: dict, sp_oauth: SpotifyOAuth) -> None:
        self.interval = 0
        self.token_info = token_info
        self.sp_oauth = sp_oauth
        self._continue_refresh = True
        self._lock = threading.Lock()

        thread = threading.Thread(target=self.refresh_fn)
        thread.daemon = True
        thread.start()

    def refresh_fn(self):
        while self._continue_refresh:
            print("Refreshing token ", datetime.datetime.now().__str__())
            with self._lock:
                self.token_info = self.sp_oauth.refresh_access_token(
                    self.token_info["refresh_token"]
                )
                token = self.token_info["access_token"]
                sp = spotipy.Spotify(auth=token)
                pprint(self.token_info["expires_at"])
            time.sleep(3)

    def stop(self):
        self._continue_refresh = False


tr = ThreadRefresh(token_info=token_info, sp_oauth=sp_oauth)
try:
    time.sleep(15)
except KeyboardInterrupt:
    print("Program killed: running cleanup code")
# finally:
#     tr.stop()
