import logging
import subprocess
from signal import pause

import RPi.GPIO as GPIO

rotary_logger = logging.getLogger("rotary_encoder")
rotary_logger.setLevel(logging.WARNING)
from rotary_encoder import RotaryEncoder


class VolumeControl:
    def __init__(self, MAX_VOLUME=65, MIN_VOLUME=15):
        GPIO.setmode(GPIO.BOARD)
        self.MAX_VOLUME = MAX_VOLUME
        self.MIN_VOLUME = MIN_VOLUME
        self.encoder = RotaryEncoder(
            pinA=37,
            pinB=11,
            functionCallDecr=self.decr_volume,
            functionCallIncr=self.incr_volume,
            timeBase=0.03,
        )
        self.volume = 25
        self.set_volume(self.volume)

    def incr_volume(self, vol_adjust: int) -> None:
        if (self.volume + vol_adjust) >= self.MAX_VOLUME:
            self.volume = self.MAX_VOLUME
        else:
            self.volume += vol_adjust
        self.set_volume(self.volume)

    def decr_volume(self, vol_adjust: int) -> None:
        if (self.volume - vol_adjust) <= self.MIN_VOLUME:
            self.volume = self.MIN_VOLUME
        else:
            self.volume -= vol_adjust
        self.set_volume(self.volume)

    def set_volume(self, vol):
        command = lambda vol: f"amixer -c IQaudIODAC sset 'Digital',0 {vol}%,{vol}% -M"
        subprocess.run(
            args=command(vol),
            shell=True,
            check=True,
            capture_output=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


if __name__ == "__main__":
    volume_control = VolumeControl()
    pause()
