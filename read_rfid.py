#!/usr/bin/env python
"""
RC522 Wiring Configuration for RaspPi:
SDA connects to Pin 24.
SCK connects to Pin 23.
MOSI connects to Pin 19.
MISO connects to Pin 21.
GND connects to Pin 6.
RST connects to Pin 22.
3.3v connects to Pin 1.
"""

import RPi.GPIO as GPIO
from time import sleep
from mfrc522 import SimpleMFRC522
import logging


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(process)d-%(levelname)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)
reader = SimpleMFRC522()


def get_reading() -> str:
    try:
        id = None
        reader = SimpleMFRC522()
        while id == None:
            id, text = reader.read()
            sleep(0.1)
            logging.info(f"id is -> {id}")
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    return id


def repeated_reading() -> str:
    try:

        while True:
            id = get_reading()
            logging.info(f"id is -> {id}")
            sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    repeated_reading()()
    GPIO.cleanup()
