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
    while not shutdown_event.is_set():
        # do a thing with rfid
        sleep(10)
        # dummy up a response
        logging.debug("sending dummy RFID code to message queue")
        result = ("play", "RFID_CODE")
        messages.put(result)
        sleep(60)


def buttons(messages: Queue) -> None:
    logging.info("Button manager Launched")
    while not shutdown_event.is_set():
        # get button input
        sleep(20)
        # dummy up a response
        logging.debug("sending dummy pause code")
        result = ("pause", "")
        messages.put(result)
        sleep(60)


def main() -> None:
    messages = Queue()

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

            sleep(0.1)

    except KeyboardInterrupt:
        shutdown_event.set()
        messages.close()
        messages.join_thread()


if __name__ == "__main__":
    main()
