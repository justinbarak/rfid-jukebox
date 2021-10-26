#!/usr/bin/python
"""This is the master file which controls the spotipy jukebox.
It imports the various components and ties them together.
"""

from jukebox import FSM_jukebox
from multiprocessing import Event, Queue
from multiprocessing import Process
from time import sleep
from datetime import datetime
from datetime import timedelta
from subprocess import call
import logging
from simple_button import SimpleButton
import signal
from read_rfid import get_reading

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(process)d-%(levelname)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

shutdown_event = Event()


def process_queue(messages: Queue) -> None:
    logging.info("Queue Processor Launched")
    jukebox = FSM_jukebox()
    try:
        while not shutdown_event.is_set():
            # wait until there is a message in the queue
            # logging.debug(messages.get())
            command = messages.get()
            logging.debug(command)
            jukebox.send(command=command)
            sleep(0.05)
    except KeyboardInterrupt:
        pass


def rfid_reader(messages: Queue) -> None:
    logging.info("RFID Reader Launched")
    try:
        while not shutdown_event.is_set():
            rfid_response = get_reading()
            if rfid_response != None:
                logging.debug(f"RFID Response - {rfid_response}")
                result = ("play/pause", rfid_response)
                messages.put(result)
                sleep(4)
            else:
                sleep(0.05)
    except KeyboardInterrupt:
        pass


def buttons(messages: Queue) -> None:
    logging.info("Button manager Launched")
    # ["play/pause", "stop", "forward", "reverse", "randomize"]
    # create functions for each button
    play_result = lambda *args: messages.put(("play/pause", ""))
    stop_result = lambda *args: messages.put(("stop", ""))
    forward_result = lambda *args: messages.put(("forward", ""))
    reverse_result = lambda *args: messages.put(("reverse", ""))
    randomize_result = lambda *args: messages.put(("randomize", ""))
    # create buttons
    play_button = SimpleButton(pin=int(36), action=play_result)
    stop_button = SimpleButton(pin=int(37), action=stop_result)
    forward_button = SimpleButton(pin=int(29), action=forward_result)
    reverse_button = SimpleButton(pin=int(31), action=reverse_result)
    randomize_button = SimpleButton(pin=int(16), action=randomize_result)
    # while not shutdown_event.is_set():
    logging.debug("Buttons created")
    try:
        signal.pause()
    except KeyboardInterrupt:
        pass


def main() -> None:
    messages = Queue(maxsize=6)

    logging.info("Launching Queue process")
    Process(target=process_queue, args=(messages,)).start()
    logging.debug("Back from launch")

    logging.info("Launching rfid reader process")
    Process(target=rfid_reader, args=(messages,)).start()
    logging.debug("Back from launch")

    logging.info("Launching button manager process")
    Process(target=buttons, args=(messages,)).start()
    logging.debug("Back from launch")

    try:
        while not shutdown_event.is_set():

            sleep(0.01)

    except KeyboardInterrupt:
        shutdown_event.set()
        messages.close()
        messages.join_thread()


if __name__ == "__main__":
    main()
