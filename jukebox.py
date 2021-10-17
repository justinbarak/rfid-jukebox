"""
jukebox.py

"""

import logging
import os
import threading
import time
from pprint import pprint
from typing import Tuple, List, Union, Optional, Generator, Dict

import spotipy
import spotipy.util as util
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import os
import json

# Initialize
load_dotenv()
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
SPOTIFY_USERNAME = int(os.environ.get("SPOTIFY_USERNAME"))  # type: ignore
REDIRECT_URI = "http://127.0.0.1:7070"


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(process)d-%(levelname)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)


def spotipy_instance(
    username: int,
) -> List[Union[spotipy.client.Spotify, SpotifyOAuth, Dict]]:
    """Returns a 'spotipy.Spotify' instance. Will request authenication at Redirect URL if not logged in before.
    Parameter username: integer found in Spotify profile
    Note, token expires after 60 minutes. Recommend refreshing more often than hourly.
    """
    scope = (
        "user-read-playback-state,user-modify-playback-state,playlist-read-private,"
        + "playlist-read-collaborative,user-read-currently-playing,user-read-private,"
        + "user-library-read,user-read-playback-position"
    )
    try:
        token = util.prompt_for_user_token(
            username=username,
            scope=scope,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
        )
        sp_auth = SpotifyOAuth(
            scope=scope,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
        )
        sp = spotipy.Spotify(
            auth=token,
            client_credentials_manager=sp_auth,
        )
        cached_token = spotipy.oauth2.SpotifyOAuth(
            username=username,
            scope=scope,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
        ).get_cached_token()
        logging.debug(f"Token successfully created/refreshed for {username}.")
        logging.debug(f"full auth token: {cached_token}")
    except Exception as e:
        logging.exception(msg=f"Can't get token for {username}.\n{e}")
    return [sp, sp_auth, cached_token]


def refresh_token(
    sp_auth: SpotifyOAuth, sp: spotipy.client.Spotify, whole_token: Dict
) -> Dict:
    """Refreshes the spotify OAuth token.
    Parameter sp_auth: SpotifyOAuth object with username and all details included (e.g. scope)
    Parameter sp: spotipy.Spotify, state will be modified and returned.
    Parameter whole_token: Doct, token return by spotify api. Updated and saved at end.
    """
    logging.info("Refreshing spotify token...\n")
    logging.debug(f"Cached access token info: {whole_token}")
    token_info = sp_auth.refresh_access_token(whole_token["refresh_token"])
    token = token_info["access_token"]
    sp = spotipy.Spotify(auth=token)
    return token_info


def get_jukebox_id(sp: spotipy.client.Spotify) -> str:
    """Pass a spotify client and return the device number for the jukebox.
    Parameter sp: spotify client
    """
    result = sp.devices()
    rest = result.get("devices")
    box_id = ""
    for device in rest:
        if device["name"] == "Kid_Jukebox":
            box_id = device["id"]
            break
    if box_id == "":
        logging.error(f"Jukebox Id not found. Aborting...")
        os._exit(1)
    logging.debug(f"Jukebox Id={box_id}")
    return box_id


def prime(fn):
    def wrapper(*args, **kwargs):
        v = fn(*args, **kwargs)
        v.send(None)
        return v

    return wrapper


class FSM_jukebox:
    def __init__(self):
        self.stopped = self._create_stopped()
        self.playing = self._create_playing()
        self.paused = self._create_paused()

        self.current_state = self.stopped

        self.username = SPOTIFY_USERNAME
        self.sp, self.sp_auth, self.token = spotipy_instance(username=self.username)
        self.device_id = get_jukebox_id(self.sp)
        self.records = self._load_records()

        self._repeat_status = True
        self.sp.repeat(state="context", device_id=self.device_id)
        self._shuffle_status = True
        self.sp.shuffle(state=True, device_id=self.device_id)

        self._lock = threading.Lock()
        self._refresh_thread = threading.Thread(target=self._refresh)
        self._refresh_thread.daemon = True
        self._refresh_thread.start()

    def _refresh(self) -> None:
        """A function running in a separate daemon thread which will refresh spotify credentials"""
        interval = 55 * 60  # 55 minutes
        while True:
            logging.debug("Locking FSM for refresh")
            with self._lock:
                self.token = refresh_token(self.sp_auth, self.sp, self.token)
                # Make sure jukebox did not change id
                self.device_id = get_jukebox_id(self.sp)
            logging.debug("Refresh completed, unlocking FSM")
            time.sleep(interval)

    def send(self, command: Tuple[str, ...]) -> None:
        assert len(command) == 2
        if command[1] != "":
            fixed_command = (
                command[0],
                self.records["records"].get(command[1]).get("uri"),
            )
            self.current_state.send(fixed_command)
        else:
            self.current_state.send(command)

    def _shuffle(self):
        """Randomize, i.e. shuffle. Update internal shuffle tracking variable."""
        if self._shuffle_status == True:
            self.sp.shuffle(state=False, device_id=self.device_id)
            self._shuffle_status = False
        else:
            self.sp.shuffle(state=True, device_id=self.device_id)
            self._shuffle_status = True
        logging.info(
            f"Shuffle Triggered in {self.current_state}. "
            + f"Now shuffle is set to {self._shuffle_status}."
        )

    def _reverse(self):
        """Skip back a track and start playing if not currently playing."""
        if self._active_device() == True:
            logging.debug(f"Rewinding Track, current state {self.current_state}")
            if self.current_state == self.playing:
                self.sp.previous_track(device_id=self.device_id)
            else:
                self._resume()
                self.sp.previous_track(device_id=self.device_id)
            self.current_state = self.playing
        else:
            pass

    def _forward(self):
        """Skip forward a track and start playing if not currently playing."""
        if self._active_device() == True:
            logging.debug(
                f"Skipping Forward a Track, current state {self.current_state}"
            )
            if self.current_state == self.playing:
                self.sp.next_track(device_id=self.device_id)
            else:
                self._resume()
                self.sp.next_track(device_id=self.device_id)
            self.current_state = self.playing
        else:
            pass

    def _resume(self) -> None:
        """Resumes playing current track."""
        if self._active_device() == True:
            self.sp.start_playback(device_id=self.device_id)
            self.current_state = self.playing

    def _stop(self) -> None:
        """Stops playing current track, moves to stopped state."""
        if self._active_device() == True:
            self.sp.start_playback(device_id=self.device_id)
        self.current_state = self.stopped

    def _play(self, uri: str) -> None:
        """Starts playback of uri on jukebox."""
        self.sp.start_playback(device_id=self.device_id, context_uri=uri)
        self.current_state = self.playing

    def _pause(self) -> None:
        """Pauses playback on jukebox."""
        if self._active_device() == True:
            self.sp.pause_playback(device_id=self.device_id)
        self.current_state = self.paused

    def _active_device(self):
        """Returns True if self.device_id (jukebox) matches the active device_id."""
        devices_dict = self.sp.devices()
        for device in devices_dict.get("devices"):
            if device.get("is_active") == True and device.get("id") == self.device_id:
                return True
        return False

    def _load_records(self) -> dict:
        """Load the records.json into python dict."""
        records_json = open("./records.json", "r")
        logging.info("Loaded records.json")
        return json.load(records_json)

    @staticmethod
    def _mapping_dict() -> Dict[str, str]:
        decode_dict = {
            "_create_stopped": "stopped",
            "_create_playing": "playing",
            "_create_paused": "paused",
        }
        return decode_dict

    @staticmethod
    def _command_options() -> list:
        options = ["stop", "play", "pause", "forward", "reverse", "randomize"]
        return options

    def __repr__(self) -> str:
        decode_dict = self._mapping_dict()
        return str(decode_dict.get(self.current_state.__name__))

    @prime
    def _create_stopped(self) -> Generator:
        while True:
            command: str = yield
            if command[0].lower() == "play":
                if command[1] != "":
                    # actually call the function to play the song
                    self._play(command[1])
                else:
                    # Pressing play while stopped does nothing
                    pass
            elif command[0].lower() == "stop":
                pass
            elif command[0].lower() == "pause":
                pass
            elif command[0].lower() == "forward":
                # Skipping Forward while stopped does nothing
                pass
            elif command[0].lower() == "reverse":
                # Skipping Forward while stopped does nothing
                pass
            elif command[0].lower() == "randomize":
                # toggles shuffling status, stays paused
                self._shuffle()
            else:
                raise IncorrectCommand(command)

    @prime
    def _create_playing(self) -> Generator:
        while True:
            command: str = yield
            if command[0].lower() == "play":
                if command[1] != "":
                    # actually call the function to play the song
                    self._play(command[1])
                else:
                    # Pressing play while playing does nothing
                    pass
            elif command[0].lower() == "stop":
                self._stop()
            elif command[0].lower() == "pause":
                self._pause()
            elif command[0].lower() == "forward":
                # Skipping Forward skips to next track
                self._forward()
            elif command[0].lower() == "reverse":
                # Skipping Reverse skips back to previous track
                self._reverse()
            elif command[0].lower() == "randomize":
                # toggles shuffling status, stays paused
                self._shuffle()
            else:
                raise IncorrectCommand(command)

    @prime
    def _create_paused(self) -> Generator:
        while True:
            command: str = yield
            if command[0].lower() == "play":
                if command[1] != "":
                    # actually call the function to play the song
                    self._play(command[1])
                elif self._active_device() == True:
                    # Pressing play while paused resumes the song if this device is being used
                    self._resume()
            elif command[0].lower() == "stop":
                self._stop()
            elif command[0].lower() == "pause":
                pass
            elif command[0].lower() == "forward":
                # Skipping Forward while paused starts playback and skips to next track
                self._forward()
            elif command[0].lower() == "reverse":
                # Skipping Reverse while paused starts playback and skips back to previous track
                self._reverse()
            elif command[0].lower() == "randomize":
                # toggles shuffling status, stays paused
                self._shuffle()
            else:
                raise IncorrectCommand(command)


class IncorrectCommand(Exception):
    def __init__(self, command):
        self.command = command
        logging.debug(f'"{self.command}" is invalid input')

    def __str__(self):
        return f'"{self.command}" is invalid input'
