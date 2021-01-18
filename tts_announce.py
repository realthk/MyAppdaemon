import pytz
import random
import appdaemon.plugins.hass.hassapi as hass
import time
import queue
import requests 
import math
import mutagen
from io import BytesIO
from datetime import datetime

# Have this in appdeamon config, as mutagen is not part of it:
# python_packages:
#  - mutagen

#SPEAKER = 'media_player.living_room_display'
SPEAKER = 'media_player.mpd'
#TTS_SERVICE = 'tts/google_say'
EXTRA_DELAY_IF_SLEEPS = False       # Set this to True for Google Home speaker
SOMEONE_AT_HOME = 'input_boolean.someone_at_home'
TTS_SERVICE = 'tts/google_cloud_say'
TTS_LANGUAGE = 'hu-HU'
FILE_URL = 'https://realthk.duckdns.org:8123/local/media/'

class tts_announce(hass.Hass):

    def initialize(self):
        self.q_listen = queue.Queue()
        self.q_run = queue.Queue()
        self.listen_event(self.tts_announce,  "tts_announce")

    def tts_announce(self, event, data, args):
        if data is not None and 'message' in data:
            text = data.get("message")
            options = {}
            language = TTS_LANGUAGE
            gender =  "female"
            if "language" in data:
                language = data.get("language")
                voice = f"{language}-Wavenet-A"
                speed = 1
                if language == "en-GB":
                    speed = 0.9
                options = {
                    "voice" : voice,
                    "gender" : gender,
                    "speed" : speed
                }

            speaker = SPEAKER
            if "speaker" in data:
                speaker = data.get("speaker")

            filename = None
            if "filename" in data:
                filename = data.get("filename")

            delay = None
            if "delay" in data:
                delay = data.get("delay")

            volume = 0.8
            if str(datetime.now().time()) > "22:00:00" or str(datetime.now().time()) < "05:00:00":
                volume = 0.60
            elif str(datetime.now().time()) > "20:00:00" or str(datetime.now().time()) < "06:00:00":
                volume = 0.7
            elif str(datetime.now().time()) < "07:30:00":
                volume = 0.75

            self.handle = None
            if self.get_state(SOMEONE_AT_HOME)=="on":
                self.call_service("media_player/volume_set", entity_id=speaker, volume_level=volume)
                if text>'':
                    if delay is None and filename is not None and filename>'':
                        r = requests.get(FILE_URL + filename)
                        ext = filename[-3:].upper()
                        if ext=="MP3":
                            audio = mutagen.mp3.MP3(BytesIO(r.content))    
                        elif ext=="OGG":
                            audio = mutagen.oggvorbis.OggVorbis(BytesIO(r.content))
                        else:
                            audio = mutagen.File(BytesIO(r.content))
                        delay = math.ceil(audio.info.length)
                    elif delay is None:
                        delay = 0    
                    # Google cast speakers might need extra 1-2 secs to wake up
                    if EXTRA_DELAY_IF_SLEEPS and self.get_state(speaker)=="off": 
                        delay += 3

                if self.get_state(speaker)=="playing":
                    handle = self.listen_state(self.listen_say_it, speaker, old = "playing", message=text, speaker=speaker, options=options, filename=filename, delay=delay)   # vagy new = "stopped" ?
                    self.q_listen.put(handle)
                else:
                    if filename is not None:
                        self.call_service("media_player/play_media", entity_id=speaker, media_content_id=FILE_URL + filename, media_content_type="music")
                        if text>'':
                            timer = self.run_in(self.run_in_say_it, delay, message=text, speaker=speaker, options=options)
                            self.q_run.put(timer)   # handle must be put in a queue, as this app might be called again while a timer already runs
                    else:
                        self.say_it(speaker, None, None, None, message=text, speaker=speaker, options=options)

        else:
            self.log("No message parameter in data")

    def listen_say_it(self, entity, attribute, old, new, kwargs):
        if not self.q_listen.empty():
            self.cancel_listen_state(self.q_listen.get())

        if kwargs is not None and 'message' in kwargs and 'speaker' in kwargs and 'options' in kwargs:
            if 'filename' in kwargs and kwargs.get("filename") is not None:
                self.call_service("media_player/play_media", entity_id=kwargs.get("speaker"), media_content_id=kwargs.get("filename"), media_content_type="music")
                self.run_in(self.run_in_say_it, delay=kwargs.get("delay"), message=kwargs.get("message"), speaker=kwargs.get("speaker"), options=kwargs.get("options"))
            else:
                self.say_it(kwargs.get("speaker"), None, None, None, message=kwargs.get("message"), speaker=kwargs.get("speaker"), options=kwargs.get("options"))

    def run_in_say_it(self, kwargs):
        if not self.q_run.empty():
            self.cancel_timer(self.q_run.get())

        if kwargs is not None and 'message' in kwargs and 'speaker' in kwargs and 'options' in kwargs:
            self.say_it(kwargs.get("speaker"), None, None, None, message=kwargs.get("message"), speaker=kwargs.get("speaker"), options=kwargs.get("options"))

    def say_it(self, entity, attribute, old, new, **kwargs):
        if kwargs is not None and 'message' in kwargs and 'speaker' in kwargs and 'options' in kwargs:
            text = kwargs.get("message")
            self.call_service(TTS_SERVICE, entity_id=kwargs.get("speaker"), language=TTS_LANGUAGE, message=text, options=kwargs.get("options"))
            self.log(("Saying '" + text + "'").encode('utf-8'))
#            self.log("Saying '" + text + "'", level="INFO", log="diag_log")
            self.call_service("logbook/log", name="Bejelentés", message=text, entity_id=kwargs.get("speaker"), domain="media_player" )