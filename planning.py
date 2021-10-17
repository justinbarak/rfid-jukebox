"""
Executing it:
    RFID badge is scanned
        RFID Code is looked up in database
    Database lookup returns the spotify album, playlist, or song link on spotify
    Spotify API is activated, song is streamed
        Spotify token is created and saved at beginning (init?)


Preparing it:
    Ability to scan cards, log RFID data or modify
    Pick up album art from Spotify link and save for purposes of printing



Additional Functionality:
    Buttons to Pause, Play, Skip song
    Log plays through app
    60 min timeout?



Bonus Notes:
    https://nfcpy.readthedocs.io/en/latest/overview.html
    --> The ACR122U is not supported as P2P Target because the listen time can not be set to less than 5 seconds.
    It can not be overstated that the ACR122U is not a good choice for nfcpy.



"""


from jukebox import FSM_jukebox
import time
import os

jukebox = FSM_jukebox()

command_options = jukebox._command_options()
# testing record
uri = jukebox.records["records"]["RFID_CODE"]["uri"]

# for option in command_options:
#     print(f"Starting State: {jukebox}")
#     if option == "play":
#         command = (option, uri)
#     else:
#         command = (option, "")
#     print(f"Command: {command}")
#     jukebox.send(command=command)
#     print(f"Ending State: {jukebox}")
#     time.sleep(2)

# command = ("reverse", "")
# jukebox.send(command=command)
# time.sleep(1)
# jukebox.send(command=command)

jukebox.send(command=(""))
