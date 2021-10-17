import json
import os
import shutil

import requests
from dotenv import load_dotenv
import spotipy

from jukebox import spotipy_instance


def main() -> None:
    IMAGE_LOCATION = "./album_art/"
    records_json = open("./records.json", "r")

    records_dict = json.load(records_json)

    # Initialize
    load_dotenv()
    SPOTIFY_USERNAME: int = int(os.environ.get("SPOTIFY_USERNAME"))  # type: ignore
    sp, sp_auth = spotipy_instance(username=SPOTIFY_USERNAME)

    for key in records_dict["records"].keys():
        item = records_dict["records"][key]

        if "album" in item.get("url"):
            details = sp.album(item.get("url"))
            item["name"] = details["name"]
            item["image_url"] = details["images"][0]["url"]
            item["uri"] = details["uri"]
        elif "playlist" in item.get("url"):
            details = sp.playlist(item.get("url"))
            item["name"] = details["name"]
            item["image_url"] = details["images"][0]["url"]
            item["uri"] = details["uri"]
        else:
            details = sp.track(item.get("url"))
            item["name"] = details["name"]
            item["image_url"] = details["album"]["images"][0]["url"]
            item["uri"] = details["uri"]

        # save images from url
        filename = IMAGE_LOCATION + item["name"] + ".png"
        r = requests.get(item["image_url"], stream=True)

        if r.status_code == 200:
            r.raw.decode_content = True
            with open(filename, "wb") as f:
                shutil.copyfileobj(r.raw, f)
        else:
            print("There was a problem.")

    # Now save updated record
    with open("./records.json", "w") as outfile:
        json.dump(records_dict, outfile)


if __name__ == "__main__":
    main()
