import pytz
import random
import appdaemon.plugins.hass.hassapi as hass
import time
from datetime import datetime

#SPEAKER = 'media_player.arpi'
#SPEAKER = 'media_player.living_room_display'
SPEAKER = 'media_player.mpd'
#TTS_SERVICE = 'tts/google_say'
SOMEONE_AT_HOME = 'input_boolean.someone_at_home'
TTS_SERVICE = 'tts/google_cloud_say'
TTS_LANGUAGE = 'hu-HU'

class tts_announce(hass.Hass):
    def initialize(self):
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

            volume = 0.6
            if str(datetime.now().time()) > "22:00:00" or str(datetime.now().time()) < "05:00:00":
                volume = 0.55
            elif str(datetime.now().time()) > "20:00:00" or str(datetime.now().time()) < "06:00:00":
                volume = 0.55
            elif str(datetime.now().time()) < "07:30:00":
                volume = 0.55

            self.handle = None
            if self.get_state(SOMEONE_AT_HOME)=="on":
                self.call_service("media_player/volume_set", entity_id=speaker, volume_level=volume)
                if filename is not None:
                    self.call_service("media_player/play_media", entity_id=speaker, media_content_id=filename, media_content_type="music")

                if delay is not None:
                    self.handle = self.run_in(self.run_in_say_it, delay, message=text, speaker=speaker, options=options)   
                else:                    
                    if self.get_state(speaker)=="playing":
                        self.handle = self.listen_state(self.listen_say_it, speaker, old = "playing", message=text, speaker=speaker, options=options)   # vagy new = "stopped" ?
                    else:
                        self.say_it(speaker, None, None, None, message=text, speaker=speaker, options=options)

        else:
            self.log("No message parameter in data")

    def run_in_say_it(self, kwargs):
        if kwargs is not None and 'message' in kwargs and 'speaker' in kwargs and 'options' in kwargs:
            self.say_it(kwargs.get("speaker"), None, None, None, message=kwargs.get("message"), speaker=kwargs.get("speaker"), options=kwargs.get("options"))

    def listen_say_it(self, entity, attribute, old, new, kwargs):
        if kwargs is not None and 'message' in kwargs and 'speaker' in kwargs and 'options' in kwargs:
            self.say_it(kwargs.get("speaker"), None, None, None, message=kwargs.get("message"), speaker=kwargs.get("speaker"), options=kwargs.get("options"))

    def say_it(self, entity, attribute, old, new, **kwargs):
        if kwargs is not None and 'message' in kwargs and 'speaker' in kwargs and 'options' in kwargs:
            text = kwargs.get("message")
            self.call_service(TTS_SERVICE, entity_id=kwargs.get("speaker"), language=TTS_LANGUAGE, message=text, options=kwargs.get("options"))
            self.log(("Saying '" + text + "'").encode('utf-8'))
            if self.handle is not None:
                self.cancel_listen_state(self.handle)
